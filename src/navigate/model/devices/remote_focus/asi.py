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


#  Standard Library Imports
import logging
import time
from typing import Any, Dict

# Third Party Imports

# Local Imports
from navigate.model.devices.device_types import SerialDevice
from navigate.model.devices.APIs.asi.asi_tiger_controller import TigerController
from navigate.tools.decorators import log_initialization

# # Logger Setup
p = __name__.split(".")[1]
logger = logging.getLogger(p)


@log_initialization
class ASIRemoteFocus(SerialDevice):
    """RemoteFocusNI Class - Analog control of the remote focus device."""

    def __init__(
        self,
        microscope_name: str,
        device_connection: Any,
        configuration: Dict[str, Any],
    ) -> None:
        """Initialize the RemoteFocusNI class.

        Parameters
        ----------
        microscope_name : str
            The microscope name.
        device_connection : Any
            The device connection object.
        configuration : Dict[str, Any]
            The configuration dictionary.

        """
        #: Any: Device connection object.
        self.device_connection = device_connection

        #: dict: Configuration dictionary.
        self.configuration = configuration

        #: str: Name of the microscope.
        self.microscope_name = microscope_name

        #: dict: Remote focus device parameters.
        self.device_config = configuration["configuration"]["microscopes"][
            microscope_name
        ]["remote_focus"]

        #: float: Sweep time of the DAQ.
        self.sweep_time = 0

        #: float: Camera delay percent.
        self.camera_delay = (
            configuration["configuration"]["microscopes"][microscope_name]["camera"][
                "delay"
            ]
            / 1000
        )

        # Waveform Parameters
        #: float: Remote focus max voltage.
        self.remote_focus_max_voltage = self.device_config["hardware"]["max"]

        #: float: Remote focus min voltage.
        self.remote_focus_min_voltage = self.device_config["hardware"]["min"]

        #: str: The trigger source (e.g., physical channel).
        self.trigger_source = configuration["configuration"]["microscopes"][
            microscope_name
        ]["daq"]["trigger_source"]

        #: str: Output axis on Tiger Controller
        self.axis = self.device_config["power"]["hardware"]["axis"]

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

    def adjust(self, exposure_times, sweep_times, offset=None):
        microscope_state = self.configuration["experiment"]["MicroscopeState"]
        waveform_constants = self.configuration["waveform_constants"]
        imaging_mode = microscope_state["microscope_name"]
        zoom = microscope_state["zoom"]
        # ramp_type = self.configuration["configuration"]["microscopes"][
        #     self.microscope_name]['remote focus device']['ramp_type']

        remote_focus_delay = (
            float(waveform_constants["other_constants"]["remote_focus_delay"]) / 1000
        )

        remote_focus_ramp_falling = (
            float(waveform_constants["other_constants"]["remote_focus_ramp_falling"])
            / 1000
        )

        for channel_key in microscope_state["channels"].keys():
            # channel includes 'is_selected', 'laser', 'filter', 'camera_exposure'...
            channel = microscope_state["channels"][channel_key]

            # Only proceed if it is enabled in the GUI
            if channel["is_selected"] is True:

                # Get the Waveform Parameters - Assumes ETL Delay < Camera Delay.
                # Should Assert.
                laser = channel["laser"]
                exposure_time = exposure_times[channel_key]
                self.sweep_time = sweep_times[channel_key]

                # Remote Focus Parameters
                temp = waveform_constants["remote_focus_constants"][imaging_mode][zoom][
                    laser
                ]["amplitude"]
                if temp == "-" or temp == ".":
                    waveform_constants["remote_focus_constants"][imaging_mode][zoom][
                        laser
                    ]["amplitude"] = "1000"

                remote_focus_amplitude = float(
                    waveform_constants["remote_focus_constants"][imaging_mode][zoom][
                        laser
                    ]["amplitude"]
                )

                # Validation for when user puts a '-' in spinbox
                temp = waveform_constants["remote_focus_constants"][imaging_mode][zoom][
                    laser
                ]["offset"]
                if temp == "-" or temp == ".":
                    waveform_constants["remote_focus_constants"][imaging_mode][zoom][
                        laser
                    ]["offset"] = "0"

                remote_focus_offset = float(
                    waveform_constants["remote_focus_constants"][imaging_mode][zoom][
                        laser
                    ]["offset"]
                )
                if offset is not None:
                    remote_focus_offset += offset

                if self.remote_focus_min_voltage < 0: 
                    self.remote_focus_min_voltage = 0
                if (amplitude + offset) > self.remote_focus_max_voltage: 
                    if offset > self.remote_focus_max_voltage:
                        logger.error("Waveform offset is greater than device maximum voltage")
                        offset = self.remote_focus_max_voltage
                    amplitude = self.remote_focus_max_voltage - offset
                if (offset - amplitude) < self.remote_focus_min_voltage:
                    if offset < self.remote_focus_min_voltage:
                        logger.error("Waveform offset is less than device minimum voltage")
                        offset = self.remote_focus_min_voltage
                    amplitude = offset - self.remote_focus_min_voltage

                # Calculate the Ramp Waveform
                exposure_time=exposure_time,
                sweep_time=self.sweep_time,
                remote_focus_delay=remote_focus_delay,
                camera_delay=self.camera_delay,
                fall=remote_focus_ramp_falling,
                amplitude=remote_focus_amplitude,
                offset=remote_focus_offset,

                self.ramp(exposure_time, sweep_time, remote_focus_delay, camera_delay, fall, amplitude, offset)

    def ramp(
        self,
        exposure_time=0.2,
        sweep_time=0.24,
        remote_focus_delay=0.005,
        camera_delay=0.001,
        fall=0.05,
        amplitude=1,
        offset=0.5,
    ):
        """Returns a numpy array with a sawtooth ramp - typically used for remote focusing.

        The waveform starts at offset and stays there for the delay period, then
        rises linearly to 2x amplitude (amplitude here refers to 1/2 peak-to-peak)
        and drops back down to the offset voltage during the fall period.

        Switching from a left to right remote focus ramp is possible by exchanging the
        rise and fall periods.

        Parameters
        ----------
        sample_rate : Integer
            Unit - Hz
        exposure_time : Float
            Unit - Seconds
        sweep_time : Float
            Unit - Seconds
        remote_focus_delay : Float
            Unit - seconds
        camera_delay : Float
            Unit - seconds
        fall : Float
            Unit - seconds
        amplitude : Float
            Unit - Volts
        offset : Float
            Unit - Volts

        Returns
        -------
        waveform : np.array

        Examples
        --------
        >>> etl_ramp = tunable_lens_ramp(sample_rate, exposure_time, sweep_time, etl_delay,
            camera_delay, fall, amplitude, offset)

        """

        # rise period
        period = int(
            (exposure_time + camera_delay - remote_focus_delay) * 1000
        )

        # delay period
        extra_samples = int(int(sweep_time)- (remote_focus_delay + period + fall))
        if extra_samples > 0:
            _delay_time = remote_focus_delay + fall + extra_samples
        else:
            _delay_time = remote_focus_delay + fall
        
        amplitude *= 1000
        offset *= 1000

        self.remote_focus.SA_waveform(self.axis, 1, amplitude, offset, period)
        self.remote_focus.SAM(self.axis, 2)
        time.sleep(_delay_time)

    
    def move(self, exposure_times, sweep_times, offset=None):
        """Move the remote focus.

        This method moves the remote focus.

        Parameters
        ----------
        exposure_times : dict
            Dictionary of exposure times for each selected channel
        sweep_times : dict
            Dictionary of sweep times for each selected channel
        offset : float
            The offset of the signal in volts.
        """
        
        self.adjust(exposure_times, sweep_times, offset)

    def __del__(self):
        """Destructor for the ASIRemoteFocus class."""
        if self.remote_focus.is_open():
            self.set_power(0)
            logger.debug("ASI Remote Focus - Closing Device.")
            self.laser.disconnect_from_serial() 

        