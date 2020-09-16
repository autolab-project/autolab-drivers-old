#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import inspect
from functools import partial
import warnings

class utilities():
    def __init__(self):
        warnings.filterwarnings("ignore")  # to remove a deprecation warning (VISA and inspect...)
        
    def print_help_classes(self,classes_list):
        return f'\n[Classes]\n{", ".join(classes_list)}\n'
    def print_help_methods(self,methods_list):
        return f'\n[Methods]\n{", ".join(methods_list)}\n'
    def print_help_methods_arguments(self,I,methods_list):
        s = f'\n[Methods arguments]'
        for command in methods_list:
            com = command
            coms = com.split('.')
            coms1_attr = getattr(I,coms[1])
            if len(coms)==2: s = s + f'\n{command}   {inspect.signature(coms1_attr)}'
            else: s = s + f'\n{command}   {inspect.signature(getattr(coms1_attr,coms[-1]))}'
        return s+'\n'
        
    def list_classes(self,module):
        
        # USE get_connection_names FROM DRIVERS.PY ?
        
        return [name for name, obj in inspect.getmembers(module, inspect.isclass) if obj.__module__ is module.__name__]
    def list_methods(self,I):
        
        ### COPY PASTED IN DRIVERS.PY BUT HAS TO BE CHECKED
        
        methods_list = []
        class_meth = [f'I.{name}' for name,obj in inspect.getmembers(I,inspect.ismethod) if name != '__init__']
        class_vars = [] 
        for key in vars(I).keys():
            try:    # explicit to avoid visa and inspect.getmembers issue
                for name,obj in inspect.getmembers(vars(I)[key],inspect.ismethod):
                    if inspect.getmembers(vars(I)[key],inspect.ismethod) != '__init__' and inspect.getmembers(vars(I)[key],inspect.ismethod) and name!='__init__':
                        class_vars.append(f'I.{key}.{name}')
            except: pass
        #class_vars = [f'I.{key}.{name}' for key in vars(I).keys() for name,obj in inspect.getmembers(vars(I)[key],inspect.ismethod) if inspect.getmembers(vars(I)[key],inspect.ismethod) != '__init__' and inspect.getmembers(vars(I)[key],inspect.ismethod) and name!='__init__']  # issue with visa open instruments
        methods_list.extend(class_meth);methods_list.extend(class_vars)
        return methods_list
    
    def parsekwargs_connectiondependant(self,kwargs,Driver_class):
        
        # USE get_class_args FROM DRIVERS.PY ?
        
        if Driver_class.__name__ == 'Driver_DLL':
            try: 
                if kwargs['port']: kwargs['libpath'] = kwargs['port']; del kwargs['port']
            except: pass
        elif Driver_class.__name__ == 'Driver_GPIB':
            try: 
                if kwargs['port']: kwargs['board_index'] = kwargs['port']; del kwargs['port']
            except: pass
        return kwargs
    
    def identify_device_class(self,module,classes_list,link):
        
        # USER get_connection_class FROM DRIVERS.PY
        
        assert f'Driver_{link}' in classes_list , f"Not in {[a for a in classes_list if a.startswith('Driver_')]}"
        Driver_class = getattr(module,f'Driver_{link}')
        return Driver_class
    
    def get_category(self,driver_module):
        
        # USE get_driver_category FROM DRIVERS.PY
        
        classes_list = self.list_classes(driver_module)
        Driver_class = getattr(driver_module,f'Driver')
        assert Driver_class.category, f"Missing category for driver {driver_module.__name__}"
        return Driver_class.category

    def parse_commands(self,I,commands,methods_list):
        
        
        
        global NAME
        
        for command in commands:
            print()
            print(f'Executing command:  {command}')
            message = None
            com     = command[0]
            assert com in methods_list, f"Method not known or bound. Methods known are: {method_list}"
            coms = com.split('.')
            coms1_attr     = getattr(I,coms[1])
            
            NAME = None
            if len(coms)==2: NAME = partial(coms1_attr)
            else: coms1_attr_attr=getattr(coms1_attr,coms[-1]); NAME = partial(coms1_attr_attr)
            for k in range(len(command[1:])):
                is_there_equal = command[1+k].split('=')
                if len(coms)==2:
                    if len(is_there_equal)==2:
                        if isinstance(is_there_equal[1],str):
                            exec(f'NAME = partial(NAME,{is_there_equal[0]}="{is_there_equal[1]}")',globals())
                        else:
                            exec(f'NAME = partial(NAME,{is_there_equal[0]}={is_there_equal[1]})',globals())
                    else:
                        NAME = partial(NAME,is_there_equal[0])
                else:
                    coms1_attr_attr = getattr(coms1_attr,coms[-1])
                    if len(is_there_equal)==2:
                        if isinstance(is_there_equal[1],str):
                            exec(f'NAME = partial(NAME,{is_there_equal[0]}="{is_there_equal[1]}")',globals())
                        else:
                            exec(f'NAME = partial(NAME,{is_there_equal[0]}={is_there_equal[1]})',globals())
                    else:
                        NAME = partial(NAME,is_there_equal[0])
            message = NAME()
            if message is not None: print('Return:  ',message)
        print()

