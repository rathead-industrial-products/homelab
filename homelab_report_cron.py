
# JSON message reporting format:
# { 'site' " 'home' | 'office',
#   'host' : 'host_name',               // i.e. 'host' = 'server', 'nas, 'magicmirror', 'flowmeter', ..
#   'process: '<cron job name>',
#   'interval' : '5'                    // reporting interval in minutes
#                                       // last_update and reporting device ip are obtained by the server
# }

SITE     = "home"
HOST     = "sshVM"
PROCESS  = "heartbeat"
INTERVAL = 1    # report health every 1 minute

REMOTE_URL = "http://mindmentum.com/cgi-bin/homelab_status.py"

import requests

# post to remote server
service  = { "site": SITE, "host": HOST, "process": PROCESS, "interval": INTERVAL }
response = requests.post(REMOTE_URL, json=service)

