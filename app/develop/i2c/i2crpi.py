#!/usr/bin/env python3
# ++++++ one function i2c access +++++++
# Contributed by Raju and updated by Jim
# June 2018 added clock stectch timeout
#   The clock stretch time out is implemented in c as it is only a one off call
#   and besides I don't know how to do it in python. See i2c_set_tout.c for
#   more details.   
#
# July 4 2018
#   Modified to work in any directory
#
# Use:
# import i2crpi 
# dev = i2crpi.IIC(timeout=4000) # default works with, bus 1 and BCM2835
# dev.i2c(<adr>,[out,out..],return,optional 0) 
#
import io,os.path
import fcntl
import subprocess
from sys import version_info

I2C_SLAVE=0x0703
_ABSPATH__ = os.path.abspath(__file__)
_I2CFPATH__, _I2CFFILE__ = os.path.split(_ABSPATH__)
I2CSTRETCH = 'i2c_set_tout'
I2CSTRETCHFULL = _I2CFPATH__+'/'+I2CSTRETCH


# ==============================================================================
# i2c_base is taken from the broadcom data sheet for BCn
# timeout Number of SCL clock cycles to wait after the rising edge 
#         of SCL before deciding that the slave is not responding.
#         at 100kHZ 2000 = 20mS (1 cycle is 10uS)
# bus is normally 1, if this is changed then the base address needs changing 
class IIC:
   def __init__(self, i2c_base=0x20804000, timeout=3000, bus=1):
      self.fr = io.open("/dev/i2c-"+str(bus), "rb", buffering=0)
      self.fw = io.open("/dev/i2c-"+str(bus), "wb", buffering=0)
      if not os.path.isfile(I2CSTRETCHFULL):
          # no compiled file, try to compile
          print("Building ",I2CSTRETCHFULL)
          subprocess.check_output(["gcc", "-o", I2CSTRETCHFULL, I2CSTRETCHFULL+'.c'])
      if os.path.isfile(I2CSTRETCHFULL):   
          rv = subprocess.check_output(['sudo',I2CSTRETCHFULL,str(i2c_base),str(timeout)])
          if type(rv) == bytes: rv = rv.decode('utf-8') # for verison 3
          print(rv)
      else:
         print("cant build "+I2CSTRETCH+" working without")

   def write(self,adr, data):
      fcntl.ioctl(self.fw, I2C_SLAVE, adr)  
      if type(data) is list:
         data = bytes(data)
      self.fw.write(data)

   # return as list of integers
   def read(self,adr, count):
      fcntl.ioctl(self.fr, I2C_SLAVE, adr)
      l = []
      s = self.fr.read(count)
      if len(s) != 0:
         for n in s:
            if version_info[0] < 3:
                l.append(ord(n))
            else:
                l.append(n)          
      return l
    

   def close(self):
      self.fw.close()
      self.fr.close()
      
   # If general call is set then that address is used for writing instead
   # of the device address, but the device address is used for reading (if any)
   # e.g dev.i2c(35,[1,2],1) # no general call
   #     dev.i2c(35,[1,2,3],1,0) # using general call
   def i2c(self,adr,inputv,outputn,gc=None):
       if isinstance(inputv,list):
           b = bytes(inputv)
           if gc is not None:
               if version_info[0] < 3:
                   self.write(gc,bytearray(inputv))
               else:
                    self.write(gc,b)
           else: 
               if version_info[0] < 3:   
                  self.write(adr,bytearray(inputv))
               else:
                  self.write(adr,b)
           # do output
           if outputn > 0:              
               return self.read(adr,outputn)
       else:
           print('iic input must be a list')       
      
