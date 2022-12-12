#!/usr/bin/env python3
#
# Mindmentum CGI script
# Remote services report their status to this script using a json message
# Returns a dashboard showing host/service status, regardless if message was posted or not
#
# Called by a URL access of the form http://mindmentum.com/cgi-bin/homelab_status.py
#
# Status is maintained in json format in HOMELAB_STATUS_LOGFILE 
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

UNIT_TEST = False

JSON_LOG_FILE_EXAMPLE = \
[
    { "site": "home", "host": "server", "process": "heartbeat", "interval": 5, "last_update": "2022-10-26 11:00", "ip": "47.33.18.178" },
    { "site": "home", "host": "server", "process": "some_service", "interval": 1, "last_update": "2022-10-26 11:01", "ip": "47.33.18.178" },
    { "site": "home", "host": "plex", "process": "heartbeat", "interval": 5, "last_update": "2022-10-26 11:00", "ip": "47.33.18.178" },
    { "site": "office", "host": "server", "process": "heartbeat", "interval": 5, "last_update": "2022-10-26 11:00", "ip": "24.182.63.74" }
]

HTML_DASHBOARD_HEADER = '''\
Content-Type: text/html

<!doctype html>
<title>Dashboard</title>
<body>
'''

HTML_DASHBOARD_FOOTER = '''
</body>
</html>
'''

from collections import namedtuple
from operator import itemgetter
import cgi, os, datetime, sys, json,  random, subprocess


if UNIT_TEST: HOMELAB_STATUS_LOGFILE = "./homelab_status.json"
else:         HOMELAB_STATUS_LOGFILE = "/big/dom/xmindmentum/homelab/homelab_status.json"

HOMELAB_STATUS_LOGFILE_ARCHIVE = HOMELAB_STATUS_LOGFILE + ".arc"
Service_t = namedtuple("Service", "site, host, process, interval, last_update, ip")


# Return True if ip responds to ping
# Return False if no response or if ip == None
def pingIP(ip):
    if not ip: return (False)
    return (not os.system("ping -c 1 -W 1 " + ip + " > /dev/null 2>&1"))

# Return the IP address of ("home" | "office")
def getIP(services, site):
    ip = None
    for service in services:
        if service.site == site and not overdue(service):
            ip = service.ip
    return (ip)

def homeIP(services):
    return (getIP(services, "home"))

def officeIP(services):
    return (getIP(services, "office"))


# Return a named tuple of the reporting service from the json dict entry
def dict2Tuple(service_d):
    service_named_tuple = Service_t( service_d["site"], service_d["host"], service_d["process"], service_d["interval"], service_d["last_update"], service_d["ip"] )
    return (service_named_tuple)

# Return a sorted list of named tuples generated from the json reporting status file
def serviceList(json_data):
    values = []
    for service_d in json_data:
        service_list = dict2Tuple(service_d)
        values.append(service_list)
    values.sort(key=itemgetter(0,1,2))
    return (values)

# return current Pacific Time
def timeNow():
    timezone_adj  = datetime.timedelta(hours=-3)    # server is on Eastern time
    now = datetime.datetime.today() + timezone_adj
    return (now)

# return current Pacific Time as a string
def timestamp():
    return (timeNow().strftime("%Y-%m-%d %H:%M"))


# compare last_update + report interval to current time
# return True if current time is later than last_update + (2 x report interval)
def overdue(service):
    last_update = datetime.datetime.strptime(service.last_update, "%Y-%m-%d %H:%M")
    report_interval = datetime.timedelta(minutes=service.interval)
    overdue_time = last_update + (2 * report_interval)
    return (timeNow() > overdue_time)

# return a static html string indicating if service is running or not
def html_status(service):
    service_str = service.last_update + ', ' + str(service.interval) + ', ' + service.site + ' ' + service.host + ' ' + service.process
    color = "green" if not overdue(service) else "red"
    return ('<span style="color:{}"><code>{}</code></span></br>'.format(color, service_str))

def html_status_h2(service):
    service_str = service.site + ' ' + service.host + ' ' + service.process
    color = "green" if not overdue(service) else "red"
    return ('<h2 style="color:{}">{}</h2>'.format(color, service_str))

def htmlIpReachable_h2(str, reachable):
    reach_str = "reachable" if reachable else "unreachable"
    color = "green" if reachable else "red"
    return ('<h2 style="color:{}">{} is {}</h2>'.format(color, str, reach_str))

# serve up html displaying status
def serveHTML():
    print (HTML_DASHBOARD_HEADER)
    try:
        f = open(HOMELAB_STATUS_LOGFILE, 'r')
        services = serviceList(json.load(f))
        f.close()
        print (timestamp())
        print (htmlIpReachable_h2("Home IP is", pingIP(homeIP(services))))
        print (htmlIpReachable_h2("Office IP is", pingIP(officeIP(services))))
        for service in services:
            print (html_status(service))
    except:
        print ("Unable to find status file")
    print (HTML_DASHBOARD_FOOTER)

# dump status file into dict, create an empty dict if file doesn't exist
# update with report from remote service
# rewrite file back out
def updateStatusFile(report):  # report is json message
    try:
        f = open(HOMELAB_STATUS_LOGFILE, 'r')
        status = json.load(f)
        f.close()
    except:
        # file doesn't exist, create empty list
        # status = []   
        pass 
    f_new_entry = True
    if UNIT_TEST: sender_ip = report["ip"]
    else:         sender_ip = os.environ['REMOTE_ADDR']
    for service_d in status:                # each entry as a dict
        service_t = dict2Tuple(service_d)   # entry as a named tuple
        if (report["site"]    != service_t.site) \
        or (report["host"]    != service_t.host) \
        or (report["process"] != service_t.process): continue
        # matched an existing entry, update it
        f_new_entry = False
        service_d["interval"]    = report["interval"]
        service_d["last_update"] = timestamp()
        service_d["ip"]          = sender_ip
    if f_new_entry:
        new = { "site":        report["site"],
                "host":        report["host"],
                "process":     report["process"],
                "interval":    report["interval"],
                "last_update": timestamp(),
                "ip":          sender_ip }
        status.append(new)

    # rewrite file back
    with open(HOMELAB_STATUS_LOGFILE, 'w') as f:
        json.dump(status, f)
    


#
# Main
#

if UNIT_TEST: data = JSON_LOG_FILE_EXAMPLE[random.randrange(len(JSON_LOG_FILE_EXAMPLE))] # one entry from example file
else:
    try:
        # json data from POST if remote service is reporting
        data = json.load(sys.stdin)           
    except:
        data = None

if data:
    updateStatusFile(data)
    #subprocess.Popen("touch ../homelab/homelab_status.json.arc", shell=True)
    subprocess.Popen("cat ../homelab/homelab_status.json >> ../homelab/homelab_status.json.arc", shell=True)

serveHTML()

    
