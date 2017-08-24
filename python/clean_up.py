#!/usr/bin/env python3
'''
kill all running drivers for a specific job name
'''

import subprocess
import json

# read spark name from env
spark_name = 'Driver for ' + str(os.environ['SPARK_NAME'])

# parse drivers from task list
cmd_read = subprocess.Popen('dcos task --json',
                       shell=True,
                       stdout=subprocess.PIPE)

data = json.load(cmd_read.stdout)

# parse drivers from task list
for task in data:
    if task["name"] == spark_name:
        print('Found ' + task["id"])

        # kill spark driver
        cmd_kill = subprocess.Popen('dcos spark kill ' + task["id"],
                                    shell=True,
                                    stdout=subprocess.PIPE)
        print(cmd_kill)