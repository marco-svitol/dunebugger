import subprocess, time, os
global mainpaneid

# def tmuxsessioneexist(sessname):
#     cmd = ["tmux","has-session","-t",sessname]
#     res = subprocess.Popen(cmd)
#     res.communicate()[0]
#     if res.returncode == 1: #session does not exist
#         return False
#     return True

def start():
    sendcmd(mainpaneid,["k","ENTER"])
    sendcmd(mainpaneid,["python /home/pi/dunebugger/cycle.py","ENTER"])

def switchon():
    sendcmd(mainpaneid,["on","ENTER"])  

def switchoff():
    sendcmd(mainpaneid,["off","ENTER"])

def sendcmd(cmdlist):
    cmd = ["tmux","send","-t",mainpaneid]
    cmd.append(cmdlist)
    subprocess.Popen(cmd)

def newpane():
    pipepath = "paneid"
    cmd = ["tmux","split-window","-h","-c","/home/pi/dunebugger"]
    subprocess.Popen(cmd)
    if not os.path.exists(pipepath):
        os.mkfifo(pipepath)
    cmd = ["tmux","send","echo $TMUX_PANE > ",pipepath,"ENTER"]
    subprocess.Popen(cmd)
    time.sleep(0.5)
    pipe = os.open(pipepath,os.O_RDONLY)
    paneid = (os.read(pipe,100)).decode('ascii')
    os.close(pipe)
    os.remove(pipepath)
    return paneid.strip()

mainpaneid = newpane()
start()
