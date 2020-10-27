#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Supported instruments (identified):
- 
"""

import os
import time
from numpy import frombuffer,int8,ndarray

help=\
f"""

----------------  Extra infos:  ----------------
    Datas are recorded in int8 format
    
    Headers contain:
    :WFMOUTPRE:BYT_NR 2;BIT_NR 16;ENCDG ASCII;BN_FMT RI;BYT_OR
    MSB;WFID 'Ch1, DC coupling, 100.0mV/div, 4.000us/div, 10000
    points, Sample mode';NR_PT 10000;PT_FMT Y;XUNIT 's';XINCR
    4.0000E-9;XZERO - 20.0000E-6;PT_OFF 0;YUNIT 'V';YMULT
    15.6250E-6;YOFF :”6.4000E+3;YZERO 0.0000
    
    To retrieve real value:
    value_in_units = ((curve_in_dl - YOFf_in_dl) * YMUlt) + YZEro_in_units
"""
    
class Driver():
    
    def __init__(self,nb_channels=4):
        
        self.modules = []
              
        self.nb_channels = int(nb_channels)
        
        self.write('HORizontal:RECOrdlength?')
        string = self.read()
        length = string[len(':HORIZONTAL:RECORDLENGTH '):]
        self.write('DAT:STAR 1')
        self.write(f'DAT:STOP {length}')
        
        for i in range(1,self.nb_channels+1):
            setattr(self,f'channel{i}',Channel(self,i))
            self.modules.append(f'channel{i}')
    
    ### User utilities
    def get_data_channels(self,channels=[]):
        """Get all channels or the ones specified"""
        self.stop()
        while not self.is_stopped():time.sleep(0.05)
        if channels == []: channels = list(range(1,self.nb_channels+1))
        for i in channels:
            time.sleep(0.1)
            getattr(self,f'channel{i}').get_data_raw()
            getattr(self,f'channel{i}').get_log_data()
        self.run()
        
    def save_data_channels(self,filename,channels=[],FORCE=False):
        if channels == []: channels = list(range(1,self.nb_channels+1))
        for i in channels:
            getattr(self,f'channel{i}').save_data_raw(filename=filename,FORCE=FORCE)
            getattr(self,f'channel{i}').save_log_data(filename=filename,FORCE=FORCE)
        
    ### Trigger functions
    def run(self):
        self.scope.write('ACQUIRE:STATE ON')
    def stop(self):
        self.scope.write('ACQUIRE:STATE OFF')
    def is_stopped(self):
        return '0' in self.query('ACQUIRE:STATE?')


    def get_driver_model(self):
        model = []
        for i in range(1,self.nb_channels+1):
            model.append({'element':'module','name':f'channel{i}','object':getattr(self,f'channel{i}'), 'help':'Channels'})
        model.append({'element':'variable','name':'is_stopped','read':self.is_stopped, 'type':bool,'help':'Query whether scope is stopped'})
        model.append({'element':'action','name':'stop','do':self.stop,'help':'Set stop mode for trigger'})
        model.append({'element':'action','name':'run','do':self.run,'help':'Set run mode for trigger'})
        return model


#################################################################################
############################## Connections classes ##############################
class Driver_VXI11(Driver):
    def __init__(self, address='192.168.0.8', **kwargs):
        import vxi11 as v
    
        self.inst = v.Instrument(address)
        Driver.__init__(self, **kwargs)

    def query(self, command, nbytes=100000000):
        self.write(command)
        return self.read(nbytes)
    def read_raw(self):
        self.inst.read_raw()
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
        self.dev  = dev
        self.autoscale = False
    
    
    def get_data_raw(self):
        self.dev.write(f'DAT:SOU CH{self.channel}')
        self.dev.write('DAT:ENC FAS')
        self.dev.write('WFMO:BYT_Nr 1')
        self.dev.write('CURV?')
        self.data_raw = self.dev.read_raw()
        self.data_raw = self.data_raw[7:-1]
        return self.data_raw
    def get_log_data(self):
        self.dev.write(f'DAT:SOU CH{self.channel}')
        self.dev.write('WFMO?')
        self.log_data = self.dev.read()
        return self.log_data     
    def get_data(self):
        return frombuffer(self.get_data_raw(),int8)
        
    def save_data_raw(self,filename,FORCE=False):
        temp_filename = f'{filename}_TDS5104BCH{self.channel}'
        if os.path.exists(os.path.join(os.getcwd(),temp_filename)) and not(FORCE):
            print('\nFile ', temp_filename, ' already exists, change filename or remove old file\n')
            return
        f = open(temp_filename,'wb')# Save data
        f.write(self.data_raw)
        f.close()
    def save_log_data(self,filename,FORCE=False):
        temp_filename = f'{filename}_TDS5104BCH{self.channel}.log'
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


    def get_driver_model(self):
        model = []
        model.append({'element':'variable','name':'trace_raw','type':bytes,'read':self.get_data_raw,'help':'Get the current trace in bytes'})
        model.append({'element':'variable','name':'trace','type':ndarray,'read':self.get_data,'help':'Get the current trace in a numpy array of integers'})
        return model
