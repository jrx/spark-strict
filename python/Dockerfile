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