#!/usr/bin/env python3
'''
check health of the spark driver
'''

import re
import subprocess
import requests
import json


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

# parse ip address
cmd = subprocess.Popen('dcos task --json ' + driver_id,
                       shell=True,
                       stdout=subprocess.PIPE)

data = json.load(cmd.stdout)

# parse drivers from task list
for task in data:
    if task["id"] == driver_id:
        ip_address = task["statuses"][0]["container_status"]["network_infos"][0]["ip_addresses"][0]["ip_address"]
        print('Found IP address: ' + ip_address)

# check if spark driver is reachable
print(url_ok("http://" + ip_address + ":4040"))