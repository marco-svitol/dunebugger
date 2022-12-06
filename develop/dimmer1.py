#!/usr/bin/env python3
# coding: utf8

import smbus,time,sys

bus = smbus.SMBus(1)

def wdata(channel,val):
    global address
    bus.write_byte_data(address, 128, 19)
    #bus.write_byte_data(address, 0, int(val))

def wblock(channel,val):
    global address
    bus.write_i2c_block_data(address,0x82,[val])

def rdata():
    global address
    a =  bus.read_byte_data(address,0x80)
    print (a)

def rblock():
    global address
    reg = bus.read_i2c_block_data(address,0x80,16)
    print (reg)

def rb():
    global address
    a = bus.read_byte(address)
    print (a)

address = 0x27
channel = int(sys.argv[1])
value = int(sys.argv[2])
#speed = sys.argv[3]

print ('arguments '+sys.argv[1]+' '+sys.argv[2]) # '+sys.argv[3])
#wblock(channel,value)
wdata(channel,value)
rb()
rblock()
