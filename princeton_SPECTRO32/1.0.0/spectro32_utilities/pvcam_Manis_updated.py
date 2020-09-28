from ctypes import *
import re, sys, numpy, time, types

## System-specific code
pvcam_header_files = ["C:\Program Files\Princeton Instruments\PVCAM\SDK\master.h", "C:\Program Files\Princeton Instruments\PVCAM\SDK\pvcam.h"]


PVCAM_CREATED = False

class _CameraClass:
    def __init__(self, name, pvcam):
        self.name = name.encode('utf-8')
        self.pvcam = pvcam
        self.isOpen = False
        self.open()
        self.initCam()
        self.exposure = 0.0001
        self.clearROI()
        self.binning = [1, 1]
        self.mode = 0
        self.frameSize = 1
        self.ringSize = 10
        self.buf = None


    def __del__(self):
        self.close()

    def open(self):
        self.hCam = c_ushort()
        self.pvcam.pl_cam_open(c_char_p(self.name), byref(self.hCam), OPEN_EXCLUSIVE)
        self.isOpen = True

    def initCam(self):
        ## This stuff should be moved out to separate functions..
        ##   - PARAM_BIT_DEPTH, PARAM_PIX_TIME, and PARAM_GAIN_INDEX(ATTR_MAX)
        ##     are determined by setting PARAM_READOUT_PORT and PARAM_SPDTAB_INDEX 
        ##   - PARAM_GAIN_INDEX must be set AFTER setting PARAM_SPDTAB_INDEX
        #self.setParam(PARAM_READOUT_PORT, 1)  ## Only option for Q57
        #self.setParam(PARAM_SPDTAB_INDEX, 2)  ## Fastest option for Q57
        #self.setParam(PARAM_GAIN_INDEX, 3)
        #self.setParam(PARAM_PMODE, PMODE_NORMAL)  ## PMODE_FT ?
        self.setParam(PARAM_SHTR_OPEN_MODE, OPEN_PRE_SEQUENCE)
		#self.setParam(PARAM_EXP_RES, EXP_RES_ONE_MILLISEC)  (bruno)
        #self.setParam(PARAM_CLEAR_MODE, CLEAR_PRE_EXPOSURE)
        self.setParam(PARAM_CLEAR_CYCLES, 2)
        pass

		
    def getTemperature(self):
        # Doesn't work for whatever reason 
        self.paramAvailable(PARAM_TEMP_SETPOINT)       # works
        self._assertParamReadable(PARAM_TEMP_SETPOINT) # works
        self.getParam(PARAM_TEMP_SETPOINT)             # ...

    def getExposure(self):
        return self.getParam(PARAM_EXP_RES)             # ...

    def listTransferModes(self):
        return self.getEnumList(PARAM_PMODE)[0]
        
    def setTransferMode(self, mode):
        self.setEnum(PARAM_PMODE, mode)

    def getTransferMode(self):
        return self.getEnum(PARAM_PMODE)
        
    def listShutterModes(self):
        return self.getEnumList(PARAM_SHTR_OPEN_MODE)[0]
        
    def setShutterMode(self, mode):
        self.setEnum(PARAM_SHTR_OPEN_MODE, mode)

    def getShutterMode(self):
        return self.getEnum(PARAM_SHTR_OPEN_MODE)

    def getEnum(self, param):
        l = self.getEnumList(param)
        v = self.getParam(param)
        return l[1].index(v)
        
    def setEnum(self, param, val):
        l = self.getEnumList(param)
        if val >= len(l[0]):
            raise Exception("Invalid value for %s" % self.paramName(param))
        self.setParam(param, l[1][val])
        

    def close(self):
        if self.isOpen:
            #self.pvcam.pl_exp_abort(CCS_HALT_CLOSE_SHUTTER)
            self.pvcam.pl_cam_close(self.hCam)
            self.isOpen = False

    def getSize(self):
        return (self.getParam(PARAM_SER_SIZE), self.getParam(PARAM_PAR_SIZE))
      
    def getBitDepth(self):
        return self.getParam(PARAM_BIT_DEPTH)

    def setExposure(self, exp):
        self.exposure = exp

    def setBinning(self, sbin, pbin=None):
        if pbin is None:
            pbin = sbin
        self.binning = [sbin, pbin]

    def setROI(self, s1, p1, s2, p2):
        self.region = [s1, p1, s2, p2]

    def clearROI(self):
        size = self.getSize()
        self.region = [0, 0, size[0]-1, size[1]-1]

    def setRingSize(self, s):
        self.ringSize = s

    def getRegion(self, region=None, binning=None):
        if region is None: region = self.region
        if binning is None: binning = self.binning
        return Region(region, binning)

    def acq(self, frames=None, exposure=None, region=None, binning=None):
		# (bruno) may be missing a cleanup => pl_exp_finish_seq(self.hCam, self.buf.ctypes.data, int16 hbuf) (page 72)
		
        if self.mode != 0:
            raise Exception("Camera is not ready to start new acquisition")
        if exposure is None: exposure = self.exposure
        exp = self._parseExposure(exposure)
        
        ## Convert exposure to indexed value
        
        ssize = c_uint()
        rgn = self.getRegion(region, binning)
        print(rgn.size())
        if frames is None:
            self.buf = numpy.empty((rgn.size()[1], rgn.size()[0]), dtype=numpy.uint16)
            frames = 1
        else:
            self.buf = numpy.empty((frames, rgn.size()[1], rgn.size()[0]), dtype=numpy.uint16)

        self.pvcam.pl_exp_setup_seq(self.hCam, c_ushort(frames), c_ushort(1), byref(rgn), TIMED_MODE, c_uint(exp), byref(ssize))
#        if len(self.buf.data) != ssize.value:
#            raise Exception('Created wrong size buffer! %d != %d' %(len(self.buf.data), ssize.value))
        self.pvcam.pl_exp_start_seq(self.hCam, self.buf.ctypes.data)   ## Warning: this memory is not locked, may cause errors if the system starts swapping.
        self.mode = 1
        while True:
            status = c_short()
            bcount = c_uint()
            self.pvcam.pl_exp_check_status(self.hCam, byref(status), byref(bcount))
            if status.value in [READOUT_COMPLETE, READOUT_NOT_ACTIVE]:
                break
            elif status.value == READOUT_FAILED:
                pass
				# Note once out of two times the READOUT fails
                #raise Exception("Readout failed: " + self.pvcam.error())
            time.sleep(exposure * 0.5)
        # pl_exp_finish_seq to add?
        self.mode = 0
        return self.buf

    def _parseExposure(self, exp):
        ## This function should make use of PARAM_EXP_RES, but it doesn't seem to work on Q57!
        #minexp = self.getParam(PARAM_MIN_EXP_TIME)
        #if exp < minexp:
        #    raise Exception("Exposure time is less than effective minimum (%f < %f)" % (exp, minexp))
        return int(exp * 1000.)

    def start(self, frames=None, exposure=None, region=None, binning=None):
        # (bruno) WARNING: memory is not locked...
        if self.mode != 0:
            raise Exception("Camera is not ready to start new acquisition")
        assert(frames > 0)

        self._assertParamAvailable(PARAM_CIRC_BUFFER)
        if exposure is None: exposure = self.exposure
        if region is None: region = self.region
        if binning is None: binning = self.binning
        if frames is None: frames = self.ringSize

        exp = self._parseExposure(exposure)

        ssize = c_uint()
        rgn = Region(region, binning)
        rSize = rgn.size()
        self.frameSize = rSize[0] * rSize[1] * 2
        self.buf = numpy.empty((frames, rgn.size()[1], rgn.size()[0]), dtype=numpy.uint16)
        self.pvcam.pl_exp_setup_cont(self.hCam, c_ushort(1), byref(rgn), TIMED_MODE, c_uint(exp), byref(ssize), CIRC_OVERWRITE)
        ssize = c_ulong(ssize.value*frames)
        if len(self.buf.data) != ssize.value:
            raise Exception('Created wrong size buffer! %d != %d' %(len(self.buf.data), ssize.value))
        self.pvcam.pl_exp_start_cont(self.hCam, self.buf.ctypes.data, ssize)   ## Warning: this memory is not locked, may cause errors if the system starts swapping.
        self.mode = 2
        
        print(self.buf.squeeze(),type(self.buf.squeeze()[0]))
		## added (bruno): make sure readout is finished before returning
        while True:
            status = c_short()
            bcount = c_uint()
            self.pvcam.pl_exp_check_status(self.hCam, byref(status), byref(bcount))
            if status.value in [READOUT_COMPLETE, READOUT_NOT_ACTIVE]:
                break
            elif status.value == READOUT_FAILED:
                pass
				# Note once out of two times the READOUT fails
                #raise Exception("Readout failed: " + self.pvcam.error())
            time.sleep(exposure*0.5)
			
        return self.buf

    def lastFrame(self):
        assert(self.buf is not None)
        frame = c_void_p()
        try:
            self.pvcam.pl_exp_get_latest_frame(self.hCam, byref(frame))
        except:
            if sys.exc_info()[1][1] == 3029:  ## No frame is ready yet (?)
                return None
            else:
                raise
        index = (frame.value - self.buf.ctypes.data) / self.frameSize
        if index < 0 or index > (self.buf.shape[0]-1):
            print("Warning: lastFrame got %d!" % index)
            return None
        return index

    def stop(self):
        if self.mode == 1:
            self.pvcam.pl_exp_abort(self.hCam, CCS_CLEAR_CLOSE_SHTR)
        elif self.mode == 2:
            self.pvcam.pl_exp_stop_cont(self.hCam, CCS_CLEAR_CLOSE_SHTR)
        self.mode = 0

    def getParam(self, param):
        ## Make sure parameter exists on this hardware and is writable
        self._assertParamReadable(param)
        return self._getParam(param, ATTR_CURRENT)
        
    def setParam(self, param, value, autoClip=False, autoQuantize=False, checkValue=True):
        ## Make sure parameter exists on this hardware and is writable
        self._assertParamWritable(param)

        ## Determine the parameter type
        typ = self.getParamType(param)
        ## Make sure value is in range
        if checkValue and typ in [TYPE_INT8, TYPE_UNS8, TYPE_INT16, TYPE_UNS16, TYPE_INT32, TYPE_UNS32, TYPE_FLT64]:
            (minval, maxval, stepval) = self.getParamRange(param)
            if value < minval:
                if autoClip:
                    value = minval
                    print("Warning: Clipped value to %s" % str(value))
                else:
                    raise Exception("Minimum value for parameter is %s (requested %s)" % (str(minval), str(value)))
            if value > maxval:
                if autoClip:
                    value = maxval
                    print("Warning: Clipped value to %s" % str(value))
                else:
                    raise Exception("Maximum value for parameter is %s (requested %s)" % (str(maxval), str(value)))
            if stepval != 0.0:   ## No idea what to do if stepval == 0
                inc = (value - minval) / stepval
                if (inc%1.0) != 0.0:
                    if autoQuantize:
                        value = minval + round(inc) * stepval
                        print("Warning: Quantized value to %s" % str(value))
                    else:
                        raise Exception("Value for parameter must be in increments of %s (requested %s)" % (str(stepval), str(value)))
        #elif typ == TYPE_ENUM:
        #    count = self._getParam(param, ATTR_COUNT)
        #    if value > (count-1):
        #        raise Exception("Enum value %d is out of range for parameter" % value)
        elif typ == TYPE_CHAR_PTR:
            count = self._getParam(param, ATTR_COUNT)
            if len(value) > count:
                raise Exception("Enum value %d is out of range for parameter" % value)
            
        ## Set value
        val = self.mkCObj(typ, value)
        self.pvcam.pl_set_param(self.hCam, param, byref(val))

    def getParamRange(self, param):
        self._assertParamAvailable(param)
        typ = self.getParamType(param)

        minval = self._getParam(param, ATTR_MIN)
        maxval = self._getParam(param, ATTR_MAX)
        stepval = self._getParam(param, ATTR_INCREMENT)

        return (minval, maxval, stepval)

    def getParamType(self, param):
        self._assertParamAvailable(param)
        return self._getParam(param, ATTR_TYPE)

    def getEnumList(self, param):
        self._assertParamAvailable(param)
        if self.getParamType(param) != TYPE_ENUM:
          raise Exception('Parameter is not enum type.')
        num = self._getParam(param, ATTR_COUNT)
        names = []
        vals = []
        for i in range(0, num):
          ind = c_int(i)
          slen = c_int()
          self.pvcam.pl_enum_str_length(self.hCam, param, ind, byref(slen))
          strn = create_string_buffer('\0' * (slen.value+1))
          val = c_int()
          self.pvcam.pl_get_enum_param(self.hCam, param, ind, byref(val), byref(strn), slen)
          names.append(strn.value)
          vals.append(val.value)
        return [names, vals]

    def _assertCameraOpen(self):
        if not self.isOpen:
            raise Exception("Camera is not open.")
    
    def paramAvailable(self, param):
        self._assertCameraOpen()
        return self._getParam(param, ATTR_AVAIL) > 0
    
    def _assertParamAvailable(self, param):
        if not self.paramAvailable(param):
            raise Exception("Parameter is not available.")
        
    def _assertParamWritable(self, param):
        self._assertParamAvailable(param)
        access = self._getParam(param, ATTR_ACCESS)
        if access in [ACC_EXIST_CHECK_ONLY, ACC_READ_ONLY]:
            raise Exception("Parameter is not writable.")
        elif access not in [ACC_WRITE_ONLY, ACC_READ_WRITE]:
            raise Exception("Unknown access check value!")

    def _assertParamReadable(self, param):
        self._assertParamAvailable(param)
        access = self._getParam(param, ATTR_ACCESS)
        if access in [ACC_EXIST_CHECK_ONLY, ACC_WRITE_ONLY]:
            raise Exception("Parameter is not readable.")
        elif access not in [ACC_READ_WRITE, ACC_READ_ONLY]:
            raise Exception("Unknown access check value!")
    
    def _getParam(self, param, attr, typ=None):
        """Gets parameter/attribute combination. Automatically handles type conversion."""
        if typ is None:
            typs = {
                ATTR_ACCESS: TYPE_UNS16,
                ATTR_AVAIL: TYPE_BOOLEAN,
                ATTR_COUNT: TYPE_UNS32,
                ATTR_TYPE: TYPE_UNS16
            }
            if attr in typs.keys():
                typ = typs[attr]
            else:
                typ = self.getParamType(param)
                
        val = self.mkCObj(typ)
        self.pvcam.pl_get_param(self.hCam, param, attr, byref(val))
        return val.value
		
    def mkCObj(self, typ, value=None):
        typs = {
            TYPE_INT8: c_byte, 
            TYPE_UNS8: c_ubyte,
            TYPE_INT16: c_short,
            TYPE_UNS16: c_ushort,
            TYPE_INT32: c_int,
            TYPE_UNS32: c_uint,
            TYPE_FLT64: c_double,
            TYPE_ENUM: c_ushort,
            TYPE_BOOLEAN: c_ushort,
            TYPE_CHAR_PTR: c_char_p, ## This is likely to cause bugs--we need to use create_string_buffer
            TYPE_VOID_PTR: c_void_p,
            TYPE_VOID_PTR_PTR: c_void_p
        }
        if not typ in typs.keys() :
            raise Exception("Unknown type %d" % typ)
        if value is None:
            return typs[typ]()
        else:
            return typs[typ](value)

    def paramName(self, param):
        for p in dir(__main__):
            if p[:6] == 'PARAM_' and getattr(__main__, p) == param:
                return p

    def attrName(self, attr):
        for p in dir(__main__):
            if p[:5] == 'ATTR_' and getattr(__main__, p) == attr:
                return p

    def typeName(self, typ):
        for p in dir(__main__):
            if p[:5] == 'TYPE_' and getattr(__main__, p) == typ:
                return p
    
class _PVCamClass:
    def __init__(self):
        self.pvcam = windll.Pvcam32
        global PVCAM_CREATED
        if PVCAM_CREATED:
            raise Exception("Will not create another pvcam instance--use the pre-existing PVCam object.")
        self.cams = {}
        if self.pvcam.pl_pvcam_init() < 1:
            raise Exception("Could not initialize pvcam library (pl_pvcam_init): %s" % self.error())
#        if self.pvcam.pl_exp_init_seq() < 1:
#            raise Exception("Could not initialize pvcam library (pl_exp_init_seq): %s" % self.error())
        PVCAM_CREATED = True

    def listCameras(self):
        nCam = c_int()
        cams = []
        if self.pvcam.pl_cam_get_total(byref(nCam)) < 1:
            raise Exception("Error getting number of cameras: %s" % self.error())
        for i in range(0, nCam.value):
            cName = create_string_buffer('\0' * CAM_NAME_LEN)
            if self.pvcam.pl_cam_get_name(c_short(i), byref(cName)) < 1:
                raise Exception("Error getting name for camera %d: %s" % (i, self.error()))
            cams.append(cName.value)
        return cams

    def getCamera(self, cam):
        if not cam in self.cams.keys() :
            self.cams[cam] = _CameraClass(cam, self)
        return self.cams[cam]
    
    def __getattr__(self, attr):
        if hasattr(self.pvcam, attr):
            return lambda *args: self.call(attr, *args)
        else:
            raise NameError

    def call(self, func, *args):
        try:
            #print("%s(%s)" % (func, str(args)))
            fn = getattr(self.pvcam, func)
        except:
            raise Exception("No PVCam function named " + func)
        a = fn(*args)
#        if a < 1:
#            raise Exception("Function '%s%s' failed: %s" % (func, str(args), self.error()), self.pvcam.pl_error_code())

    def error(self):
        err = create_string_buffer('\0'.encode('utf-8')*ERROR_MSG_LEN)
        erc = self.pvcam.pl_error_code()
        self.pvcam.pl_error_message(erc, byref(err))
        return "%d: %s" % (erc, err.value)

    def __del__(self):
        for c in self.cams:
            try:
                self.cams[c].close()
            except:
                pass
        self.pvcam.pl_exp_uninit_seq()
        self.pvcam.pl_pvcam_uninit()
        PVCAM_CREATED = False

class Region(Structure):
    _fields_ = [
        ('s1', c_ushort),
        ('s2', c_ushort),
        ('sbin', c_ushort),
        ('p1', c_ushort),
        ('p2', c_ushort),
        ('pbin', c_ushort)
    ]
    
    def __init__(self, *args):
        if len(args) == 6:
            Structure.__init__(self, *args)
        else:
            rgn = args[0][:]
            if type(args[1]) == int:
                bin = [args[1], args[1]]
            else:
                bin = args[1][:]
            assert( hasattr(rgn, '__len__') and len(rgn) == 4 )
            assert( hasattr(bin, '__len__') and len(bin) == 2 )
            rgn[2] = rgn[0] + (int((rgn[2]-rgn[0])/bin[0]) * bin[0])
            rgn[3] = rgn[1] + (int((rgn[3]-rgn[1])/bin[1]) * bin[1])
            Structure.__init__(self, rgn[0], rgn[2], bin[0], rgn[1], rgn[3], bin[1])
            
    def size(self):
        return (int((self.s2-self.s1+1) / self.sbin), int((self.p2-self.p1+1) / self.pbin))








class Init_PVCam():
	def __init__(self):
		self.createConstants()
		self.PVCam = _PVCamClass()

	def decomment(self, string):
		return re.sub(r'/\*.*\*/', '', re.sub(r'//.*', '', string))

	def createConstants(self):
		global pvcam_header_files
		names = []
		for hfile in pvcam_header_files:
			fh = open(hfile)
			data = fh.readlines()
			fh.close()
			global header_vars
			header_vars = []
			
			for i in range(0, len(data)):
				l = self.decomment(data[i])
				
				# Search for #define, set variable
				m = re.match(r'\s*\#define\s+(\S+)\s+(.*)', l)
				if m is not None:
					var = m.groups()[0]
					expr = m.groups()[1]
					if len(var) > 0 and len(expr) > 0:
						
						try:
							setattr(sys.modules[__name__], var, eval(expr))
							names.append(var)
							header_vars.append(var)
							print(var,eval(expr))
						except:
							pass
							#print("Error setting variable '%s' = '%s'" % (var, expr))

				# search for enum
				if re.match(r'\s*enum\s+', l):
					# concatenate lines until the end of the enum
					ind = i
					enum = ''
					while True:
						enum += self.decomment(data[ind])
						if re.search('}', data[ind]):
							break
						ind += 1

					# Pull out variables
					enum = re.sub('(\n|\s)', '', enum)
					enum = re.sub(r'.*{', '', enum)
					enum = re.sub(r'}.*', '', enum)
					ind = 0
					for var in enum.split(','):
						setattr(sys.modules[__name__], var, ind)
						names.append(var)
						ind += 1

		vals = {}
		for n in names:
			vals[n] = getattr(sys.modules[__name__], n)
		return vals


#init()
#PVCam.listCameras()
#c = PVCam.getCamera('Camera1')
#d=c.start(1)
#numpy.savetxt('test_winspec.txt',d.squeeze())
