import sys
sys.path.insert(0,'/home/pi/dunebugger')

import InTime
from datetime import datetime, timedelta

d = datetime(2020,1,4,18,31,0)
print (d)
if InTime.duranteCelebrazioni(d,372):#datetime.now()) :
    print (True)
else:
    print (False)
