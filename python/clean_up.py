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