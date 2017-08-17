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

## 2. Access driver logs without root permissions

- Create a user `test` that has the following permissions

```
dcos:adminrouter:service:marathon full
dcos:adminrouter:service:spark full
dcos:service:marathon:marathon:services:/spark read
```

TODO: Set correct permissions to retrieve logs

- Login as user `test`

```
dcos auth login
```

- Submit a Spark Job

```
dcos spark run --verbose --submit-args="--conf spark.mesos.executor.docker.image=mesosphere/spark:1.1.1-2.2.0-hadoop-2.6 --conf spark.mesos.executor.docker.forcePullImage=true --conf spark.mesos.principal=spark-principal --conf spark.mesos.driverEnv.LIBPROCESS_SSL_CA_DIR=.ssl/ --conf spark.mesos.driverEnv.LIBPROCESS_SSL_CA_FILE=.ssl/ca.crt --conf spark.mesos.driverEnv.LIBPROCESS_SSL_CERT_FILE=.ssl/scheduler.crt --conf spark.mesos.driverEnv.LIBPROCESS_SSL_KEY_FILE=.ssl/scheduler.key --conf spark.mesos.driverEnv.MESOS_MODULES=file:///opt/mesosphere/etc/mesos-scheduler-modules/dcos_authenticatee_module.json --conf spark.mesos.driverEnv.MESOS_AUTHENTICATEE=com_mesosphere_dcos_ClassicRPCAuthenticatee --conf spark.mesos.containerizer=mesos --class org.apache.spark.examples.SparkPi https://downloads.mesosphere.com/spark/assets/spark-examples_2.11-2.0.1.jar 30"
```

- View the driver status

```
dcos spark status driver-20170817131417-0006
```

- View the driver logs

```
dcos spark log driver-20170817131417-0006
```

## 3. Restart Spark Streaming Jobs if they are failing

- Submit a long running Job and the flag --supervise

```
dcos spark run --verbose --submit-args="--supervise --conf spark.mesos.executor.docker.image=janr/spark-streaming-kafka:v2 --conf spark.mesos.executor.docker.forcePullImage=true --conf spark.mesos.principal=spark-principal --conf spark.mesos.driverEnv.LIBPROCESS_SSL_CA_DIR=.ssl/ --conf spark.mesos.driverEnv.LIBPROCESS_SSL_CA_FILE=.ssl/ca.crt --conf spark.mesos.driverEnv.LIBPROCESS_SSL_CERT_FILE=.ssl/scheduler.crt --conf spark.mesos.driverEnv.LIBPROCESS_SSL_KEY_FILE=.ssl/scheduler.key --conf spark.mesos.driverEnv.MESOS_MODULES=file:///opt/mesosphere/etc/mesos-scheduler-modules/dcos_authenticatee_module.json --conf spark.mesos.driverEnv.MESOS_AUTHENTICATEE=com_mesosphere_dcos_ClassicRPCAuthenticatee https://gist.githubusercontent.com/jrx/436a3779403158753cefaeae747de40b/raw/3e4725e7f28fca30baeb8aaaebc6189510799719/streamingWordCount.py"
```

- Find the node the driver is running on

```
dcos task
```

- Connect to the node and kill the task

```
docker ps
docker kill <id>
```

The driver should be restarted.

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
