from abc import ABC, abstractmethod


class AscomDevice(ABC):
    # GETTERS:
    
    @abstractmethod
    def get_connected(self):
        """
        Retrieves the connected state of the device
        """
        pass
    
    @abstractmethod
    def get_name(self):
        """
        The name of the device
        """
        pass
    
    @abstractmethod
    def get_interfaceversion(self):
        print("ASCOM DEVICE method")
        """
        This method returns the version of the ASCOM device interface contract to which this device complies.
        Only one interface version is current at a moment in time and all new devices should be built to the latest
        interface version. Applications can choose which device interface versions they support and it is in their
        interest to support previous versions as well as the current version to ensure thay can use the largest
        number of devices.
        """
        pass
    
    @abstractmethod
    def get_description(self):
        """
        The description of the device
        """
        pass

    @abstractmethod
    def get_driverinfo(self):
        """
        The description of the driver
        """
        pass

    def get_driverversion(self):
        """
        A string containing only the major and minor version of the driver.
        """
        pass

    def get_supportedactions(self):
        """
        Returns the list of action names supported by this driver.
        """
        pass

    # SETTERS
    @abstractmethod
    def set_connected(self, value):
        pass
