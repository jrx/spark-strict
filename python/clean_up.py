#!/usr/bin/env python3
'''
kill all running drivers for a specific job name
'''

import subprocess
import re
import os

# read spark name from env
spark_name = 'Driver for ' + str(os.environ['SPARK_NAME'])

# parse drivers from task list
cmd = subprocess.Popen('dcos task',
                       shell=True,
                       stdout=subprocess.PIPE)
for line in cmd.stdout:
    if spark_name in line.decode("utf-8"):
        result = line.decode("utf-8")

        match = re.search(r'driver-(\d+)-(\d+)', result)
        if match:
            driver_id = match.group(0)
            print('found: ' + driver_id)

            # kill spark driver
            cmd = subprocess.Popen('dcos spark kill ' + driver_id,
                                   shell=True,
                                   stdout=subprocess.PIPE)
            print(cmd)