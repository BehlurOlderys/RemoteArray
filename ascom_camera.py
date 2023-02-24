from .ascom_device import AscomDevice
from abc import abstractmethod
from enum import IntEnum


class CameraState(IntEnum):
    IDLE = 0
    WAITING = 1
    EXPOSING = 2
    READING = 3
    DOWNLOAD = 4
    ERROR = 5


class AscomCamera(AscomDevice):
    @abstractmethod
    def get_bayeroffsetx(self):
        """
        Returns the X offset of the Bayer matrix.
        """
        pass

    @abstractmethod
    def get_bayeroffsety(self):
        """
        Returns the Y offset of the Bayer matrix.
        """
        pass

    @abstractmethod
    def get_binx(self):
        """
        Returns the binning factor for the X axis.
        """
        pass

    @abstractmethod
    def get_biny(self):
        """
        Returns the binning factor for the Y axis.
        """
        pass

    @abstractmethod
    def get_camerastate(self):
        """
        Returns the camera operational state.
        Returns the current camera operational state as an integer.
        0 = CameraIdle ,
        1 = CameraWaiting ,
        2 = CameraExposing ,
        3 = CameraReading ,
        4 = CameraDownload ,
        5 = CameraError
        """
        pass

    @abstractmethod
    def get_cameraxsize(self):
        """
        Returns the width of the CCD camera chip.
        """
        pass

    @abstractmethod
    def get_cameraysize(self):
        """
        Returns the height of the CCD camera chip.
        """
        pass

    @abstractmethod
    def get_canabortexposure(self):
        """
        Indicates whether the camera can abort exposures.
        """
        pass

    @abstractmethod
    def get_canasymmetricbin(self):
        """
        Indicates whether the camera supports asymmetric binning
        """
        pass

    @abstractmethod
    def get_canfastreadout(self):
        """
        Indicates whether the camera has a fast readout mode.
        """
        pass

    @abstractmethod
    def get_cangetcoolerpower(self):
        """
        Indicates whether the camera's cooler power setting can be read.
        """
        pass

    @abstractmethod
    def get_canpulseguide(self):
        """
        Returns a flag indicating whether this camera supports pulse guiding
        """
        pass

    @abstractmethod
    def get_cansetccdtemperature(self):
        """
        Returns a flag indicating whether this camera supports setting the CCD temperature
        """
        pass

    @abstractmethod
    def get_canstopexposure(self):
        """
        Returns a flag indicating whether this camera can stop an exposure that is in progress
        """
        pass

    @abstractmethod
    def get_ccdtemperature(self):
        """
        Returns the current CCD temperature
        """
        pass

    @abstractmethod
    def get_cooleron(self):
        """
        Returns the current cooler on/off state.
        """
        pass

    @abstractmethod
    def get_coolerpower(self):
        """
        Returns the present cooler power level
        """
        pass

    @abstractmethod
    def get_electronsperadu(self):
        """
        Returns the gain of the camera
        """
        pass

    @abstractmethod
    def get_exposuremax(self):
        """
        Returns the maximum exposure time supported by StartExposure.
        """
        pass

    @abstractmethod
    def get_exposuremin(self):
        """
        Returns the Minimium exposure time
        """
        pass

    @abstractmethod
    def get_exposureresolution(self):
        """
        Returns the smallest increment in exposure time supported by StartExposure.
        """
        pass

    @abstractmethod
    def get_fastreadout(self):
        """
        Returns whenther Fast Readout Mode is enabled.
        """
        pass

    @abstractmethod
    def get_fullwellcapacity(self):
        """
        Reports the full well capacity of the camera
        """
        pass

    @abstractmethod
    def get_gain(self):
        """
        Returns the camera's gain
        """
        pass

    @abstractmethod
    def get_gainmax(self):
        """
        Maximum Gain value of that this camera supports
        """
        pass

    @abstractmethod
    def get_gainmin(self):
        """
        Minimum Gain value of that this camera supports
        """
        pass

    @abstractmethod
    def get_gains(self):
        """
        List of Gain names supported by the camera
        """
        pass

    @abstractmethod
    def get_hasshutter(self):
        """
        Indicates whether the camera has a mechanical shutter
        """
        pass

    @abstractmethod
    def get_heatsinktemperature(self):
        """
        Returns the current heat sink temperature.
        """
        pass

    @abstractmethod
    def get_imagearray(self):
        """
        Returns an array of integers containing the exposure pixel values
        """
        pass

    @abstractmethod
    def get_imagearrayvariant(self):
        """
        Returns an array of int containing the exposure pixel values
        """
        pass

    @abstractmethod
    def get_imageready(self):
        """
        Indicates that an image is ready to be downloaded
        """
        pass

    @abstractmethod
    def get_ispulseguiding(self):
        """
        Indicates that the camera is pulse guideing.
        """
        pass

    @abstractmethod
    def get_lastexposureduration(self):
        """
        Duration of the last exposure
        """
        pass

    @abstractmethod
    def get_lastexposurestarttime(self):
        """
        Start time of the last exposure in FITS standard format.
        """
        pass

    @abstractmethod
    def get_maxadu(self):
        """
        Camera's maximum ADU value
        """
        pass

    @abstractmethod
    def get_maxbinx(self):
        """
        Maximum binning for the camera X axis
        """
        pass

    @abstractmethod
    def get_maxbiny(self):
        """
        Maximum binning for the camera Y axis
        """
        pass

    @abstractmethod
    def get_numx(self):
        """
        Returns the current subframe width
        """
        pass

    @abstractmethod
    def get_numy(self):
        """
        Returns the current subframe height
        """
        pass

    @abstractmethod
    def get_offset(self):
        """
        Returns the camera's offset
        """
        pass

    @abstractmethod
    def get_offsetmax(self):
        """
        Maximum offset value of that this camera supports
        """
        pass

    @abstractmethod
    def get_offsetmin(self):
        """
        Minimum offset value of that this camera supports
        """
        pass

    @abstractmethod
    def get_offsets(self):
        """
        List of offset names supported by the camera
        """
        pass

    @abstractmethod
    def get_percentcompleted(self):
        """
        Indicates percentage completeness of the current operation
        """
        pass

    @abstractmethod
    def get_pixelsizex(self):
        """
        Width of CCD chip pixels (microns)
        """
        pass

    @abstractmethod
    def get_pixelsizey(self):
        """
        Height of CCD chip pixels (microns)
        """
        pass

    @abstractmethod
    def get_readoutmode(self):
        """
        Indicates the canera's readout mode as an index into the array ReadoutModes
        """
        pass

    @abstractmethod
    def get_readoutmodes(self):
        """
        List of available readout modes
        """
        pass

    @abstractmethod
    def get_sensorname(self):
        """
        Sensor name
        """
        pass

    @abstractmethod
    def get_sensortype(self):
        """
        Type of information returned by the the camera sensor (monochrome or colour)
        """
        pass

    @abstractmethod
    def get_setccdtemperature(self):
        """
        Returns the current camera cooler setpoint in degrees Celsius.
        """
        pass

    @abstractmethod
    def get_startx(self):
        """
        Sets the subframe start position for the X axis (0 based) and returns the current value.
        If binning is active, value is in binned pixels
        """
        pass

    @abstractmethod
    def get_starty(self):
        """
        Sets the subframe start position for the Y axis (0 based) and returns the current value.
        If binning is active, value is in binned pixels.
        """
        pass

    # SETTERS:
    @abstractmethod
    def set_gain(self, value):
        """
        The camera's gain (GAIN VALUE MODE) OR
        the index of the selected camera gain description in the Gains array (GAINS INDEX MODE).
        """
        pass

    @abstractmethod
    def set_readoutmode(self, value):
        """
        Sets the ReadoutMode as an index into the array ReadoutModes.
        """
        pass

    @abstractmethod
    def set_binx(self, value):
        """
        Sets the binning factor for the X axis.
        """
        pass

    @abstractmethod
    def set_biny(self, value):
        """
        Sets the binning factor for the Y axis.
        """
        pass

    @abstractmethod
    def set_numx(self, value):
        """
        Sets the current subframe width.
        """
        pass

    @abstractmethod
    def set_numy(self, value):
        """
        Sets the current subframe height.
        """
        pass

    @abstractmethod
    def set_startx(self, value):
        """
        Sets the current subframe X axis start position in binned pixels.
        """
        pass

    @abstractmethod
    def set_starty(self, value):
        """
        Sets the current subframe Y axis start position in binned pixels.
        """
        pass

    @abstractmethod
    def abortexposure(self):
        """
        Aborts the current exposure, if any, and returns the camera to Idle state.
        """
        pass

    @abstractmethod
    def startexposure(self, duration: float, light=True, save=False):
        """
        Starts an exposure. Use ImageReady to check when the exposure is complete.
        Save is additional parameter making camera save a file
        """
        pass

    @abstractmethod
    def stoptexposure(self):
        """
        Stops the current exposure, if any. If an exposure is in progress, the readout process is initiated.
        Ignored if readout is already in process.
        """
        pass