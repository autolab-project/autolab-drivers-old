#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Supported instruments (identified):
- 
"""

import os
import time
from numpy import frombuffer,int8


class Driver():

    category = 'Oscilloscope'
    #['Oscilloscope','Optical source','Spectrum analyser','Motion controller','Function generator','Power meter','Electrical source','Optical frame', 'Electrical frame','Optical shutter','PID controller','Temperature controller']

    def __init__(self,nb_channels=4):
              
        self.nb_channels = int(nb_channels)
        
        for i in range(1,self.nb_channels+1):
            setattr(self,f'channel{i}',Channel(self,i))
    
    
    ### User utilities
    def get_data_channels(self,channels=[]):
        """Get all channels or the ones specified"""
        previous_trigger_state = self.get_previous_trigger_state()
        self.stop()
        while not self.is_stopped():time.sleep(0.05)
        if channels == []: channels = list(range(1,self.nb_channels+1))
        for i in channels:
            if not(getattr(self,f'channel{i}').is_active()): continue
            getattr(self,f'channel{i}').get_data_raw()
            getattr(self,f'channel{i}').get_log_data()
        self.set_previous_trigger_state(previous_trigger_state)
        
    def save_data_channels(self,filename,channels=[],FORCE=False):
        if channels == []: channels = list(range(1,self.nb_channels+1))
        for i in channels:
            getattr(self,f'channel{i}').save_data_raw(filename=filename,FORCE=FORCE)
            getattr(self,f'channel{i}').save_log_data(filename=filename,FORCE=FORCE)
        
    ### Trigger functions
    def single(self):
        pass
    def stop(self):
        pass
    def is_stopped(self):
        return 'STOP' in self.query('TRMD?')            # typical example when response from scope is "TRMD STOP"
    def get_previous_trigger_state(self):
        return str(previous_trigger_state)
        
    def set_previous_trigger_state(self,prious_trigger_state):
        pass
        
    ### Cross-channel settings 
    def set_encoding(self):
        return str
    def get_encoding(self):
        return str


#################################################################################
############################## Connections classes ##############################
class Driver_VISA(Driver):
    def __init__(self, address='TCPIP::192.168.0.3::INSTR', **kwargs):
        import pyvisa as v
        
        rm        = v.ResourceManager()
        self.inst = rm.get_instrument(address)
        Driver.__init__(self, **kwargs)
        
    def query(self,command):
        self.write(command)
        return self.read()
    def read(self):
        return self.inst.read()
    def write(self,command):
        self.inst.write(command)
    def close(self):
        self.inst.close()

class Driver_VXI11(Driver):
    def __init__(self, address='192.168.0.3', **kwargs):
        import vxi11 as v
    
        self.inst = v.Instrument(address)
        Driver.__init__(self, **kwargs)

    def query(self, command, nbytes=100000000):
        self.write(command)
        return self.read(nbytes)
    def read(self,nbytes=100000000):
        self.inst.read(nbytes)
    def write(self,cmd):
        self.inst.write(cmd)
    def close(self):
        self.inst.close()
############################## Connections classes ##############################
#################################################################################


class Channel():
    def __init__(self,dev,channel):
        self.channel = int(channel)
        self.dev     = dev
        self.autoscale = False
    
    
    def get_data_raw(self):
        #self.dev.write(...)
        #self.data_raw = self.dev.read()
        #return self.data_raw
    def get_log_data(self):
        #self.dev.write(...)
        #self.log_data = self.dev.read()
        #return self.log_data
    def get_data(self):
        return frombuffer(self.get_data_raw(),int8)

        
    def save_data_raw(self,filename,FORCE=False):
        temp_filename = f'{filename}_DSACHAN{self.channel}'
        if os.path.exists(os.path.join(os.getcwd(),temp_filename)) and not(FORCE):
            print('\nFile ', temp_filename, ' already exists, change filename or remove old file\n')
            return
        f = open(temp_filename,'wb')# Save data
        f.write(self.data_raw)
        f.close()
    def save_log_data(self,filename,FORCE=False):
        temp_filename = f'{filename}_DSACHAN{self.channel}.log'
        if os.path.exists(os.path.join(os.getcwd(),temp_filename)) and not(FORCE):
            print('\nFile ', temp_filename, ' already exists, change filename or remove old file\n')
            return
        f = open(temp_filename,'w')
        f.write(self.log_data)
        f.close()
    
    
    def get_data_numerical(self):
        return array_of_float
    def save_data_numerical(self):
        return array_of_float
    
    # additionnal functions
    def get_min(self):
        return float
    def get_max(self):
        return float
    def get_mean(self):
        return float
       
    
    def set_autoscale_enabled(bool):
        #self.autoscale = 
        pass
    def is_autoscable_enabled():
        return bool
    def do_autoscale():
        pass
       
    def is_active():
        pass


