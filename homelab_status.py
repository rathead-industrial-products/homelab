#
#!/usr/bin/python3
#
# Mindmentum CGI script
# Services report their status to this script using a json message
# With no input message, the script responds with a dashboard showing host/service status
#
# Called by a URL access of the form http://mindmentum.com/cgi-bin/homelab_status.py
#
# Status is maintained in the homelab_status.json 
#
#############
#
# POST URL
#
# Logs status of homelab services.
#
# JSON message reporting format:
# { 'site' " 'home' | 'office',
#   'host' : 'host_name',               // i.e. 'host' = 'server', 'nas, 'magicmirror', 'flowmeter', ..
#   'process: '<cron job name>',
#   'interval' : '5'                    // reporting interval in minutes
#                                       // last_update and reporting device ip are obtained by the server
# }
#

JSON_LOG_FILE_EXAMPLE = \
{
    "site": [{
            "name": "home",
            "host": [{
                    "name": "server",
                    "process": [{
                            "name": "heartbeat",
                            "interval" : 5,
                            "last_update": "2022-10-26 11:00",
                            "ip": "47.33.18.178"
                        },
                        {
                            "name": "some_service",
                            "interval" : 1,
                            "last_update": "2022-10-26 11:01",
                            "ip": "47.33.18.178"
                        }
                    ]
                },
                {   "name": "plex",
                    "process": {
                        "name": "heartbeat",
                        "interval" : 5,
                        "last_update": "2022-10-26 11:00",
                        "ip": "47.33.18.178"
                    }
                }
            ]
        },
        {   "name": "office",
            "host": {
                "name": "server",
                "process": {
                    "name": "heartbeat",
                    "interval" : 5,
                    "last_update": "2022-10-26 11:00",
                    "ip": "47.33.18.178"
                }
            }
        }
    ]
}



from operator import itemgetter
import cgi, os, datetime, sys, json

HOMELAB_STATUS_LOGFILE = "/big/dom/xmindmentum/homelab/homelab_status.json"

# Return lists of keys of the json dict that span from the root to the leaf
# The entire leaf node is included at the end of the list
# e.g ("home", "server", "heartbeat", <heartbeat dict>)
def flatten(json_t):
    def _makeList(value): # if value is not a list, return it as a one-element list, otherwise return value
        if not isinstance(value, list): return ([value,])
        else:                           return (value)

    def _isLeaf(dict_t):  # return True if leaf node
        return ("interval" in dict_t.keys())

    branches = []
    for site in _makeList(json_t["site"]):
        for host in _makeList(site["host"]):
            if _isLeaf(host):
                branches.append([site["name"], host["name"], host])
            else:
                for process in _makeList(host["process"]):
                   branches.append([site["name"], host["name"], process["name"], process]) 

    return (branches)


services = sorted(flatten(JSON_LOG_FILE_EXAMPLE), key=itemgetter(0,1,2))
for service in services:
    print (service)


'''
UPDATE_STATUS = False   # flags
REPORT_STATUS = False

timezone_adj  = datetime.timedelta(hours=-3)    # server is on Eastern time
now = datetime.datetime.today() + timezone_adj
timestamp = now.strftime("%Y-%m-%d %H:%M")

# get sender's ip address
ip = os.environ['REMOTE_ADDR']

# JSON data from POST
data = json.load(sys.stdin)
if data:
    UPDATE_STATUS = True
else:
    REPORT_STATUS = True

# in case of problems, reply to sendor with some info
print("Content-Type: text/html\n")
print (data)

# dump status file into dict for updating, create an empty dict if file doesn't exist
try:
    f = open(HOMELAB_STATUS_LOGFILE, 'r')
except:
    updates = {}        # file doesn't exist, create empty dict
else:
    updates = json.load(f)
    f.close()

    #
    # update dict
    #
    # do not update ip address if reporting node is 'fireriser' or 'wiringcloset' (not in the home network)
    #
    if ((host != 'fireriser') and (host != 'wiringcloset')):
        if updates['ip']['addr'] != ip:
            updates['ip']['addr'] = ip
        updates['ip']['last_update'] = timestamp     # changed or unchanged ip has been confirmed at this time

    num_hosts = len(updates['hosts'])
    # replace last update time for host with current time
    hostfound = False
    for i in range(num_hosts):
        if updates['hosts'][i]['hostname'] == host:
            updates['hosts'][i]['last_update'] = timestamp
            hostfound = True
            break            # to save current value of i, used below

    if not hostfound:   # host not in database, add it
        updates['hosts'].append({ 'hostname': host, 'last_update': timestamp })
        i = -1

    updates['hosts'][i].update(data)    # i is still in scope from for i in range(num_hosts)
    del updates['hosts'][i]['host']     # 'host' in json is already saved as 'hostname' in the logfile


    # rewrite file
    with open(HA_STATUS_LOGFILE, 'w') as f:
        json.dump(updates, f)
        
'''
