# spark-strict

## 1. Install Spark in Strict Mode

- Setup service account and secret

```bash
dcos security org service-accounts keypair spark-private.pem spark-public.pem
dcos security org service-accounts create -p spark-public.pem -d "Spark service account" spark-principal
dcos security secrets create-sa-secret --strict spark-private.pem spark-principal spark/secret
```

- Create permissions for the Spark Service Account¬ (Note: Some of them already exist.)

```bash
curl -X PUT -k \
-H "Authorization: token=$(dcos config show core.dcos_acs_token)" $(dcos config show core.dcos_url)/acs/api/v1/acls/dcos:mesos:agent:task:user:root \
-d '{"description":"Allows Linux user root to execute tasks"}' \
-H 'Content-Type: application/json'
curl -X PUT -k \
-H "Authorization: token=$(dcos config show core.dcos_acs_token)" "$(dcos config show core.dcos_url)/acs/api/v1/acls/dcos:mesos:master:framework:role:*" \
-d '{"description":"Allows a framework to register with the Mesos master using the Mesos default role"}' \
-H 'Content-Type: application/json'
curl -X PUT -k \
-H "Authorization: token=$(dcos config show core.dcos_acs_token)" "$(dcos config show core.dcos_url)/acs/api/v1/acls/dcos:mesos:master:task:app_id:%252Fspark" \
-d '{"description":"Allow to read the task state"}' \
-H 'Content-Type: application/json'
curl -X PUT -k \
-H "Authorization: token=$(dcos config show core.dcos_acs_token)" $(dcos config show core.dcos_url)/acs/api/v1/acls/dcos:mesos:master:task:user:nobody \
-d '{"description":"Allows Linux user nobody to execute tasks"}' \
-H 'Content-Type: application/json'
curl -X PUT -k \
-H "Authorization: token=$(dcos config show core.dcos_acs_token)" $(dcos config show core.dcos_url)/acs/api/v1/acls/dcos:mesos:master:task:user:root \
-d '{"description":"Allows Linux user root to execute tasks"}' \
-H 'Content-Type: application/json'
```

- Grant permissions to the Spark Service Account

```bash
curl -X PUT -k \
-H "Authorization: token=$(dcos config show core.dcos_acs_token)" $(dcos config show core.dcos_url)/acs/api/v1/acls/dcos:mesos:agent:task:user:root/users/spark-principal/create
curl -X PUT -k \
-H "Authorization: token=$(dcos config show core.dcos_acs_token)" "$(dcos config show core.dcos_url)/acs/api/v1/acls/dcos:mesos:master:framework:role:*/users/spark-principal/create"
curl -X PUT -k \
-H "Authorization: token=$(dcos config show core.dcos_acs_token)" "$(dcos config show core.dcos_url)/acs/api/v1/acls/dcos:mesos:master:task:app_id:%252Fspark/users/spark-principal/create"
curl -X PUT -k \
-H "Authorization: token=$(dcos config show core.dcos_acs_token)" $(dcos config show core.dcos_url)/acs/api/v1/acls/dcos:mesos:master:task:user:nobody/users/spark-principal/create
curl -X PUT -k \
-H "Authorization: token=$(dcos config show core.dcos_acs_token)" $(dcos config show core.dcos_url)/acs/api/v1/acls/dcos:mesos:master:task:user:root/users/spark-principal/create
```

- Grant  permissions to Marathon in order to the Spark the dispatcher in root

```bash
# Grant permissions to Marathon
curl -X PUT -k \
-H "Authorization: token=$(dcos config show core.dcos_acs_token)" $(dcos config show core.dcos_url)/acs/api/v1/acls/dcos:mesos:master:task:user:root/users/dcos_marathon/create
```

- Create a file **config.json** and set the Spark principal and secret

```json
{
   "security": {
       "mesos": {
           "authentication": {
               "secret_name": "spark/secret"
           }
       }
   },
   "service": {
       "principal": "spark-principal",
       "secret": "spark/secret",
       "user": "root"
   }
}
```

- Install Spark using the config.json file

```
dcos package install --options=config.json spark
```

- As a workaround add additional flags to the Spark run command

```bash
dcos spark run --verbose --submit-args="--conf spark.mesos.executor.docker.image=mesosphere/spark:1.1.1-2.2.0-hadoop-2.6 --conf spark.mesos.executor.docker.forcePullImage=true --conf spark.mesos.principal=spark-principal --conf spark.mesos.driverEnv.LIBPROCESS_SSL_CA_DIR=.ssl/ --conf spark.mesos.driverEnv.LIBPROCESS_SSL_CA_FILE=.ssl/ca.crt --conf spark.mesos.driverEnv.LIBPROCESS_SSL_CERT_FILE=.ssl/scheduler.crt --conf spark.mesos.driverEnv.LIBPROCESS_SSL_KEY_FILE=.ssl/scheduler.key --conf spark.mesos.driverEnv.MESOS_MODULES=file:///opt/mesosphere/etc/mesos-scheduler-modules/dcos_authenticatee_module.json --conf spark.mesos.driverEnv.MESOS_AUTHENTICATEE=com_mesosphere_dcos_ClassicRPCAuthenticatee --conf spark.mesos.containerizer=mesos --class org.apache.spark.examples.SparkPi https://downloads.mesosphere.com/spark/assets/spark-examples_2.11-2.0.1.jar 30"
```

## 2. Create Service Account to start Spark without root permissions

- Create a service account called `stream-principal`

```
dcos security org service-accounts keypair stream-private.pem stream-public.pem
dcos security org service-accounts create -p stream-public.pem -d "Spark Streaming Job service account" stream-principal
dcos security secrets create-sa-secret --strict stream-private.pem stream-principal stream/secret
```

- Set the following permissions for the service account

```
dcos:adminrouter:ops:mesos full
dcos:adminrouter:ops:mesos-dns full
dcos:adminrouter:ops:slave full
dcos:adminrouter:service:marathon full
dcos:adminrouter:service:spark full
dcos:mesos:agent:framework:role full
dcos:mesos:master:framework:role full
dcos:service:marathon:marathon:services:/spark read
```

- Login as user `test`

```
dcos auth login
```

- Submit a Spark Job

```
dcos spark run --verbose --submit-args="--conf spark.mesos.executor.docker.image=mesosphere/spark:1.1.1-2.2.0-hadoop-2.6 --conf spark.mesos.executor.docker.forcePullImage=true --conf spark.mesos.principal=spark-principal --conf spark.mesos.driverEnv.LIBPROCESS_SSL_CA_DIR=.ssl/ --conf spark.mesos.driverEnv.LIBPROCESS_SSL_CA_FILE=.ssl/ca.crt --conf spark.mesos.driverEnv.LIBPROCESS_SSL_CERT_FILE=.ssl/scheduler.crt --conf spark.mesos.driverEnv.LIBPROCESS_SSL_KEY_FILE=.ssl/scheduler.key --conf spark.mesos.driverEnv.MESOS_MODULES=file:///opt/mesosphere/etc/mesos-scheduler-modules/dcos_authenticatee_module.json --conf spark.mesos.driverEnv.MESOS_AUTHENTICATEE=com_mesosphere_dcos_ClassicRPCAuthenticatee --conf spark.mesos.containerizer=mesos --class org.apache.spark.examples.SparkPi https://downloads.mesosphere.com/spark/assets/spark-examples_2.11-2.0.1.jar 30"
```

- Find driver ip address using dcos spark status

```
dcos spark status driver-20170817131417-0006
```

- Find driver ip address using Mesos DNS

```
https://leader.mesos/mesos_dns/v1/enumerate
```

## 3. Restart Spark Streaming Jobs if they are failing

- For this demo install Kafka in Strict Mode

```
dcos security org service-accounts keypair kafka-private-key.pem kafka-public-key.pem
dcos security org service-accounts create -p kafka-public-key.pem -d "Kafka service account" kafka-principal
dcos security secrets create-sa-secret --strict kafka-private-key.pem kafka-principal kafka/secret
```

- Create permissions for Kafka

```
curl -X PUT -k \
-H "Authorization: token=$(dcos config show core.dcos_acs_token)" $(dcos config show core.dcos_url)/acs/api/v1/acls/dcos:mesos:master:framework:role:kafka-role \
-d '{"description":"Controls the ability of kafka-role to register as a framework with the Mesos master"}' \
-H 'Content-Type: application/json'
curl -X PUT -k \
-H "Authorization: token=$(dcos config show core.dcos_acs_token)" $(dcos config show core.dcos_url)/acs/api/v1/acls/dcos:mesos:master:reservation:role:kafka-role \
-d '{"description":"Controls the ability of kafka-role to reserve resources"}' \
-H 'Content-Type: application/json'
curl -X PUT -k \
-H "Authorization: token=$(dcos config show core.dcos_acs_token)" $(dcos config show core.dcos_url)/acs/api/v1/acls/dcos:mesos:master:volume:role:kafka-role \
-d '{"description":"Controls the ability of kafka-role to access volumes"}' \
-H 'Content-Type: application/json'
curl -X PUT -k \
-H "Authorization: token=$(dcos config show core.dcos_acs_token)" $(dcos config show core.dcos_url)/acs/api/v1/acls/dcos:mesos:master:reservation:principal:kafka-principal \
-d '{"description":"Controls the ability of kafka-principal to reserve resources"}' \
-H 'Content-Type: application/json'
curl -X PUT -k \
-H "Authorization: token=$(dcos config show core.dcos_acs_token)" $(dcos config show core.dcos_url)/acs/api/v1/acls/dcos:mesos:master:volume:principal:kafka-principal \
-d '{"description":"Controls the ability of kafka-principal to access volumes"}' \
-H 'Content-Type: application/json'  
```

- Grant Permissions to Kafka

```
curl -X PUT -k \
-H "Authorization: token=$(dcos config show core.dcos_acs_token)" $(dcos config show core.dcos_url)/acs/api/v1/acls/dcos:mesos:master:framework:role:kafka-role/users/kafka-principal/create
curl -X PUT -k \
-H "Authorization: token=$(dcos config show core.dcos_acs_token)" $(dcos config show core.dcos_url)/acs/api/v1/acls/dcos:mesos:master:reservation:role:kafka-role/users/kafka-principal/create
curl -X PUT -k \
-H "Authorization: token=$(dcos config show core.dcos_acs_token)" $(dcos config show core.dcos_url)/acs/api/v1/acls/dcos:mesos:master:volume:role:kafka-role/users/kafka-principal/create
curl -X PUT -k \
-H "Authorization: token=$(dcos config show core.dcos_acs_token)" $(dcos config show core.dcos_url)/acs/api/v1/acls/dcos:mesos:master:task:user:nobody/users/kafka-principal/create
curl -X PUT -k \
-H "Authorization: token=$(dcos config show core.dcos_acs_token)" $(dcos config show core.dcos_url)/acs/api/v1/acls/dcos:mesos:master:reservation:principal:kafka-principal/users/kafka-principal/delete
curl -X PUT -k \
-H "Authorization: token=$(dcos config show core.dcos_acs_token)" $(dcos config show core.dcos_url)/acs/api/v1/acls/dcos:mesos:master:volume:principal:kafka-principal/users/kafka-principal/delete
```

- Install Kafka

**config.json**

```
{
  "service": {
    "principal": "kafka-principal",
    "secret_name": "kafka/secret",
    "user": "nobody"
  }
}
```

```
dcos package install --options=config.json kafka
```

- Setup a topic

```
dcos kafka topic create mytopic --replication=2 --partitions=4
```

### 3.1 Use --supervise flag

- Submit a long running Job and set the flag --supervise to keep restart the driver, if it's failing

```
dcos spark run --verbose --submit-args="--supervise --conf spark.cores.max=6 --conf spark.mesos.executor.docker.image=janr/spark-streaming-kafka:v2 --conf spark.mesos.executor.docker.forcePullImage=true --conf spark.mesos.principal=spark-principal --conf spark.mesos.driverEnv.LIBPROCESS_SSL_CA_DIR=.ssl/ --conf spark.mesos.driverEnv.LIBPROCESS_SSL_CA_FILE=.ssl/ca.crt --conf spark.mesos.driverEnv.LIBPROCESS_SSL_CERT_FILE=.ssl/scheduler.crt --conf spark.mesos.driverEnv.LIBPROCESS_SSL_KEY_FILE=.ssl/scheduler.key --conf spark.mesos.driverEnv.MESOS_MODULES=file:///opt/mesosphere/etc/mesos-scheduler-modules/dcos_authenticatee_module.json --conf spark.mesos.driverEnv.MESOS_AUTHENTICATEE=com_mesosphere_dcos_ClassicRPCAuthenticatee https://gist.githubusercontent.com/jrx/436a3779403158753cefaeae747de40b/raw/3e4725e7f28fca30baeb8aaaebc6189510799719/streamingWordCount.py"
```

- Find the node the driver is running on

```
dcos spark status <driver-id>
```

- Connect to the node and kill the task

```
docker ps
docker kill <container-id>
```

The driver should be restarted.

### 3.2 Use Marathon for submitting the Spark Job

- Create a `health_check.py` file

```python
#!/usr/bin/env python3
'''
check health of the spark driver
'''

import re
import subprocess
import requests
import json
import os

def url_ok(url):
    r = requests.head(url)
    return r.status_code == 200

# read filename from env
file_name = str(os.environ['SPARK_SUBMIT_STDOUT'])
f = open(file_name, "r+")
spark_output = f.read()
f.close()

# parse driver id
result = {}
for row in spark_output.split('\n'):
    if 'Submission id: ' in row:
        result = row

match = re.search(r'driver-(\d+)-(\d+)',result)
if match:
    driver_id = match.group(0)
    print('Found Driver ID: ' + driver_id)

# retrieve task list
cmd_read = subprocess.getoutput("dcos task --json " + driver_id)
data = json.loads(cmd_read)

# parse ip address
for task in data:
    if task["id"] == driver_id:
        ip_address = task["statuses"][0]["container_status"]["network_infos"][0]["ip_addresses"][0]["ip_address"]
        print('Found IP address: ' + ip_address)

# check if spark driver is reachable
print(url_ok("http://" + ip_address + ":4040"))
```

- Create a `clean_up.py` file

```python
#!/usr/bin/env python3
'''
kill all running drivers for a specific job name
'''

import subprocess
import json
import os

# read spark name from env
spark_name = 'Driver for ' + str(os.environ['SPARK_NAME'])

# parse drivers from task list
cmd_read = subprocess.getoutput("dcos task --json")
data = json.loads(cmd_read)

# parse drivers from task list
for task in data:
    if task["name"] == spark_name:
        print('Found ' + task["id"])

        # kill spark driver
        cmd_kill = subprocess.getoutput('dcos spark kill ' + task["id"])
        print(cmd_kill)
```

- Create a `Dockerfile` to install the Spark CLI

```
FROM openjdk:8-jre-slim
MAINTAINER Jan Repnak <jan.repnak@mesosphere.io>
RUN apt-get update && apt-get install -y curl python3 python3-pip jq
RUN pip3 install virtualenv requests
ADD https://downloads.dcos.io/binaries/cli/linux/x86-64/dcos-1.9/dcos /usr/local/bin/dcos
RUN chmod +x /usr/local/bin/dcos && dcos config set core.dcos_url https://leader.mesos && dcos config set core.ssl_verify false && dcos config set core.ssl_verify false && dcos auth login --username=admin --password=admin
RUN dcos package install spark --cli
RUN dcos spark run --help
COPY health_check.py /
RUN chmod +x /health_check.py
COPY clean_up.py /
RUN chmod +x /clean_up.py
```

```
$ docker build -t janr/dcos-spark-cli:v6 .
```

- Place Jar or Python Script on the local filesystem of each DC/OS Agent

```
mdir /tmp/spark
curl https://gist.githubusercontent.com/jrx/436a3779403158753cefaeae747de40b/raw/3e4725e7f28fca30baeb8aaaebc6189510799719/streamingWordCount.py -o /tmp/spark/streamingWordCount.py
```

- Create a Marathon service definition to submit the Spark Job

```json
{
  "id": "/stream",
  "cmd": "sleep 10 && dcos config set core.dcos_acs_token $LOGIN_TOKEN && /clean_up.py || true && dcos spark run --submit-args=\"--name ${SPARK_NAME} --conf spark.cores.max=6 --conf spark.mesos.executor.docker.image=janr/spark-streaming-kafka:v2 --conf spark.mesos.executor.docker.forcePullImage=true --conf spark.mesos.principal=spark-principal --conf spark.mesos.driverEnv.LIBPROCESS_SSL_CA_DIR=.ssl/ --conf spark.mesos.driverEnv.LIBPROCESS_SSL_CA_FILE=.ssl/ca.crt --conf spark.mesos.driverEnv.LIBPROCESS_SSL_CERT_FILE=.ssl/scheduler.crt --conf spark.mesos.driverEnv.LIBPROCESS_SSL_KEY_FILE=.ssl/scheduler.key --conf spark.mesos.driverEnv.MESOS_MODULES=file:///opt/mesosphere/etc/mesos-scheduler-modules/dcos_authenticatee_module.json --conf spark.mesos.driverEnv.MESOS_AUTHENTICATEE=com_mesosphere_dcos_ClassicRPCAuthenticatee --conf spark.mesos.executor.docker.volumes=/tmp/spark:/tmp/spark:ro /tmp/spark/streamingWordCount.py\" > ${SPARK_SUBMIT_STDOUT} && while true; do echo 'idle'; sleep 300; done",
  "user": "root",
  "instances": 1,
  "cpus": 0.5,
  "mem": 512,
  "disk": 0,
  "gpus": 0,
  "container": {
    "type": "DOCKER",
    "volumes": [
      {
        "containerPath": "/tmp/spark",
        "hostPath": "/tmp/spark",
        "mode": "RO"
      }
    ],
    "docker": {
      "image": "janr/dcos-spark-cli:v6",
      "portMappings": [],
      "privileged": false,
      "parameters": [],
      "forcePullImage": false
    }
  },
  "healthChecks": [
    {
      "gracePeriodSeconds": 300,
      "intervalSeconds": 60,
      "timeoutSeconds": 20,
      "maxConsecutiveFailures": 5,
      "delaySeconds": 15,
      "command": {
        "value": "/health_check.py"
      },
      "protocol": "COMMAND"
    }
  ],
  "secrets": {
    "secret0": {
      "source": "stream-login"
    }
  },
  "portDefinitions": [
    {
      "port": 0,
      "protocol": "tcp",
      "name": "default"
    }
  ],
  "requirePorts": false,
  "env": {
    "LOGIN_TOKEN": {
      "secret": "secret0"
    },
    "SPARK_SUBMIT_STDOUT": "/mnt/mesos/sandbox/spark-out",
    "SPARK_NAME": "wordcount"
  }
}
```

## 5. Connect to the Driver UI

- Submit a long running Job

- **Example 1:** Do port forwarding using SSH

- Retrieve the IP Address of the Spark driver

```
$ dcos spark status driver-20170817111145-0001 | grep ip_address:
ip_address: "10.0.2.215"
```

- Setup port forwarding using SSH (Note: Default port for Spark UI is 4040)

```
$ ssh -A -p22 core@34.209.32.162 -L 4040:10.0.2.215:4040
open http://localhost:4040/jobs
```

- **Example 2:** Use DC/OS Tunnel
[DC/OS Tunnel Documentation](https://docs.mesosphere.com/1.9/developing-services/tunnel/)

```
# on mac
$ dcos package install tunnel-cli --cli

# Option 1:
$ brew install openvpn
$ sudo dcos tunnel vpn --client=/usr/local/sbin/openvpn

open http://10.0.2.215:4040/jobs

# Option 2: Use Tunnelblick OpenVPN
$ sudo dcos tunnel vpn --client=/Applications/Tunnelblick.app/Contents/Resources/openvpn/openvpn-*/openvpn

open http://10.0.2.215:4040/jobs
```
