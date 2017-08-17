# spark-strict


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
