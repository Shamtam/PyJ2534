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

import logging
import sys
import winreg

_logger = logging.getLogger(__name__)

from ctypes import (
    byref, create_string_buffer, POINTER, cast,
    WinDLL,
    c_char, c_char_p, c_long, c_ulong, c_void_p
)

from .define import (
    IoctlParameter, FilterType, ProgrammingVoltage, IoctlID,
    PASSTHRU_MSG, SBYTE_ARRAY, SCONFIG, SCONFIG_LIST,
)
from .error import LoadDLLError, J2534Errors, J2534Error

def get_interfaces():
    """Get all registered J2534 04.04 Pass-Thru interface .dlls

    Returns a dictionary `{Name: FunctionLibrary}` where `Name` is the
    display string for the given Pass-Thru interface, and
    `FunctionLibrary` is the absolute path to the corresponding .dll
    """

    ret = {}

    _64bit = sys.maxsize > 2**32
    _passthru_key = (
        r"Software\\Wow6432Node\\PassThruSupport.04.04\\" if _64bit else
        r"Software\\PassThruSupport.04.04\\"
    )

    BaseKey = winreg.OpenKeyEx(winreg.HKEY_LOCAL_MACHINE, _passthru_key)
    count = winreg.QueryInfoKey(BaseKey)[0]

    for i in range(count):
        DeviceKey = winreg.OpenKeyEx(BaseKey, winreg.EnumKey(BaseKey, i))
        Name = winreg.QueryValueEx(DeviceKey, "Name")[0]
        FunctionLibrary = winreg.QueryValueEx(DeviceKey, "FunctionLibrary")[0]
        ret[Name] = FunctionLibrary

    return ret

def load_interface(dll_path):
    """Returns a `J2534Dll` for the specified `dll_path`"""
    return J2534Dll(dll_path)

class J2534Dll(object):
    "Wrapper around a J2534 dll as specified in the SAE J2534-1 2004 document"

    def __init__(self, dll_path):

        try:
            self._dll = WinDLL(dll_path)
        except WindowsError:
            raise LoadDLLError

        _func_defs = {
            # extern "C" long WINAPI PassThruOpen (
            #   void *pName
            #   unsigned long *pDeviceID
            # )
            'PassThruOpen': {
                'argtypes': (c_void_p, POINTER(c_ulong)),
            },
            # extern "C" long WINAPI PassThruClose (
            #   unsigned long DeviceID
            # )
            'PassThruClose': {
                'argtypes': (c_ulong,),
            },
            # extern "C" long WINAPI PassThruConnect (
            #   unsigned long DeviceID,
            #   unsigned long ProtocolID,
            #   unsigned long Flags,
            #   unsigned long BaudRate,
            #   unsigned long *pChannelID
            # )
            'PassThruConnect': {
                'argtypes': (
                    c_ulong, c_ulong, c_ulong, c_ulong, POINTER(c_ulong)
                ),
            },
            # extern "C" long WINAPI PassThruDisconnect (
            #   unsigned long ChannelID
            # )
            'PassThruDisconnect': {
                'argtypes': (c_ulong,),
            },
            # extern "C" long WINAPI PassThruReadMsgs (
            #   unsigned long ChannelID,
            #   PASSTHRU_MSG *pMsg,
            #   unsigned long *pNumMsgs,
            #   unsigned long Timeout
            # )
            'PassThruReadMsgs': {
                'argtypes': (
                    c_ulong,
                    POINTER(PASSTHRU_MSG),
                    POINTER(c_ulong),
                    c_ulong
                ),
                'errcheck': self._read_check,
            },
            # extern "C" long WINAPI PassThruWriteMsgs (
            #   unsigned long ChannelID,
            #   PASSTHRU_MSG *pMsg,
            #   unsigned long *pNumMsgs,
            #   unsigned long Timeout
            # )
            'PassThruWriteMsgs': {
                'argtypes': (
                    c_ulong,
                    POINTER(PASSTHRU_MSG),
                    POINTER(c_ulong),
                    c_ulong
                ),
            },
            # extern "C" long WINAPI PassThruStartPeriodicMsg (
            #   unsigned long ChannelID,
            #   PASSTHRU_MSG *pMsg,
            #   unsigned long *pMsgID,
            #   unsigned long TimeInterval
            # )
            'PassThruStartPeriodicMsg': {
                'argtypes': (
                    c_ulong,
                    POINTER(PASSTHRU_MSG),
                    POINTER(c_ulong),
                    c_ulong
                ),
            },
            # extern "C" long WINAPI PassThruStopPeriodicMsg (
            #   unsigned long ChannelID,
            #   unsigned long MsgID
            # )
            'PassThruStopPeriodicMsg': {
                'argtypes': (c_ulong, c_ulong),
            },
            # extern "C" long WINAPI PassThruStartMsgFilter (
            #   unsigned long ChannelID,
            #   unsigned long FilterType,
            #   PASSTHRU_MSG *pMaskMsg,
            #   PASSTHRU_MSG *pPatternMsg,
            #   PASSTHRU_MSG *pFlowControlMsg,
            #   unsigned long *pFilterID
            # )
            'PassThruStartMsgFilter': {
                'argtypes': (
                    c_ulong,
                    c_ulong,
                    POINTER(PASSTHRU_MSG),
                    POINTER(PASSTHRU_MSG),
                    POINTER(PASSTHRU_MSG),
                    POINTER(c_ulong)
                ),
            },
            # extern "C" long WINAPI PassThruStopMsgFilter (
            #   unsigned long ChannelID,
            #   unsigned long FilterID
            # )
            'PassThruStopMsgFilter': {
                'argtypes': (c_ulong, c_ulong),
            },
            # extern "C" long WINAPI PassThruSetProgrammingVoltage (
            #   unsigned long DeviceID,
            #   unsigned long PinNumber,
            #   unsigned long Voltage
            # )
            'PassThruSetProgrammingVoltage': {
                'argtypes': (c_ulong, c_ulong, c_ulong),
            },
            # extern "C" long WINAPI PassThruReadVersion (
            #   unsigned long DeviceID
            #   char *pFirmwareVersion,
            #   char *pDllVersion,
            #   char *pApiVersion
            # )
            'PassThruReadVersion': {
                'argtypes': (c_ulong, c_char_p, c_char_p, c_char_p),
            },
            # extern "C" long WINAPI PassThruGetLastError (
            #   char   *pErrorDescription
            # )
            'PassThruGetLastError': {
                'argtypes': (c_char_p,),
                'errcheck': lambda x, y, z: None, # no callback
            },
            # extern "C" long WINAPI PassThruIoctl (
            #   unsigned long ChannelID,
            #   unsigned long IoctlID,
            #   void *pInput,
            #   void *pOutput
            # )
            'PassThruIoctl': {
                'argtypes': (c_ulong, c_ulong, c_void_p, c_void_p),
            }
        }
        _default_restype = J2534Errors
        _default_errcheck = self._error_check

        # annotate all DLL functions
        for func in _func_defs:
            fdef = _func_defs[func]
            f = self._dll.__getattr__(func)

            # set default return types and callback functions
            if 'restype' not in fdef:
                fdef['restype'] = _default_restype
            if 'errcheck' not in fdef:
                fdef['errcheck'] = _default_errcheck

            # commit annotation
            for key, val in fdef.items():
                f.__setattr__(key, val)

    def _error_check(self, result, func, arguments):
        """Default callback for J2534 DLL function calls"""
        if result != J2534Errors.STATUS_NOERROR:
            raise J2534Error(result)

    def _read_check(self, result, func, arguments):
        """Callback for a J2534 `PassThruReadMsgs` call"""
        if result == J2534Errors.ERR_BUFFER_EMPTY:
            return
        else:
            self._error_check(result, func, arguments)

    def PassThruOpen(self):
        """Open the Pass-Thru device.

        Returns a handle to the opened device
        """
        dev_id = c_ulong()
        self._dll.PassThruOpen(c_void_p(), byref(dev_id))
        return dev_id

    def PassThruClose(self, device_id):
        """Close the Pass-Thru device

        Arguments:
        - `device_id`: handle to the previously opened device
        """
        self._dll.PassThruClose(device_id)

    def PassThruConnect(self, device_id, protocol, flags, baud):
        """Establish a Pass-Thru connection using the given device

        Returns a handle to the channel if successfully opened.

        Arguments:
        `device_id`: handle to the previously opened device
        `protocol`: `ProtocolID`
        `flags`: `ProtocolFlags`
        `baud`: `int` specifying the desired baud rate
        """
        chan_id = c_ulong()
        self._dll.PassThruConnect(
            device_id,
            protocol,
            flags,
            baud,
            chan_id
        )
        return chan_id

    def PassThruDisconnect(self, channel_id):
        """Close the specified Pass-Thru channel

        Arguments:
        `channel_id`: the handle to the previously opened channel
        """
        self._dll.PassThruDisconnect(channel_id)

    def PassThruReadMsgs(self, channel_id, num_msgs=1, timeout=None):
        """Read messages from the specified channel.

        Returns a `list` containing all read `PASSTHRU_MSG` instances

        Arguments:
        - `channel_id`: the handle to the previously opened channel

        Keywords [Default]:
        - `num_msgs` [`1`]: the number of messages to attempt to read
        - `timeout` [`None`]: `int` specifying the read timeout in ms.
            If `None`, then this function will return up to `num_msgs`
            from the receive buffer (or nothing) and return immediately.
            Otherwise, this function will return either when the timeout
            has expired, an error occurs, or the specified number of
            messages has been read.
        """
        Msg = (PASSTHRU_MSG*num_msgs)()
        NumMsgs = c_ulong(num_msgs)

        if timeout is None or timeout < 0:
            timeout = 0

        ret = self._dll.PassThruReadMsgs(
            channel_id, byref(Msg[0]), byref(NumMsgs), timeout
        )

        return [] if ret == J2534Errors.ERR_BUFFER_EMPTY else list(Msg)[:NumMsgs.value]

    def PassThruWriteMsgs(self, channel_id, msgs, timeout=None):
        """Write messages to the specified channel.

        Returns the number of messages successfully transmitted (non-zero
        timeout) or queued (no timeout).

        Arguments:
        - `channel_id`: the handle to the previously opened channel
        - `msgs`: `list` of `PASSTHRU_MSG` instances

        Keywords [Default]
        - `timeout` [`None`]: `int` specifying the write timeout in ms.
            If `None`, then this function will queue up to `num_msgs`
            into the write buffer, and return immediately. Otherwise,
            this function will return either when the timeout has
            expired, an error occurs, or the specified number of
            messages have been written.
        """
        Msg = (PASSTHRU_MSG*len(msgs))(*msgs)
        NumMsgs = c_ulong(len(msgs))

        if timeout is None or timeout < 0:
            timeout = 0

        self._dll.PassThruWriteMsgs(
            channel_id, byref(Msg[0]), byref(NumMsgs), timeout
        )

        return NumMsgs.value

    def PassThruStartPeriodicMsg(self, channel_id, msgs, interval):
        """Queue the specified messages for periodic transmission.

        Returns a handle to this periodic message.

        Arguments:
        - `channel_id`: the handle to the previously opened channel
        - `msgs`: `list` of `PASSTHRU_MSG` instances
        - `interval`: `int` specifying the period of transmissions, in
            ms. Valid intervals are between 5-65535ms
        """
        if interval not in range(5, 65536):
            raise ValueError('`interval` must be between 5-65535')

        Msg = (PASSTHRU_MSG*len(msgs))(*msgs)
        MsgID = c_ulong()

        self._dll.PassThruStartPeriodicMsg(
            channel_id, byref(Msg[0]), byref(MsgID), interval
        )

        return MsgID

    def PassThruStopPeriodicMsg(self, channel_id, msg_id):
        """Stop the transmission of the specified message

        Arguments:
        - `channel_id`: the handle to the previously opened channel
        - `msg_id`: the handle to the periodic message to stop
        """
        self._dll.PassThruStopPeriodicMsg(channel_id, msg_id)

    def PassThruStartMsgFilter(
        self, channel_id, filter_type,
        mask_msg=None, pattern_msg=None, flow_msg=None
    ):
        """Configure filtering for messages on the specified channel.

        Returns a handle to the created filter. Keywords are to be
        specified as required. See the SAE J2534-1 recommended practices
        document for more information.

        Arguments:
        - `channel_id`: the handle to the previously opened channel
        - `filter_type`: `FilterType`

        Keywords [Default]
        - `mask_msg` [`None`]: `PASSTHRU_MSG`
        - `pattern_msg` [`None`]: `PASSTHRU_MSG`
        - `flow_msg` [`None`]: `PASSTHRU_MSG`, ignored for
            `PASS_FILTER` or `BLOCK_FILTER` cases
        """
        FilterID = c_ulong()

        if filter_type == FilterType.FLOW_CONTROL_FILTER:
            args = [
                channel_id, filter_type,
                byref(mask_msg), byref(pattern_msg), byref(flow_msg),
                byref(FilterID)
            ]
        else:
            args = [
                channel_id, filter_type,
                byref(mask_msg), byref(pattern_msg), None,
                byref(FilterID)
            ]

        self._dll.PassThruStartMsgFilter(*args)

        return FilterID

    def PassThruStopMsgFilter(self, channel_id, filter_id):
        """Remove the specified filter from the specified channel

        Arguments:
        - `channel_id`: the handle to the previously opened channel
        - `filter_id`: the handle to the periodic message to stop
        """
        self._dll.PassThruStopMsgFilter(channel_id, filter_id)

    def PassThruSetProgrammingVoltage(self, device_id, pin_number, voltage):
        """Set the programming voltage on the specified pin on the specified device

        Arguments:
        - `device_id` - handle to the previously opened device
        - `pin_number` - `ProgrammingPin`
        - `voltage` - `int` specifying the voltage to apply to the pin.
            The voltage can either directly specified in mV, or via the
            `ProgrammingVoltage` enumeration for cases where it's
            desired to switch off the voltage or short the pin to GND.
            Acceptable ranges are between 5000 and 20000.
        """
        valid_voltages = range(
            ProgrammingVoltage.MIN_VOLTAGE, ProgrammingVoltage.MAX_VOLTAGE + 1
        )
        if voltage not in (
            [   ProgrammingVoltage.SHORT_TO_GROUND,
                ProgrammingVoltage.VOLTAGE_OFF
            ] + list(valid_voltages)
        ):
            raise ValueError(
                '`voltage` must be between {} and {}'.format(
                    ProgrammingVoltage.MIN_VOLTAGE.value,
                    ProgrammingVoltage.MAX_VOLTAGE.value
                )
            )

        self._dll.PassThruSetProgrammingVoltage(
            device_id, pin_number.value, voltage
        )

    def PassThruReadVersion(self, device_id):
        """Returns a 3-tuple of (device firmware, DLL, and API) versions

        Arguments:
        `device_id`: handle to the previously opened device
        """
        fw_str = create_string_buffer(80)
        dll_str = create_string_buffer(80)
        api_str = create_string_buffer(80)
        self._dll.PassThruReadVersion(
            device_id, fw_str, dll_str, api_str
        )
        return (fw_str, dll_str, api_str)

    def PassThruGetLastError(self):
        desc = create_string_buffer(80)
        self._dll.PassThruGetLastError(desc)
        return desc.value

    def PassThruIoctlGetConfig(self, channel_id, params):
        """Get protocol configuration parameters for the given channel.

        Returns a `dict` of {`IoctlParameter`: `int`} instances.

        Arguments:
        - `channel_id`: handle to the previously opened channel
        - `params`: `list` of `IoctlParameter`s to retrieve the values of
        """
        _unused_params = set([
            IoctlParameter.P1_MIN,
            IoctlParameter.P2_MIN,
            IoctlParameter.P2_MAX,
            IoctlParameter.P3_MAX,
            IoctlParameter.P4_MAX,
        ])

        _warn_params = set(params).intersection(_unused_params)
        for p in _warn_params:
            _logger.warn(
                '{} not supported by interface, ignoring'.format(p.name)
            )

        _params = set(params) - _unused_params
        ioctl_params = [
            SCONFIG(par, 0) for par in _params if par not in _unused_params
        ]

        Config = (SCONFIG*len(ioctl_params))(*ioctl_params)
        Input = SCONFIG_LIST(len(params), cast(Config, POINTER(SCONFIG)))
        self._dll.PassThruIoctl(
            channel_id,
            IoctlID.GET_CONFIG,
            byref(Input),
            None
        )
        return {IoctlParameter(x.Parameter): x.Value for x in Config}

    def PassThruIoctlSetConfig(self, channel_id, params):
        """Set protocol configuration parameters for the given channel.

        Arguments:
        - `channel_id`: handle to the previously opened channel
        - `params`: `dict` of {`IoctlParameter`: `int`} key-val pairs
        """
        ioctl_params = [SCONFIG(par.value, val) for par, val in params.items()]

        Config = (SCONFIG*len(ioctl_params))(*ioctl_params)
        Input = SCONFIG_LIST(len(params), cast(Config, POINTER(SCONFIG)))
        self._dll.PassThruIoctl(
            channel_id,
            IoctlID.SET_CONFIG,
            byref(Input),
            None
        )

    def PassThruIoctlReadVbatt(self, device_id):
        """Read the voltage at pin 16 of the J1962 connector

        Returns an `int` indicating the voltage in mV

        Arguments:
        - `device_id`: handle to the previously opened device
        """
        Output = c_ulong()
        self._dll.PassThruIoctl(
            device_id,
            IoctlID.READ_VBATT,
            None,
            byref(Output)
        )
        return Output.value

    def PassThruIoctlReadProgVoltage(self, device_id):
        """Read the programming voltage of the pass-thru device

        Returns an `int` indicating the voltage in mV

        Arguments:
        - `device_id`: handle to the previously opened device
        """
        Output = c_ulong()
        self._dll.PassThruIoctl(
            device_id,
            IoctlID.READ_PROG_VOLTAGE,
            None,
            byref(Output)
        )
        return Output.value

    def PassThruIoctlFiveBaudInit(self, channel_id, addr):
        """Initiate a five-baud initialization

        Returns a `bytes` containing the response from the ECU.

        Arguments:
        - `channel_id`: handle to the previously opened channel
        - `addr`: `int` containing the target address
        """
        Input = SBYTE_ARRAY(1, bytes([addr]))
        Output = SBYTE_ARRAY(2, b'\xff\xff')
        self._dll.PassThruIoctl(
            channel_id,
            IoctlID.FIVE_BAUD_INIT,
            byref(Input),
            byref(Output)
        )

    def PassThruIoctlFastInit(self, channel_id, msg=None):
        """Initiate a fast initialization

        Returns a `PASSTHRU_MSG` containing the response from the ECU,
        or `None` if no response is expected. If a response is not
        received in the allowed time, initialization has failed
        and this will raise an exception.

        Arguments:
        - `channel_id`: handle to the previously opened channel

        Keywords [Default]
        - `msg` [`None`]: `PASSTHRU_MSG` containing the message to be
            sent to the ECU for initialization.
        """
        Input = PASSTHRU_MSG()
        Output = PASSTHRU_MSG()
        self._dll.PassThruIoctl(
            channel_id,
            IoctlID.FAST_INIT,
            byref(Input) if Input is not None else None,
            byref(Output)
        )
        return Output

    def PassThruIoctlClearTxBuffer(self, channel_id):
        """Clear the transmit messages queue

        Arguments:
        - `channel_id`: handle to the previously opened channel
        """
        self._dll.PassThruIoctl(
            channel_id,
            IoctlID.CLEAR_TX_BUFFER,
            None,
            None
        )

    def PassThruIoctlClearRxBuffer(self, channel_id):
        """Clear the received messages queue

        Arguments:
        - `channel_id`: handle to the previously opened channel
        """
        self._dll.PassThruIoctl(
            channel_id,
            IoctlID.CLEAR_RX_BUFFER,
            None,
            None
        )

    def PassThruIoctlClearPeriodicMsgs(self, channel_id):
        """Clear all configured periodic messages

        Arguments:
        - `channel_id`: handle to the previously opened channel
        """
        self._dll.PassThruIoctl(
            channel_id,
            IoctlID.CLEAR_PERIODIC_MSGS,
            None,
            None
        )

    def PassThruIoctlClearMsgFilters(self, channel_id):
        """Clear all configured filters

        Arguments:
        - `channel_id`: handle to the previously opened channel
        """
        self._dll.PassThruIoctl(
            channel_id,
            IoctlID.CLEAR_MSG_FILTERS,
            None,
            None
        )

    def PassThruIoctlClearFunctMsgLookupTable(self, channel_id):
        """Clear the functional message look-up table

        Arguments:
        - `channel_id`: handle to the previously opened channel
        """
        self._dll.PassThruIoctl(
            channel_id,
            IoctlID.CLEAR_FUNCT_MSG_LOOKUP_TABLE,
            None,
            None
        )

    def PassThruIoctlAddToFunctMsgLookupTable(self, channel_id, addrs):
        """Add addresses to the functional message look-up table

        Arguments:
        - `channel_id`: handle to the previously opened channel
        - `addrs`: `list` of `int` containing the addresses to be added
        """
        Input = SBYTE_ARRAY(len(addrs), bytes(addrs))
        self._dll.PassThruIoctl(
            channel_id,
            IoctlID.ADD_TO_FUNCT_MSG_LOOKUP_TABLE,
            byref(Input),
            None
        )

    def PassThruIoctlDeleteFromFunctMsgLookupTable(self, channel_id, addrs):
        """Delete addresses to the functional message look-up table

        Arguments:
        - `channel_id`: handle to the previously opened channel
        - `addrs`: `list` of `int` containing the addresses to be deleted
        """
        Input = SBYTE_ARRAY(len(addrs), bytes(addrs))
        self._dll.PassThruIoctl(
            channel_id,
            IoctlID.DELETE_FROM_FUNCT_MSG_LOOKUP_TABLE,
            byref(Input),
            None
        )
