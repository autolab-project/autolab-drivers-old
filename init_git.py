# -*- coding: utf-8 -*-

import os
import shutil

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
    drivers_dir_list_to_copy = [name for name in os.listdir(path_to_drivers) if name not in ['init_git.py','__init__.py','.git','__pycache__']]
    for driver_dir in drivers_dir_list_to_copy:
        # Create path to driver to copy
        driver_path_to_copy = os.path.join(path_to_drivers,driver_dir)
        
        # Create a directory appropriate directory structure using the driver name
        new_driver_dir = os.path.join(path_to_new_git,driver_dir)
        os.mkdir(new_driver_dir)
        
        # Copy driver directory to git
        new_sub_driver_dir = os.path.join(new_driver_dir,'v1.0.0')
        shutil.copytree(driver_path_to_copy,new_sub_driver_dir)
