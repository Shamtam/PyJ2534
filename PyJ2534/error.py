#   PyJ2534 - A complete J2534 Pass-Thru DLL wrapper implementation
#   Copyright (C) 2021  Shamit Som <shamitsom@gmail.com>
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU Affero General Public License as published
#   by the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU Affero General Public License for more details.
#
#   You should have received a copy of the GNU Affero General Public License
#   along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""This module provides helpers to easily handle J2534 errors"""

from enum import IntEnum


class J2534Errors(IntEnum):
    """J2534 return/error codes."""

    STATUS_NOERROR              = 0x00
    ERR_NOT_SUPPORTED           = 0x01
    ERR_INVALID_CHANNEL_ID      = 0x02
    ERR_INVALID_PROTOCOL_ID     = 0x03
    ERR_NULL_PARAMETER          = 0x04
    ERR_INVALID_IOCTL_VALUE     = 0x05
    ERR_INVALID_FLAGS           = 0x06
    ERR_FAILED                  = 0x07
    ERR_DEVICE_NOT_CONNECTED    = 0x08
    ERR_TIMEOUT                 = 0x09
    ERR_INVALID_MSG             = 0x0A
    ERR_INVALID_TIME_INTERVAL   = 0x0B
    ERR_EXCEEDED_LIMIT          = 0x0C
    ERR_INVALID_MSG_ID          = 0x0D
    ERR_DEVICE_IN_USE           = 0x0E
    ERR_INVALID_IOCTL_ID        = 0x0F
    ERR_BUFFER_EMPTY            = 0x10
    ERR_BUFFER_FULL             = 0x11
    ERR_BUFFER_OVERFLOW         = 0x12
    ERR_PIN_INVALID             = 0x13
    ERR_CHANNEL_IN_USE          = 0x14
    ERR_MSG_PROTOCOL_ID         = 0x15
    ERR_INVALID_FILTER_ID       = 0x16
    ERR_NO_FLOW_CONTROL         = 0x17
    ERR_NOT_UNIQUE              = 0x18
    ERR_INVALID_BAUDRATE        = 0x19
    ERR_INVALID_DEVICE_ID       = 0x1A

    RESERVED_J2534_1            = 0x1B

    RESERVED_J2534_2            = 0x10000


_error_msg_map = {
    J2534Errors.STATUS_NOERROR: 'Function call successful',

    J2534Errors.ERR_NOT_SUPPORTED: (
        'Device cannot support requested functionality mandated in this '
        'document. Device is not fully SAE J2534 compliant'
    ),

    J2534Errors.ERR_INVALID_CHANNEL_ID: 'Invalid ChannelID value',

    J2534Errors.ERR_INVALID_PROTOCOL_ID: (
        'Invalid ProtocolID value, unsupported ProtocolID, or there is a '
        'resource conflict (i.e. trying to connect to multiple protocols that '
        'are mutually exclusive such as J1850PWM and J1850VPW, or CAN and SCI '
        'A, etc.)'
    ),

    J2534Errors.ERR_NULL_PARAMETER: (
        'NULL pointer supplied where a valid pointer is required'
    ),

    J2534Errors.ERR_INVALID_IOCTL_VALUE: 'Invalid value for Ioctl parameter',

    J2534Errors.ERR_INVALID_FLAGS: 'Invalid flag values',

    J2534Errors.ERR_FAILED: (
        'Undefined error, use PassThruGetLastError for text description'
    ),

    J2534Errors.ERR_DEVICE_NOT_CONNECTED: 'Device ID invalid',

    J2534Errors.ERR_TIMEOUT: (
        'Timeout. '
        'PassThruReadMsg: No message available to read or could not read the '
        'specified number of messages. The actual number of messages read is '
        'placed in <NumMsgs> '
        'PassThruWriteMsg: Device could not write the specified number of '
        'messages. The actual number of messages sent on the vehicle network '
        'is placed in <NumMsgs>.'
    ),

    J2534Errors.ERR_INVALID_MSG: (
        'Invalid message structure pointed to by pMsg (Reference Section 8 – '
        'Message Structure)'
    ),

    J2534Errors.ERR_INVALID_TIME_INTERVAL: 'Invalid TimeInterval value',

    J2534Errors.ERR_EXCEEDED_LIMIT: (
        'Exceeded maximum number of message IDs or allocated space'
    ),

    J2534Errors.ERR_INVALID_MSG_ID: 'Invalid MsgID value',

    J2534Errors.ERR_DEVICE_IN_USE: 'Device is currently open',

    J2534Errors.ERR_INVALID_IOCTL_ID: 'Invalid IoctlID value',

    J2534Errors.ERR_BUFFER_EMPTY: (
        'Protocol message buffer empty, no messages available to read'
    ),

    J2534Errors.ERR_BUFFER_FULL: (
        'Protocol message buffer full. All the messages specified may not '
        'have been transmitted'
    ),

    J2534Errors.ERR_BUFFER_OVERFLOW: (
        'Indicates a buffer overflow occurred and messages were lost'
    ),

    J2534Errors.ERR_PIN_INVALID: (
        'Invalid pin number, pin number already in use, or voltage already '
        'applied to a different pin'
    ),

    J2534Errors.ERR_CHANNEL_IN_USE: 'Channel number is currently connected',

    J2534Errors.ERR_MSG_PROTOCOL_ID: (
        'Protocol type in the message does not match the protocol associated '
        'with the Channel ID'
    ),

    J2534Errors.ERR_INVALID_FILTER_ID: 'Invalid Filter ID value',

    J2534Errors.ERR_NO_FLOW_CONTROL: (
        'No flow control filter set or matched (for protocolID ISO15765 only).'
    ),

    J2534Errors.ERR_NOT_UNIQUE: (
        'A CAN ID in pPatternMsg or pFlowControlMsg matches either ID in an '
        'existing FLOW_CONTROL_FILTER'
    ),

    J2534Errors.ERR_INVALID_BAUDRATE: (
        'The desired baud rate cannot be achieved within the tolerance '
        'specified in Section 6.5'
    ),

    J2534Errors.ERR_INVALID_DEVICE_ID: 'Unable to communicate with device',

    J2534Errors.RESERVED_J2534_1: 'Reserved for SAE J2534-1',

    J2534Errors.RESERVED_J2534_2: 'Reserved for SAE J2534-2',
}


def _get_error_text(err):

    if isinstance(err, int):
        if err < J2534Errors.RESERVED_J2534_1:
            errorID = J2534Errors(err)
        elif err < J2534Errors.RESERVED_J2534_2:
            errorID = J2534Errors.RESERVED_J2534_1
        else:
            errorID = J2534Errors.RESERVED_J2534_2

    elif isinstance(err, J2534Errors):
        errorID = err

    else:
        return 'Invalid error {}'.format(err)

    return _error_msg_map.get(
        errorID,
        'Invalid or undefined error code 0x{:02x}'.format(err)
    )


class LoadDLLError(Exception):
    """Exception raised when a DLL fails to load."""
    pass


class J2534Error(Exception):
    """Exception raised when J2534 errors are not handled by the wrapper.

    Attributes:
        error (:class:`J2534Errors`): error code
        message (str): error description
    """

    def __init__(self, j2534_error):
        """Initialize the exception with a :class:`J2534Errors`"""
        self.error = j2534_error
        self.message = _get_error_text(j2534_error)
        super(J2534Error, self).__init__('[{}] {}'.format(
            self.error.name, self.message)
        )
