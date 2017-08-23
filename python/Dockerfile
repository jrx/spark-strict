docker run -ti openjdk:8-jre-slim bash

apt-get update
apt-get install curl python3 python3-pip -y
pip3 install virtualenv

curl https://downloads.dcos.io/binaries/cli/linux/x86-64/dcos-1.9/dcos -o dcos && 
mv dcos /usr/local/bin && 
chmod +x /usr/local/bin/dcos && 
dcos config set core.dcos_url https://janrepnak-elasticl-1wghcmd8thhve-2018568342.us-west-2.elb.amazonaws.com && 
dcos config set core.ssl_verify false &&
dcos auth login --username=bootstrapuser --password=deleteme

dcos config set core.ssl_verify false
dcos package install spark --cli
dcos spark run --help
