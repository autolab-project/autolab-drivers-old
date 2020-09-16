# -*- coding: utf-8 -*-

import os
import shutil
import configparser
from datetime import date

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
            os.mkdir(new_driver_dir)  # create dir only if v1.0.0 has to be created
            new_sub_driver_dir = os.path.join(new_driver_dir,'v1.0.0')
        
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
