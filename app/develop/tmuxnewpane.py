import time,os, subprocess

def tmuxnewpane():
    pipepath = "paneid"
    cmd = ["tmux","split-window","-h"]
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

paneid = tmuxnewpane()
cmd = ["tmux","send","-t",paneid,"yeahhhhhhhhh","ENTER"]
subprocess.Popen(cmd)
