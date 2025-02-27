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
from navigate.model.devices.shutter.base import ShutterBase
from navigate.model.devices.device_types import SerialDevice
from navigate.model.devices.APIs.asi.asi_tiger_controller import TigerController
from navigate.tools.decorators import log_initialization

# Logger Setup
p = __name__.split(".")[1]
logger = logging.getLogger(p)


@log_initialization
class ASIShutter(ShutterBase, SerialDevice):
    """ASIShutter - Class for controlling ASI Shutters

    Note
    ----
        Additional information on the ASI Filter Wheel can be found at:
        https://asiimaging.com/docs/fw_1000#fw-1000_ascii_command_set
    """

    def __init__(self, microscope_name, device_connection, configuration, device_id=0):
        """Initialize the ASIFilterWheel class.

        Parameters
        ----------
        microscope_name : str
            Name of the microscope.
        device_connection : TigerController
            Communication object for the ASI Filter Wheel.
        configuration : dict
            Global configuration of the microscope.
        device_id : int
            The ID of the device. Default is 0.
        """

        super().__init__(microscope_name, device_connection, configuration)

        #: float: Delay for filter wheel to change positions.
        #self.wait_until_done_delay = self.device_config["shutter_delay"]

        self.shutter = device_connection

        # Send Filter Wheel/Wheels to Zeroth Position
        #self.filter_wheel.select_filter_wheel(
        #    filter_wheel_number=self.filter_wheel_number
        #)

        #self.filter_wheel.move_filter_wheel(filter_wheel_position=0)

        #: int: Filter wheel position.
        #self.filter_wheel_position = 0

    def __str__(self):
        """String representation of the class."""
        return "ASIShutter"

    @classmethod
    def connect(cls, port, baudrate=115200, timeout=0.25):
        """Build ASIShutter Serial Port connection

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

    def __str__(self) -> str:
        """Return the string representation of the Shutter."""
        return "ASIShutter"

    def open_shutter(self) -> None:
        """Open the Shutter."""
        self.shutter.square_wave()
        self.shutter_state = True

    def close_shutter(self) -> None:
        """Close the Shutter."""
        self.shutter.off()
        self.shutter_state = False

    def __del__(self):
        """Destructor for the ASIFilterWheel class."""
        self.close_shutter()