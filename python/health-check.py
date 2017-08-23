#!/usr/bin/env python3
'''
check health of spark driver and executors
'''

import re
import subprocess
import requests
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
    print (driver_id)

# parse ip address

cmd = subprocess.Popen('dcos task ' + driver_id,
                       shell=True,
                       stdout=subprocess.PIPE)
for line in cmd.stdout:
    if driver_id in line.decode("utf-8"):
        result = line.decode("utf-8")

match = re.search(r'(\d+)\.(\d+)\.(\d+)\.(\d+)', result)
if match:
    ip_address = match.group(0)
    print (ip_address)

# check if spark driver is reachable
print(url_ok("http://" + ip_address + ":4040"))