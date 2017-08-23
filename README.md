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

## 2. Start and access Spark without root permissions

- Create a user `test` that has the following permissions

```
dcos:adminrouter:service:marathon full
dcos:adminrouter:service:spark full
dcos:service:marathon:marathon:services:/spark read
dcos:adminrouter:ops:mesos full
dcos:adminrouter:ops:slave full
dcos:mesos:agent:executor:app_id:/spark read
dcos:mesos:agent:framework:role:slave_public/ read
dcos:mesos:agent:sandbox:app_id:/spark read
dcos:mesos:agent:task:app_id:/spark read
dcos:mesos:master:executor:app_id:/spark read
dcos:mesos:master:framework:role:slave_public/ read
dcos:mesos:master:task:app_id:/spark/ read
dcos:mesos:master:framework:role:slave/ read
dcos:mesos:agent:framework:role:slave/ read
dcos:adminrouter:ops:mesos-dns full
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
dcos spark run --verbose --submit-args="--supervise --conf spark.mesos.executor.docker.image=janr/spark-streaming-kafka:v2 --conf spark.mesos.executor.docker.forcePullImage=true --conf spark.mesos.principal=spark-principal --conf spark.mesos.driverEnv.LIBPROCESS_SSL_CA_DIR=.ssl/ --conf spark.mesos.driverEnv.LIBPROCESS_SSL_CA_FILE=.ssl/ca.crt --conf spark.mesos.driverEnv.LIBPROCESS_SSL_CERT_FILE=.ssl/scheduler.crt --conf spark.mesos.driverEnv.LIBPROCESS_SSL_KEY_FILE=.ssl/scheduler.key --conf spark.mesos.driverEnv.MESOS_MODULES=file:///opt/mesosphere/etc/mesos-scheduler-modules/dcos_authenticatee_module.json --conf spark.mesos.driverEnv.MESOS_AUTHENTICATEE=com_mesosphere_dcos_ClassicRPCAuthenticatee https://gist.githubusercontent.com/jrx/436a3779403158753cefaeae747de40b/raw/3e4725e7f28fca30baeb8aaaebc6189510799719/streamingWordCount.py"
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

- Create a `health_check.sh` file

```
#!/bin/bash
# Get driver id > Write to file ${MESOS_SANDBOX}/spark-out
driver=`awk '{print $6}' ${MESOS_SANDBOX}/spark-out | tail -1 | cut -d, -f 1`
echo "found: $driver"
# Connect to Mesos DNS > Read HostName
ipaddress=`/usr/local/bin/dcos task --json | jq --raw-output ".[] | select(.id == \"$driver\") | .statuses | .[].container_status | .network_infos | .[].ip_addresses | .[] | .ip_address"`
echo "$driver runs on host: $ipaddress"
# Do Health Check against HostName:4040
curl -sSf http://$ipaddress:4040 > /dev/null
```

- Create a `clean_up.sh` file

```
#!/bin/bash
# Get driver id > Write to file ${MESOS_SANDBOX}/spark-out
driver=`awk '{print $6}' ${MESOS_SANDBOX}/spark-out | tail -1 | cut -d, -f 1`
echo "found: $driver"
# Kill the driver
/usr/local/bin/dcos spark kill $driver
```

- Create a `Dockerfile` to install the Spark CLI

```
FROM openjdk:8-jre-slim
MAINTAINER Jan Repnak <jan.repnak@mesosphere.io>
RUN apt-get update && apt-get install -y curl python3 python3-pip jq
RUN pip3 install virtualenv
ADD https://downloads.dcos.io/binaries/cli/linux/x86-64/dcos-1.9/dcos /usr/local/bin/dcos
RUN chmod +x /usr/local/bin/dcos && dcos config set core.dcos_url https://leader.mesos && dcos config set core.ssl_verify false && dcos config set core.ssl_verify false && dcos auth login --username=admin --password=admin
RUN dcos package install spark --cli
RUN dcos spark run --help
COPY health_check.sh /
RUN chmod +x /health_check.sh
COPY clean_up.sh /
RUN chmod +x /clean_up.sh
```

```
$ docker build -t janr/dcos-spark-cli:v2 .
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
  "cmd": "trap '/clean_up.sh' TERM; dcos config set core.dcos_acs_token $LOGIN_TOKEN && dcos spark run --submit-args=\"--name wordcount --conf spark.mesos.executor.docker.image=janr/spark-streaming-kafka:v2 --conf spark.mesos.executor.docker.forcePullImage=true --conf spark.mesos.principal=spark-principal --conf spark.mesos.driverEnv.LIBPROCESS_SSL_CA_DIR=.ssl/ --conf spark.mesos.driverEnv.LIBPROCESS_SSL_CA_FILE=.ssl/ca.crt --conf spark.mesos.driverEnv.LIBPROCESS_SSL_CERT_FILE=.ssl/scheduler.crt --conf spark.mesos.driverEnv.LIBPROCESS_SSL_KEY_FILE=.ssl/scheduler.key --conf spark.mesos.driverEnv.MESOS_MODULES=file:///opt/mesosphere/etc/mesos-scheduler-modules/dcos_authenticatee_module.json --conf spark.mesos.driverEnv.MESOS_AUTHENTICATEE=com_mesosphere_dcos_ClassicRPCAuthenticatee --conf spark.mesos.executor.docker.volumes=/tmp/spark:/tmp/spark:ro /tmp/spark/streamingWordCount.py\" > ${MESOS_SANDBOX}/spark-out && while true; do echo 'idle'; sleep 300; done",
  "user": "root",
  "instances": 0,
  "cpus": 0.5,
  "mem": 512,
  "disk": 0,
  "gpus": 0,
  "constraints": [],
  "fetch": [],
  "storeUrls": [],
  "backoffSeconds": 1,
  "backoffFactor": 1.15,
  "maxLaunchDelaySeconds": 3600,
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
      "image": "janr/dcos-spark-cli:v3"
    }
  },
  "healthChecks": [
    {
      "gracePeriodSeconds": 300,
      "intervalSeconds": 60,
      "timeoutSeconds": 20,
      "maxConsecutiveFailures": 20,
      "delaySeconds": 15,
      "command": {
        "value": "/health_check.sh"
      },
      "protocol": "COMMAND"
    }
  ],
  "readinessChecks": [],
  "dependencies": [],
  "upgradeStrategy": {
    "minimumHealthCapacity": 1,
    "maximumOverCapacity": 1
  },
  "secrets": {
    "secret0": {
      "source": "stream-login"
    }
  },
  "unreachableStrategy": {
    "inactiveAfterSeconds": 300,
    "expungeAfterSeconds": 600
  },
  "killSelection": "YOUNGEST_FIRST",
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
    }
  }
}
```

## 4. Use Secrets within your Spark Job

## 5. Mount Volumes

## 6. Connect to the Driver UI

 - Submit a long running Job

```bash
$ dcos spark run --docker-image=janr/spark-streaming-kafka:v2 --submit-args="https://gist.githubusercontent.com/jrx/436a3779403158753cefaeae747de40b/raw/3e4725e7f28fca30baeb8aaaebc6189510799719/streamingWordCount.py"
```

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
