from .ascom_device import AscomDevice
from abc import abstractmethod


class AscomFocuser(AscomDevice):
    @abstractmethod
    def get_absolute(self):
        """
        True if the focuser is capable of absolute position; that is, being commanded to a specific step location.
        """
        pass

    @abstractmethod
    def get_ismoving(self):
        """
        True if the focuser is currently moving to a new position. False if the focuser is stationary.
        """
        pass

    @abstractmethod
    def get_maxincrement(self):
        """
        Maximum increment size allowed by the focuser; i.e. the maximum number of steps allowed in one move operation.
        """
        pass

    @abstractmethod
    def get_maxstep(self):
        """
        Maximum step position permitted.
        """
        pass

    @abstractmethod
    def get_position(self):
        """
        Current focuser position, in steps.
        """
        pass

    @abstractmethod
    def get_stepsize(self):
        """
        Step size (microns) for the focuser.
        """
        pass

    @abstractmethod
    def get_tempcomp(self):
        """
        Gets the state of temperature compensation mode (if available), else always False.
        """
        pass

    @abstractmethod
    def get_tempcompavailable(self):
        """
        True if focuser has temperature compensation available.
        """
        pass

    @abstractmethod
    def get_temperature(self):
        """
        Current ambient temperature as measured by the focuser.
        """
        pass

    @abstractmethod
    def put_tempcomp(self, value):
        """
        Sets the state of temperature compensation mode.
        value: TempComp
        Set true to enable the focuser's temperature compensation mode,
        otherwise false for normal operation.
        """
        pass

    @abstractmethod
    def put_halt(self):
        """
        Immediately stop any focuser motion due to a previous Move(Int32) method call.
        """
        pass

    @abstractmethod
    def put_move(self, value):
        """
        Moves the focuser by the specified amount or to the specified position
        depending on the value of the Absolute property.
        value: Position
Step    distance or absolute position, depending on the value of the Absolute property
        """
        pass
