# spark-strict

## 1. Install Spark in Strict Mode

- Setup service account and secret

```shell
dcos security org service-accounts keypair /tmp/spark-private.pem /tmp/spark-public.pem
dcos security org service-accounts create -p /tmp/spark-public.pem -d "Spark service account" spark-principal
dcos security secrets create-sa-secret --strict /tmp/spark-private.pem spark-principal spark/secret
```

- Grant permissions to the Spark Service Account

```shell
dcos security org users grant spark-principal dcos:mesos:agent:task:user:root create
dcos security org users grant spark-principal "dcos:mesos:master:framework:role:*" create
dcos security org users grant spark-principal dcos:mesos:master:task:app_id:/spark create
dcos security org users grant spark-principal dcos:mesos:master:task:user:nobody create
dcos security org users grant spark-principal dcos:mesos:master:task:user:root create
```

- Grant  permissions to Marathon in order to the Spark the dispatcher in root

```shell
dcos security org users grant dcos_marathon dcos:mesos:master:task:user:root create
```

- Create a configurationfile **/tmp/spark.json** and set the Spark principal and secret

```json
cat <<EOF > /tmp/spark.json
{
  "service": {
    "name": "spark",
    "service_account": "spark-principal",
    "service_account_secret": "spark/secret",
    "user": "root"
  }
}
EOF
```

- Install Spark using the config.json file

```shell
dcos package install --options=/tmp/spark.json spark --yes
```

- Add the name of the principal to the Spark run command

```shell
dcos spark run --verbose --submit-args=" \
--conf spark.mesos.executor.docker.image=mesosphere/spark:2.3.1-2.2.1-2-hadoop-2.6 \
--conf spark.mesos.executor.docker.forcePullImage=true \
--conf spark.mesos.containerizer=mesos \
--conf spark.mesos.principal=spark-principal \
--class org.apache.spark.examples.SparkPi \
https://downloads.mesosphere.com/spark/assets/spark-examples_2.11-2.0.1.jar 30"
```

## 2. Create IAM user to start Spark jobs without root permissions

- Create a user called `test`

```shell
dcos security org users create test --password test123
```

- Set the following permissions for the service account

```shell
dcos security org users grant test dcos:adminrouter:ops:mesos full
dcos security org users grant test dcos:adminrouter:ops:mesos-dns full
dcos security org users grant test dcos:adminrouter:ops:slave full
dcos security org users grant test dcos:adminrouter:service:marathon full
dcos security org users grant test dcos:adminrouter:service:spark full
dcos security org users grant test dcos:mesos:agent:framework:role full
dcos security org users grant test dcos:mesos:master:framework:role full
dcos security org users grant test dcos:service:marathon:marathon:services:/spark read
```

- Login as user `test`

```shell
dcos auth login --username=test --password=test123
```

- Submit a Spark Job

```shell
dcos spark run --verbose --submit-args=" \
--conf spark.mesos.executor.docker.image=mesosphere/spark:2.3.1-2.2.1-2-hadoop-2.6 \
--conf spark.mesos.executor.docker.forcePullImage=true \
--conf spark.mesos.containerizer=mesos \
--conf spark.mesos.principal=spark-principal \
--class org.apache.spark.examples.SparkPi \
https://downloads.mesosphere.com/spark/assets/spark-examples_2.11-2.0.1.jar 30"
```

- Find driver ip address using dcos spark status

```shell
dcos spark status driver-20170817131417-0006
```

## 3. Submit and restart Spark Streaming Jobs if they are failing

- For this demo install Kafka in Strict Mode

```shell
dcos security org service-accounts keypair /tmp/kafka-private-key.pem /tmp/kafka-public-key.pem
dcos security org service-accounts create -p /tmp/kafka-public-key.pem -d "Kafka service account" kafka-principal
dcos security secrets create-sa-secret --strict /tmp/kafka-private-key.pem kafka-principal kafka/secret
```

- Grant Permissions to Kafka

```shell
dcos security org users grant kafka-principal dcos:mesos:master:framework:role:kafka-role create
dcos security org users grant kafka-principal dcos:mesos:master:reservation:role:kafka-role create
dcos security org users grant kafka-principal dcos:mesos:master:volume:role:kafka-role create
dcos security org users grant kafka-principal dcos:mesos:master:task:user:nobody create
dcos security org users grant kafka-principal dcos:mesos:master:reservation:principal:kafka-principal delete
dcos security org users grant kafka-principal dcos:mesos:master:volume:principal:kafka-principal delete
```

- Create Kafka configuration file **/tmp/spark.json**

```shell
cat <<EOF > /tmp/kafka.json
{
  "service": {
    "name": "kafka",
    "user": "nobody",
    "service_account": "kafka-principal",
    "service_account_secret": "kafka/secret"
  }
}
EOF
```

- Install Kafka

```shell
dcos package install --options=/tmp/kafka.json kafka
```

- Setup a topic

```shell
dcos kafka topic create mytopic --replication=2 --partitions=4
```

### 3.1 Use --supervise flag

- Submit a long running Job and set the flag `--supervise` to automatically restart the driver, if it's failing

```shell
dcos spark run --verbose --submit-args=" \
--supervise \
--conf spark.app.name=wordcount \
--conf spark.mesos.containerizer=mesos \
--conf spark.mesos.principal=spark-principal \
--conf spark.mesos.driverEnv.SPARK_USER=root \
--conf spark.cores.max=6 \
--conf spark.mesos.executor.docker.image=janr/spark-streaming-kafka:2.1.0-2.2.1-1-hadoop-2.6-nobody-99 \
--conf spark.mesos.executor.docker.forcePullImage=true \
https://gist.githubusercontent.com/jrx/56e72ada489bf36646525c34fdaa7d63/raw/90df6046886e7c50fb18ea258a7be343727e944c/streamingWordCount-CNI.py"
```

- Jump into the container of the Spark driver and kill all processes

```shell
dcos task exec -it driver-20180829130652-0008 bash
kill -9 -1
```

The driver should be automatically restarted.

- You can kill the driver by running:

```shell
dcos spark kill driver-20180829130652-0008
```

### 3.2 Use Marathon for submitting the Spark Job

```json
{
  "id": "/stream",
  "cpus": 1,
  "mem": 1024,
  "instances": 1,
  "user": "root",
  "env": {
    "SPARK_NAME": "wordcount",
    "MESOS_CONTAINERIZER": "mesos",
    "MESOS_PRINCIPAL": "spark-principal",
    "MESOS_ROLE": "*",
    "SPARK_USER": "root",
    "SPARK_DRIVER_CORES": "1",
    "SPARK_DRIVER_MEM": "512m",
    "SPARK_CORES_MAX": "6",
    "SPARK_DOCKER_IMAGE": "janr/spark-streaming-kafka:2.1.0-2.2.1-1-hadoop-2.6-nobody-99",
    "SPARK_EXECUTOR_HOME": "/opt/spark/dist",
    "SPARK_JAR": "streamingWordCount-CNI.py",
    "SPARK_ARGS": ""
  },
  "fetch": [
    {
      "uri": "https://gist.githubusercontent.com/jrx/56e72ada489bf36646525c34fdaa7d63/raw/90df6046886e7c50fb18ea258a7be343727e944c/streamingWordCount-CNI.py"
    }
  ],
  "cmd": "/opt/spark/dist/bin/spark-submit --conf spark.app.name=${SPARK_NAME} --conf spark.mesos.containerizer=${MESOS_CONTAINERIZER} --conf spark.mesos.principal=${MESOS_PRINCIPAL} --conf spark.mesos.role=${MESOS_ROLE} --conf spark.mesos.driverEnv.SPARK_USER=${SPARK_USER} --conf spark.driver.cores=${SPARK_DRIVER_CORES} --conf spark.driver.memory=${SPARK_DRIVER_MEM} --conf spark.cores.max=${SPARK_CORES_MAX} --conf spark.mesos.executor.docker.image=${SPARK_DOCKER_IMAGE} --conf spark.executor.home=${SPARK_EXECUTOR_HOME} ${MESOS_SANDBOX}/${SPARK_JAR} ${SPARK_ARGS}",
  "container": {
    "type": "MESOS",
    "docker": {
      "image": "janr/spark-streaming-kafka:2.1.0-2.2.1-1-hadoop-2.6-nobody-99",
      "forcePullImage": false
    },
    "portMappings": [
      {
        "containerPort": 4040,
        "hostPort": 0,
        "protocol": "tcp",
        "name": "driver-ui"
      }
    ]
  },
  "networks": [
    {
      "mode": "container/bridge"
    }
  ],
  "upgradeStrategy": {
    "maximumOverCapacity": 0,
    "minimumHealthCapacity": 0
  },
  "labels": {
    "MARATHON_SINGLE_INSTANCE_APP": "true"
  },
  "requirePorts": false
}
```
