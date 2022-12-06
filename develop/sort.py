from datetime import time as dtime
from datetime import datetime
from itertools import tee, islice, chain

def previous_and_next(some_iterable):
    prevs, items, nexts = tee(some_iterable, 3)
    prevs = chain([None], prevs)
    nexts = chain(islice(nexts, 1, None), [None])
    return zip(prevs, items, nexts)
#acc spe acc anche con acc 0:0 inserisce 0:0 dispari
#acc spe OK anche con acc 0:0 pari
#spe acc spe OK pari
#spe acc anche con acc 0:0 inserisce 0:0 dispari
# se dispari, se index0 == 0:0 allora parte con spegnimento all'index1

onseq =[dtime(21,54),dtime(21,56)]
offseq = [dtime(21,55)]

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


sortonoff()
for onoff in onoffsorted:
    print (str(onoff))
print (str(checktimeon(datetime.now().time())))

starton = 0
if len(onoffsorted) % 2 != 0:
    starton = 1
    onoffsorted.pop(0)

for ind,onoff in enumerate(onoffsorted):
    if ind % 2 ==  starton :
        print("Adding SwitchOn scheduling at "+str(onoff))
        print ("schedule.every().day.at(str(onoff.hour)+:+str(onoff.minute)).do(switchon)")
    else:
        print("Adding SwitchOff scheduling at "+str(onoff))
        print("schedule.every().day.at(str(onoff.hour)+:+str(onoff.minute)).do(switchoff)")


