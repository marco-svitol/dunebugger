#!/usr/bin/python3
import os,schedule,time,subprocess, logging, logging.config
from datetime import time as dtime
from datetime import datetime
from itertools import tee, islice, chain
from InTime import getNTPTime
from os import path

appPath = path.join(path.dirname(path.abspath(__file__)), '..')
mainModule = "main.py"

#TODO verific timesync su orologio hw
#TODO forza switch on tramite tree state

def tmuxsessioneexist(sessname):
    cmd = ["tmux","has-session","-t",sessname]
    res = subprocess.Popen(cmd)
    res.communicate()[0]
    if res.returncode == 1: #session does not exist
        return False
    return True

def switchon():
    global showoffsched
    cmd = ["tmux","send","-t",mainpaneid,"q","ENTER"]
    subprocess.Popen(cmd)
    mainModulePath = path.join(appPath, mainModule)
    cmd = ["tmux","send","-t",mainpaneid,"python "+mainModulePath,"ENTER"]
    logger.info ("Switching on dunebugger")
    subprocess.Popen(cmd)
    showoffsched = True

def switchoff():
    global showonsched
    if timesyncJob is None:
        logger.info("Switching off dunebugger")
        cmd = ["tmux", "send-keys", "-t", mainpaneid, "C-c"]
        subprocess.Popen(cmd)
    else:
        logger.warning("Time not synced, scheduled switching off not done")
    showonsched = True
    
def tmuxnewpane():
    appPath = '/home/marco/dunebugger/app'  # Adjust this path as needed
    cmd = ["tmux", "split-window", "-h", "-c", appPath]
    subprocess.Popen(cmd).wait()  # Wait for the pane to be created

    # Get the pane ID of the last pane created
    cmd = ["tmux", "display-message", "-p", "#{pane_id}"]
    paneid = subprocess.check_output(cmd).decode('ascii').strip()
    return paneid

def set_prompt(paneid):
    cmd = ["tmux", "send-keys", "-t", paneid, "export PS1='>'", "C-m"]
    subprocess.Popen(cmd)

def previous_and_next(some_iterable):
    prevs, items, nexts = tee(some_iterable, 3)
    prevs = chain([None], prevs)
    nexts = chain(islice(nexts, 1, None), [None])
    return zip(prevs, items, nexts)

def sortonoff():
    global onseq, offseq, onoffsorted

    if offseq[0] == dtime(0,0): #se lo spegnimento è alle 0:0 è troppo complesso da gestire e lo sposto avanti un minuto. Muore nessuno dai.
        offseq[0] = dtime(0,1)

    onseq.sort()
    offseq.sort()

    if onseq[len(onseq)-1] > offseq[len(offseq)-1] and offseq[0] != dtime(0,0): #se finisce con un'accensione allora aggiungo accensione a mezzanotte
        onseq.insert(0,dtime(0,0))

    onoffsorted = [onseq[0]]

    for previous, item, nxt in previous_and_next(onseq):
        for ofs in offseq:
            if nxt is not None:
                if item < ofs < nxt:
                    onoffsorted.extend([ofs,nxt])
                    break
            else:
                if item < ofs:
                    onoffsorted.extend([ofs])
                    break

def checktimeon(d):
    if d < onoffsorted[0]: #now è prima della prima accensione
        return False
    elif d > onoffsorted[len(onoffsorted)-1]: #se sono oltre l'ultimo orario verifico se l'ultimo item è accen o spegn
        if len(onoffsorted) % 2 == 0:# se pari allora ultimo è spegnimento
            return False
        else:
            return True # se invece dispari l'ultimo è accensione
    i = 1
    for previous, item, nxt in previous_and_next(onoffsorted):
        if item < d < nxt and i % 2 == 0:
            return False
        i += 1
    return True

def checkTimeSync():
    global timesyncJob
    nettime = getNTPTime()
    if isinstance(nettime,int): #check Internet time sync
        logging.info("Time successfully synced from the net:"+time.ctime(nettime))
        if timesyncJob is not None:
            logging.info("Removing timesync job from scheduling")
            schedule.cancel_job(timesyncJob)
            timesyncJob = None
            checktimeonandswitch()
    else:
        logging.warning("Time syncing failed!")

def checktimeonandswitch():
    if checktimeon(datetime.now().time()) : #check if current time dunebugger should be on
        logger.info("Current time is after a switch on and before a switch off: switching on")
        switchon()
    else:
        logger.info("Current time is after a switch off and before a switch on: switching off")
        switchoff()

supervisorloggingConfig = path.join(appPath, 'config/supervisorlogging.conf')

logging.config.fileConfig(supervisorloggingConfig) #load logging config file
logger = logging.getLogger('supervisorLog')
logger.info('Dunebugger supervisor started')

onseq = [dtime(6,55),dtime(14,55)]
offseq = [dtime(12,30),dtime(19,30)]
onoffsorted = []

timesyncsleep = 10
timesyncmin = 180
timesyncmax = 200
timesyncJob = None

checkinterval = 20 #checkscheduling interval

showoffsched = False
showonsched = False

mainpaneid = tmuxnewpane() #creates new tmux pane and return ID num
time.sleep(1)
set_prompt(mainpaneid)

logger.info("Checking if time sync is available...")

nettime = getNTPTime() #check Internet time sync
if not isinstance(nettime,int):
    logger.warning("Not syncing first try...waiting "+str(timesyncsleep)+" secs")
    time.sleep(timesyncsleep)
    nettime = getNTPTime()
    #verify another another time. If still not syncing run a scheduled job and switch on the presepe
    if not isinstance(nettime,int):
        logger.warning ("time not synced at startup: scheduling timesyncjob with random frequency between " + str(timesyncmin) + " secs and " + str(timesyncmax) + " secs")
        timesyncJob = schedule.every(timesyncmin).to(timesyncmax).seconds.do(checkTimeSync)
        #fo = open(installfolder+"timenotsynced", "wb") #tells dunebugger that syncing is not working....
        #fo.close()
if isinstance(nettime,int):
    logger.info("...time sync ok. Time is "+time.ctime(nettime))

sortonoff() #sort, merge and clean on off sequence

if timesyncJob is None: # if time is synced check scheduling
    checktimeonandswitch()
else: #if time is not syncing switch on and warning
    logger.warning("Time not synced, forcefully switching on")
    switchon()

# se dispari, se index0 == 0:0 allora parte con spegnimento all'index1
starton = 0
if len(onoffsorted) % 2 != 0:
    starton = 1
    onoffsorted.pop(0)

for ind,onoff in enumerate(onoffsorted):
    if ind % 2 ==  starton :
        logger.debug("Adding SwitchOn scheduling at "+str(onoff))
        schedule.every().day.at(str(onoff)).do(switchon)
    else:
        logger.debug("Adding SwitchOff scheduling at "+str(onoff))
        schedule.every().day.at(str(onoff)).do(switchoff)

logger.info("Checking scheduling every "+str(checkinterval)+" seconds")

while True:
    time.sleep(checkinterval) #check scheduling every checkinterval seconds
    schedule.run_pending()
    if timesyncJob is None:
        if showoffsched:
            logger.info ("Next scheduled switchOFF at "+str(schedule.next_run()))
            showoffsched = False
        if showonsched:
            logger.info ("Next scheduled switchON at "+str(schedule.next_run()))
            showonsched = False
    else:
        showoffsched = False
        showonsched = False
