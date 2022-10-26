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
# JSON message format:
# { 'site' " 'home' | 'office',
#   'host' : 'host_name',               // i.e. 'host' = 'server', 'nas, 'magicmirror', 'flowmeter', ..
#   'process: '<cron job name>',
#   'subprocess' : '<subprocess name>',
#   'interval' : '5'                    // reporting interval in minutes
# }
#
# JSON log file format
# { 'site': {
#       'home': {
#           'server': {
#               'cronjob-1': {
#                   'interval' : 5,
#                   'last_update': '2022-10-26 11:00',
#                   'ip': '47.33.18.178'
#               },
#               'cronjob-2': {
#                   'interval' : 5,
#                   'last_update': '2022-10-26 11:01',
#                   'ip': '47.33.18.178'
#               }
#           },
#           'pfsense': {
#               'interval' : 5,
#               'last_update': '2022-10-26 11:00',
#               'ip': '47.33.18.178'
#           }
#       },
#       'office': {
#       }
# }
#   
#

import cgi, os, datetime, sys, json

HOMELAB_STATUS_LOGFILE = "/big/dom/xmindmentum/homelab/homelab_status.json"
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
