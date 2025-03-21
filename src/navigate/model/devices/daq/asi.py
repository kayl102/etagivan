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


# Standard Imports
import logging
from threading import Lock
import traceback
import time
from typing import Union, Dict, Any

# Third Party Imports
import nidaqmx
import nidaqmx.constants
import nidaqmx.task
import numpy as np
import serial
# Local Imports
from navigate.model.devices.daq.base import DAQBase
from navigate.tools.waveform_template_funcs import get_waveform_template_parameters
from navigate.tools.decorators import log_initialization







def create_camera_task(self, channel_key: str) -> None:
    """Set up the camera trigger task using the ASI Tiger Controller via serial.

    Parameters
    ----------
    channel_key : str
        Channel key for current channel.
    """

    # Compute timing parameters from config
    camera_waveform_repeat_num = self.waveform_repeat_num * self.waveform_expand_num

    if self.analog_outputs:
        camera_high_time = 4  # ms
        camera_low_time = (self.sweep_times[channel_key] * 1000) - camera_high_time
    elif camera_waveform_repeat_num == 1:
        camera_high_time = (self.sweep_times[channel_key] * 1000) - (self.camera_delay * 1000)
        camera_low_time = 4
    else:
        camera_high_time = (self.sweep_times[channel_key] * 1000) - 4
        camera_low_time = 4

    camera_delay_ms = self.camera_delay * 1000  # Convert seconds to ms

    # TTL output line from config
    ttl_channel = self.configuration["configuration"]["microscopes"][self.microscope_name]["daq"]["camera_trigger_out_line"]

    # Construct ASI TTL command
    asi_command = f'TTL X={ttl_channel} P={camera_high_time:.0f} D={camera_delay_ms:.0f}\r'

    # Send command over serial
    try:
        self.serial_port.write(asi_command.encode())
        response = self.serial_port.readline().decode().strip()
        logger.info(f"Sent camera trigger command: {asi_command.strip()}, Response: {response}")
    except Exception:
        logger.exception("Failed to send camera TTL command to ASI Tiger Controller.")

