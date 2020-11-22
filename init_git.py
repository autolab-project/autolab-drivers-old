# -*- coding: utf-8 -*-

import os,sys
import shutil
import configparser
from datetime import date
import importlib
import inspect
import re
import subprocess


def import_drivers_from_autolab_git(path_to_drivers,path_to_new_git):
    
    ''' Function made for initial commit of autolab drivers into autolab-driver git. Remove all drivers in the target path_to_new_git directory then copy drivers from path_to_drivers directory with appropriate structure '''
    
    assert 'autolab' in path_to_drivers, f"Check you input paths. Provided was: {path_to_drivers}"
    assert 'autolab-drivers' in path_to_new_git, f"Check you input paths. Provided was: {path_to_new_git}"
    
    # Remove all previous drivers into path_to_new_git
    drivers_dir_list_to_remove = [name for name in os.listdir(path_to_new_git) if name not in ['init_git.py','__init__.py','.git','__pycache__']]
    for driver_dir in drivers_dir_list_to_remove:
        driver_path_to_remove = os.path.join(path_to_new_git,driver_dir)
        shutil.rmtree(driver_path_to_remove)
    
    # Copying all drivers from autolab into path_to_new_git with new structure (driver_MODEL/v1.0.0/driver_MODEL.py)
    dir_list_to_copy = [name for name in os.listdir(path_to_drivers) if name not in ['init_git.py','__init__.py','.git','__pycache__']]
    for driver_dir in dir_list_to_copy:
        # Create path to driver to copy
        driver_path_to_copy = os.path.join(path_to_drivers,driver_dir)
        
        # Create an appropriate directory structure using the driver name
        new_driver_dir = os.path.join(path_to_new_git,driver_dir)
        # Do we need versionning for the directory?
        list_dir_without_versioning = ['More']
        if driver_dir in list_dir_without_versioning:
            new_sub_driver_dir = new_driver_dir
        else:
            os.mkdir(new_driver_dir)  # create dir only if 1.0.0 has to be created
            new_sub_driver_dir = os.path.join(new_driver_dir,'1.0.0')
        
        # Copy driver directory to git
        shutil.copytree(driver_path_to_copy,new_sub_driver_dir)
        
        # Write release_notes.ini
        if driver_dir not in list_dir_without_versioning:
            config = configparser.ConfigParser()
            config.add_section('release_notes')
            config['release_notes']['version'] = '1.0.0'
            config['release_notes']['date']    = date.today().strftime("%d/%m/%Y")
            config['release_notes']['notes']   = "First push from autolab's previous version"
            
            path_release_notes = os.path.join(new_sub_driver_dir,'release_notes.ini')
            with open(path_release_notes, 'w') as configfile:    # save
                config.write(configfile)


def convert_version_folder_name(path_to_folder,target_name='1.0.0'):
    assert 'autolab-drivers' in path_to_folder, f"Check you input paths. Provided was: {path_to_new_git}"
    
    for folder_name in [name for name in os.listdir(path_to_folder) if os.path.isdir(name)]:
        inner_path = os.path.join(path_to_folder,folder_name)
        if 'v1.0.0' in os.listdir(inner_path):
            os.rename(os.path.join(folder_name,'v1.0.0'),os.path.join(folder_name,target_name))
            


def convert_getdrivermodel_to_autolabini():
    
    lib_path = 'driver'
    
    # Get all the class defined whitin a module but Driver_CONN
    module = importlib.import_module(lib_path)
    module = importlib.reload(module) # If has already been imported takes the local version of driver.py instead
    module_classes = [name for name, obj in inspect.getmembers(module,inspect.isclass) if obj.__module__ is lib_path.split('.')[-1] if 'Driver_' not in name]
    
    print(f'Classes here: {module_classes}',module)
    
    # Open module as a text file to get the get_driver_model without instanciating
    f = open(f'{lib_path}.py','r')
    module_text = f.read()
    f.close()
    
    classes_str = module_text.split('class ')
    flag                = 0
    getdrivermodel_list = []
    for classe_str in classes_str:
        for module_classe in module_classes:
            if classe_str.startswith(module_classe) and classe_str.find('def get_driver_model')!=-1:
                getdrivermodel_list.append([])
                getdrivermodel_list[flag].append(module_classe)
                
                getdrivermodel_text_list = classe_str[classe_str.find('def get_driver_model'):classe_str.find('return model')].splitlines()
                
                # get_driver_model line by line
                lines = []
                for line in getdrivermodel_text_list:
                    if '.append' in line:
                        line2 = line.strip(' ')
                        # After the : there might be things in () otherwise finishes with , or a )
                        line2 = re.findall("[\'\"](.+?)[\'\"]\s*:\s*(.+?(?:\(.*?\))?)(?:,|}\s*\)\s*$)",line2)
                        
                        elements = {}
                        for index,element in enumerate(line2):
                            assert len(element) == 2
                            elements[element[0].strip('\'').strip('\"')] = element[1].strip('\'').strip('\"')
                        lines.append(elements)
                        
                getdrivermodel_list[flag].append(lines)
                flag += 1
    
    #return getdrivermodel_list
    #['Driver',
    #[{'element': 'module',
    #'help': 'Channels',
    #'name': "f'channel{i}",
    #'object': "getattr(self,f'channel{i}')"}]
    #
    #f[0][0] = 'Driver'
    #f[0][1][0] = {'element':'module','help':'Channels','name':"f'channel{i}",'object':"getattr(self,f'channel{i}')"}
    #f[0][1][0]['element'] = 'module'
    
    # Add to configparser sections
    config = configparser.ConfigParser()
    
    for classe_index in range(len(getdrivermodel_list)):
        print(getdrivermodel_list[classe_index][0])
        classe_name = getdrivermodel_list[classe_index][0]
        for element_index in range(len(getdrivermodel_list[classe_index][1])):
            if getdrivermodel_list[classe_index][1][element_index]['element'] == 'module':
                print('ici')
                continue
            ## If Driver => [variable]
            if classe_name == 'Driver':
                name = getdrivermodel_list[classe_index][1][element_index]['name']
            ## If Module_XXX => [Module_XXX.variable]
            else:
                name = classe_name + '.' + getdrivermodel_list[classe_index][1][element_index]['name']
            config.add_section(name)
            for key in getdrivermodel_list[classe_index][1][element_index].keys():
                if key != 'name':
                    # If 'type' is 'ndarray' modify it to array
                    if key == 'type':
                        if getdrivermodel_list[classe_index][1][element_index][key] == 'ndarray':
                            getdrivermodel_list[classe_index][1][element_index][key] = 'array'
                    # remove self. at start of element if present
                    config[name][key] = re.sub('^self.','',getdrivermodel_list[classe_index][1][element_index][key]) 
    
    
    # Add the section for additional modules (e.g. Channel)
    list_utilities_files = subprocess.getoutput('ls *utilities.py').splitlines()
    assert len(list_utilities_files) == 1, f"Found {len(list_utilities_files)} utilities file"
    lib_utilities_path = list_utilities_files[0]
    
    ff = open(lib_utilities_path,'r')
    module_utilities_text = ff.read()
    ff.close()
    
    lines_category_found = [line for line in module_utilities_text.splitlines() if 'category' in line]
    assert len(lines_category_found) == 1, f"Found {len(lines_category_found)} mention of category in the file"
    print(lines_category_found[0])
    category_name = lines_category_found[0].split('=')[1].replace("'","").strip(' ')
    
    print(module_classes)
    for module_classe in module_classes:
        if module_classe != 'Driver':
            print(module_classe)
            config.add_section(module_classe)
            config[module_classe]['element'] = 'module'
            config[module_classe]['category'] = category_name
    
    # Write to autolab.ini file
    with open('autolab.ini', 'w') as configfile:    # save
        config.write(configfile)
    
    # Remove the module re-import from scratch it at next occurence of this function
    del module
    sys.modules.pop(lib_path)

def all_getdrivermodel_to_autolabini():
    
    list_driver_folders = [dire for dire in os.listdir() if '.' not in dire if '__'not in dire if dire!='More']
    
    auto_driv_root_path = os.getcwd()
    for driver_folder in list_driver_folders:
        os.chdir(os.path.join(driver_folder,'1.0.0'))
        print('before:',os.getcwd())
        convert_getdrivermodel_to_autolabini()
        os.chdir(auto_driv_root_path)











