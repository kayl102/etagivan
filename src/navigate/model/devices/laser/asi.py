# Copyright (c) 2021-2024  The University of Texas Southwestern Medical Center.
# All rights reserved.

# Redistribution and use in source and binary forms, with or without
# modification, are permitted for academic and research use only (subject to the
# limitations in the disclaimer below) provided that the following conditions are met:

#      * Redistributions of source code must retain the above copyright notice,
#      this list of conditions and the following disclaimer.

#      * Redistributions in binary form must reproduce the above copyright
#      notice, this list of conditions and the following disclaimer in the
#      documentation and/or other materials provided with the distribution.

#      * Neither the name of the copyright holders nor the names of its
#      contributors may be used to endorse or promote products derived from this
#      software without specific prior written permission.

# NO EXPRESS OR IMPLIED LICENSES TO ANY PARTY'S PATENT RIGHTS ARE GRANTED BY
# THIS LICENSE. THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND
# CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A
# PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR
# CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
# EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
# BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER
# IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
#

#  Standard Library Imports
import logging
import time

# Third Party Imports

# Local Imports
from navigate.model.devices.laser.base import LaserBase
from navigate.model.devices.device_types import SerialDevice
from navigate.model.devices.APIs.asi.asi_tiger_controller import TigerController
from navigate.tools.decorators import log_initialization

# Logger Setup
p = __name__.split(".")[1]
logger = logging.getLogger(p)


@log_initialization
class ASILaser(LaserBase, SerialDevice):
    """ASILaser - Class for controlling ASI Lasers

    This class is used to control a laser connected to a ASI Device.
    """

    def __init__(self, microscope_name, device_connection, configuration, device_id: int):
        """Initialize the ASILaser class.

        Parameters
        ----------
        microscope_name : str
            The microscope name.
        device_connection : TigerController
            The device connection object.
        configuration : dict
            The device configuration.
        device_id : int
            The laser id.
        """

        super().__init__(microscope_name, device_connection, configuration)
        #: TigerController: ASI Tiger Controller object.
        self.laser = device_connection

        #: dict: Configuration dictionary.
        self.device_config = configuration
        
        #: str: Device type - analog or digital.
        self.device_type = configuration.get("device_type", "analog")

        #: int: Laser Number
        self.axis = configuration["axis"]

        # Set voltage to 0.
        self.laser.move_axis(self.axis, 0)

    def __str__(self):
        """String representation of the class."""
        return "ASILaser"

    @classmethod
    def connect(cls, port, baudrate=115200, timeout=0.25):
        """Build ASILaser Serial Port connection

        Parameters
        ----------
        port : str
            Port for communicating with the filter wheel, e.g., COM1.
        baudrate : int
            Baud rate for communicating with the filter wheel, default is 115200.
        timeout : float
            Timeout for communicating with the filter wheel, default is 0.25.

        Returns
        -------
        tiger_controller : TigerController
            ASI Tiger Controller object.
        """
        # wait until ASI device is ready
        tiger_controller = TigerController(port, baudrate)
        tiger_controller.connect_to_serial()
        if not tiger_controller.is_open():
            logger.error("ASI stage connection failed.")
            raise Exception("ASI stage connection failed.")
        return tiger_controller

    def set_voltage(self, axis, voltage):
        """Change the filter wheel to the filter designated by the filter
        position argument.
        """
        if self.device_type == "analog":
            # TGDAC
            output_voltage = voltage * 1000
            self.laser.move_axis(axis, output_voltage)
        else:
            # Programmable Logic Card
            if voltage > 2.5:
                output_voltage = 5
            else:
                output_voltage = 0
            self.laser.move_digital_axis(axis, output_voltage)

    
    def close(self):
        """Close the ASI Laser serial port.

        Turns the laser off and then closes the port.
        """
        if self.laser.is_open():
            self.laser.move_filter_wheel_to_home()
            logger.debug("ASI Laser - Closing Device.")
            self.laser.disconnect_from_serial()

    def __del__(self):
        """Destructor for the ASILaser class."""
        self.close()


if __name__ == "__main__":
    # Test the ASILaser class
    comport="COM1"
    device_connection = ASILaser.connect(comport, baudrate=115200, timeout=0.25)
    device_config = {
        "axis": 5,
        "min_voltage": 0,
        "max_voltage": 10,
    }
    laser = ASILaser(device_connection, device_config)

    for i in range(10):
        laser.set_analog_voltage(0, wait_until_done=True)
        time.sleep(1)
        laser.set_analog_voltage(10, wait_until_done=True)
        time.sleep(1)

    laser.close()


