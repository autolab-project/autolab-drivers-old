#!/c/Python27/python.exe
# -*- coding: utf-8 -*-
"""


"""
import pvcam_Manis
#import visa
import os

ADDRESS = 'ASRL6::INSTR'     # to implement with the x axis and modify accordingly....

class Driver():
    def __init__(self,camera='Camera1'):
        
        self.minExpTimeAllowed = 2e-5  #s
        self.maxExpTimeAllowed = 10    #s
        self.minCountsAllowed  = 5000
        self.maxCountsAllowed  = 61000
        self.exposure          = 0.01
        self.nb_frames         = 1
        self.data              = None
        self.auto_exposure     = False
        
        ### Initiate necessary libraries ###
        self.pvcam = pvcam_Manis.Init_PVCam()
        
        ### Initiate camera ###
        self.CAM = self.get_camera(camera=camera)


    def command(self,command):
        if command == 'DATA?':
            self.get_data()
            return self.data
        elif command.startswith('EXPTIME='):
            expTime = float(command.split('=')[1])
            self.setExposureTime(expTime)
        elif command.startswith('EXPTIME?'):
            return self.exposure
        elif command.startswith('NBFRAMES='):
            self.nb_frames = int(command.split('=')[1])
            self.setNbFrames(self.nb_frames)
        elif command.startswith('NBFRAMES?'):
            return self.getNbFrames()
        elif command.startswith('CONNECT='):
            camera = command.split('=')[1]
            self.CAM = self.get_camera(camera)
        elif command.startswith('LISTCAMS?'):
            return self.list_cameras()
        elif command.startswith('AUTOEXPEN'):
            return self.set_auto_exposure_enabled()
        elif command.startswith('AUTOEXPDIS'):
            return self.set_auto_exposure_disabled()
        elif command.startswith('SAVEDATA'):
            return self.save_data_local()

    def getExposureTime(self):
        return self.exposure
    
    def setExposureTime(self,value):
        self.exposure = value

    def setNbFrames(self,value):
        self.nb_frames = value

    def getNbFrames(self):
        return self.nb_frames

    def get_data(self):
        data = self.CAM.acq(frames=self.nb_frames, exposure=self.exposure)
        self.data = [list(data[i].squeeze()) for i in xrange(len(data))]
        
        if self.auto_exposure:
            while True :

                # Récupération des données
                maxValue=max(self.data[0])
                
                # Reduction du temps d'exposition
                if maxValue>self.maxCountsAllowed : 
                    exposureTime_save = self.getExposureTime()
                    self.setExposureTime(self.getExposureTime()/10)
                    if self.getExposureTime() == exposureTime_save :
                        break
                # Augmentation du temps d'exposition
                elif maxValue<self.minCountsAllowed : 
                    exposureTime_save = self.getExposureTime()
                    self.setExposureTime(self.getExposureTime()*self.maxCountsAllowed/maxValue*0.9)
                    if self.getExposureTime() == exposureTime_save :
                        break
                else :
                    break
                
                # Mesure spectre
                data = self.CAM.acq(frames=self.nb_frames, exposure=self.exposure)
                self.data = [list(data[i].squeeze()) for i in xrange(len(data))]
    
    
    def get_camera(self,camera='Camera1'):
        ### Initiate communication with the requested camera ###
        print('Trying to get: %s' %camera)
        CAM = self.pvcam.PVCam.getCamera(camera)
        print('Got: %s' %camera)
        return CAM

    def save_data_local(self,filename,FORCE=False):
        data = eval(self.data.deepcopy())
        temp_filename = f'{filename}_SPECTRO32{self.camera}.txt'
        if os.path.exists(os.path.join(os.getcwd(),temp_filename)) and not(FORCE):
            print('\nFile ', temp_filename, ' already exists, change filename or remove old file\n')
            return
        
        self.lambd=[list(range(len(data[0])))]
        assert self.lambd, 'You may want to get_data before saving ...'
        [self.lambd.append(data[i]) for i in xrange(len(data))]
        f = savetxt(temp_filename,self.lambd)  ## squeeze
        print(camera + ' saved')
    
    def list_cameras(self):
        return self.pvcam.listCameras()
    
    def set_auto_exposure_enabled(self):
        self.auto_exposure = True
    def set_auto_exposure_disabled(self):
        self.auto_exposure = False

