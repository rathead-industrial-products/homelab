#
#!/usr/bin/python3
#
# Mindmentum CGI script
# Services report their status to this script
# Responds with a dashboard showing host/service status
#
# Called by a URL access of the form http://mindmentum.com/cgi-bin/homelab_status.py
#
#############
#
# POST URL
#
# Logs status of home automation devices at hidden valley.
#
# JSON message format:
# {  'host' : 'host_name',              // i.e. 'host' = 'magicmirror', 'fencepost-back-1', ..
#   <other JSON data>
# }
#
# JSON log file format
# {
#       'ip': {
#               'addr': '0.0.0.0',
#               'last_update': '2010-12-12 11:42'
#       },
#       'hosts': [
#       {
#               'hostname': 'magicmirror',
#               'last_update': '2010-12-12 11:41',
#                <other JSON data from latest message, if any>
#       },
#       {
#               'hostname': 'fencepost-back-1',
#               'last_update': '2010-12-12 11:42'
#                <other JSON data from latest message, if any>
#       }]
# }
#
#
#

import cgi, os, datetime, sys, json

HA_STATUS_LOGFILE = "/big/dom/xmindmentum/hidden_valley/ha_status.json"

timezone_adj  = datetime.timedelta(hours=-3)    # server is on Eastern time
now = datetime.datetime.today() + timezone_adj
timestamp = now.strftime("%Y-%m-%d %H:%M")

# get hidden valley ip address
ip = os.environ['REMOTE_ADDR']

# JSON data from POST
data = json.load(sys.stdin)
host = None
if data and 'host' in data:
        host = data['host']

# in case of problems, reply to sendor with some info
print("Content-Type: text/html\n")
print (data)

if host:
    try:
        f = open(HA_STATUS_LOGFILE, 'r')
    except:
        # file doesn't exist to read json data, create dict
        updates = {}
        updates['ip'] = { 'addr': '0.0.0.0', 'last_update': 'Never' }
        updates['hosts'] = []
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
