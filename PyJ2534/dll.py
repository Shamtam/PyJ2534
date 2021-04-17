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

"""This module provides a Python-native implementation of the J2534-1 API."""

import logging
import platform
import sys

from ctypes import (
    byref, create_string_buffer, POINTER,
    c_char_p, c_ulong, c_void_p
)

from .define import (
    IoctlParameter, FilterType, ProgrammingVoltage, IoctlID,
    PASSTHRU_MSG, SBYTE_ARRAY, SCONFIG, SCONFIG_LIST,
)
from .error import LoadDLLError, J2534Errors, J2534Error

_logger = logging.getLogger(__name__)
_platform = platform.architecture()[1].lower()


def get_interfaces():
    """Enumerate all registered J2534 04.04 Pass-Thru interface DLLs

    Returns:
        dict: A dict mapping display names of any registered J2534
        Pass-Thru DLLs to their absolute filepath.

        The name can be used in user-facing GUI elements to allow
        selection of a particular Pass-Thru device, and filepath can
        be passed to :func:`load_interface` to instantiate a
        :class:`J2534Dll` wrapping the desired DLL.
    """

    if 'win' not in _platform:
        raise RuntimeError('PyJ2534 currently only supports Windows')
    else:
        import winreg

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
    """Load a J2534 DLL.

    Args:
        dll_path (str): Absolute filepath to the DLL to load

    Returns:
        :class:`J2534Dll`: A wrapper around the supplied DLL
    """
    return J2534Dll(dll_path)


class J2534Dll(object):
    """Wrapper around a J2534-1 DLL.

    Refer to the J2534-1 API specification for more information.

    All functions raise a :class:`.J2534Error` if an error occurs.
    """

    def __init__(self, dll_path):
        """Instantiate a wrapper to the DLL at the given filepath."""

        try:
            if 'win' not in _platform:
                raise RuntimeError('PyJ2534 currently only supports Windows')
            else:
                from ctypes import WinDLL

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

    def __repr__(self):
        return '<{}: {}>'.format(
            self.__class__.__name__,
            self._dll._name
        )

    def _error_check(self, result, func, arguments):
        """Default callback for J2534 DLL function calls."""
        if result != J2534Errors.STATUS_NOERROR:
            raise J2534Error(result)

    def _read_check(self, result, func, arguments):
        """Callback for a J2534 :func:`PassThruReadMsgs` call."""
        if result == J2534Errors.ERR_BUFFER_EMPTY:
            return
        else:
            self._error_check(result, func, arguments)

    def PassThruOpen(self):
        """Open the Pass-Thru device.

        Returns:
            int: Handle to the opened device
        """
        dev_id = c_ulong()
        self._dll.PassThruOpen(c_void_p(), byref(dev_id))
        return dev_id

    def PassThruClose(self, device_id):
        """Close the Pass-Thru device

        Args:
            device_id (int): Handle to the previously opened device
        """
        self._dll.PassThruClose(device_id)

    def PassThruConnect(self, device_id, protocol, flags, baud):
        """Establish a Pass-Thru connection using the given device.

        Args:
            device_id (int):
                Handle to the previously opened device
            protocol (:class:`.ProtocolID`):
                Desired protocol
            flags (:class:`.ProtocolFlags`):
                Connection flags
            baud (int):
                Desired baud rate

        Returns:
            int: Handle to the opened channel
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
        """Close the specified Pass-Thru channel.

        Args:
            channel_id (int): Handle to the previously opened channel
        """
        self._dll.PassThruDisconnect(channel_id)

    def PassThruReadMsgs(self, channel_id, num_msgs=1, timeout=None):
        """Read messages from the specified channel.

        Args:
            channel_id (int):
                Handle to the previously opened channel
            num_msgs (int):
                Number of messages to attempt to read.
            timeout (int):
                Read timeout in ms, or None.

                If None, then this function will return up to
                ``num_msgs`` from the receive buffer (or nothing) and
                return immediately.

                Otherwise, this function will return either when the
                timeout has expired, an error occurs, or the specified
                number of messages has been read.

        Returns:
            list: list of :py:class:`PyJ2534.define.PASSTHRU_MSG`
            instances.

            If no timeout is specified, up to ``num_msgs`` messages from
            the receive buffer are returned immediately.

            Otherwise, this function will return when ``num_msgs``
            messages have been read from the receive buffer, or raises
            a timeout :class:`.J2534Error` if the timeout lapses before
            ``num_msgs`` messages have been read.
        """
        Msg = (PASSTHRU_MSG*num_msgs)()
        NumMsgs = c_ulong(num_msgs)

        if timeout is None or timeout < 0:
            timeout = 0

        ret = self._dll.PassThruReadMsgs(
            channel_id, byref(Msg[0]), byref(NumMsgs), timeout
        )

        return (
            [] if ret == J2534Errors.ERR_BUFFER_EMPTY
            else list(Msg)[:NumMsgs.value]
        )

    def PassThruWriteMsgs(self, channel_id, msgs, timeout=None):
        """Write messages to the specified channel.

        Returns the number of messages successfully transmitted
        (non-zero timeout) or queued (no timeout).

        Args:
            channel_id (int):
                Handle to the previously opened channel
            msgs (list):
                list of :class:`.PASSTHRU_MSG` instances
            timeout (int):
                Write timeout in ms, or None

        Returns:
            int: Number of successfully transmitted/queued messages.

            If no timeout is specified, the number of messages queued
            into the write buffer is returned immediately.

            Otherwise, the number of transmitted messages is returned,
            or a timeout :class:`.J2534Error` is raised if the timeout
            lapses before all provided messages have been transmitted.
        """
        Msg = (PASSTHRU_MSG*len(msgs))(*msgs)
        NumMsgs = c_ulong(len(msgs))

        if timeout is None or timeout < 0:
            timeout = 0

        self._dll.PassThruWriteMsgs(
            channel_id, byref(Msg[0]), byref(NumMsgs), timeout
        )

        return NumMsgs.value

    def PassThruStartPeriodicMsg(self, channel_id, msg, interval):
        """Queue the specified message for periodic transmission.

        Args:
            channel_id (int):
                Handle to the previously opened channel
            msg (:class:`.PASSTHRU_MSG`):
                Message to be queued
            interval (int):
                Period of transmissions, in ms. Valid intervals are
                between 5-65535ms

        Returns:
            int: Handle to the periodic message
        """
        if interval not in range(5, 65536):
            raise ValueError('`interval` must be between 5-65535')

        MsgID = c_ulong()

        self._dll.PassThruStartPeriodicMsg(
            channel_id, byref(msg), byref(MsgID), interval
        )

        return MsgID

    def PassThruStopPeriodicMsg(self, channel_id, msg_id):
        """Stop the transmission of the specified message

        Args:
            channel_id (int):
                Handle to the previously opened channel
            msg_id (int):
                Handle to the periodic message to stop
        """
        self._dll.PassThruStopPeriodicMsg(channel_id, msg_id)

    def PassThruStartMsgFilter(
        self, channel_id, filter_type,
        mask_msg=None, pattern_msg=None, flow_msg=None
    ):
        """Configure filtering for messages on the specified channel.

        Keywords are to be specified as required. See the SAE J2534-1
        recommended practices document for more information.

        Args:
            channel_id (int):
                Handle to the previously opened channel
            filter_type (:class:`.FilterType`):
                Type of filter
            mask_msg (:class:`.PASSTHRU_MSG`):
                Mask message
            pattern_msg (:class:`PASSTHRU_MSG`):
                Pattern message
            flow_msg (:class:`PASSTHRU_MSG`):
                ignored when ``filter_type`` is
                :attr:`~.FilterType.PASS_FILTER` or
                :attr:`~.FilterType.BLOCK_FILTER`

        Returns:
            int: Handle to the created filter.
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
        """Remove the specified filter from the specified channel.

        Args:
            channel_id (int):
                Handle to the previously opened channel
            filter_id (int):
                Handle to the periodic message to stop
        """
        self._dll.PassThruStopMsgFilter(channel_id, filter_id)

    def PassThruSetProgrammingVoltage(self, device_id, pin_number, voltage):
        """Set the programming voltage on the specified pin on the specified device.

        Args:
            device_id (int):
                Handle to the previously opened device
            pin_number (:class:`.ProgrammingPin`):
                Pin to set
            voltage (int):
                Voltage to apply to the pin. The voltage can either
                directly specified in mV, or via the
                :class:`.ProgrammingVoltage` enumeration for cases where
                it's desired to switch off the voltage or short the pin
                to GND. Acceptable ranges are between 5000 and 20000.
        """
        valid_voltages = range(
            ProgrammingVoltage.MIN_VOLTAGE, ProgrammingVoltage.MAX_VOLTAGE + 1
        )
        if voltage not in (
            [
                ProgrammingVoltage.SHORT_TO_GROUND,
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
        """Get version information.

        Args:
            device_id (int): Handle to the previously opened device

        Returns:
            tuple: 3-tuple of versions: (device firmware, DLL, and API)
        """
        fw_str = create_string_buffer(80)
        dll_str = create_string_buffer(80)
        api_str = create_string_buffer(80)
        self._dll.PassThruReadVersion(
            device_id, fw_str, dll_str, api_str
        )
        return (fw_str, dll_str, api_str)

    def PassThruGetLastError(self):
        """Get the last error message generated by the interface.

        Returns:
            str: Error message
        """
        desc = create_string_buffer(80)
        self._dll.PassThruGetLastError(desc)
        return desc.value

    def PassThruIoctlGetConfig(self, channel_id, params):
        """Get protocol configuration parameters for the given channel.

        Args:
            channel_id (int):
                Handle to the previously opened channel
            params (list):
                list of :class:`.IoctlParameter` to retrieve values of

        Returns:
            dict: dict mapping the requested :class:`.IoctlParameter` to
            their currently set int values
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
        Input = SCONFIG_LIST(ioctl_params)
        self._dll.PassThruIoctl(
            channel_id,
            IoctlID.GET_CONFIG,
            byref(Input),
            None
        )
        return {IoctlParameter(x.Parameter): x.Value for x in Input.Config}

    def PassThruIoctlSetConfig(self, channel_id, params):
        """Set protocol configuration parameters for the given channel.

        Args:
            channel_id (int):
                Handle to the previously opened channel
            params (dict):
                Mapping of :class:`.IoctlParameter` to desired values
        """
        ioctl_params = [SCONFIG(par.value, val) for par, val in params.items()]
        Input = SCONFIG_LIST(ioctl_params)
        self._dll.PassThruIoctl(
            channel_id,
            IoctlID.SET_CONFIG,
            byref(Input),
            None
        )

    def PassThruIoctlReadVbatt(self, device_id):
        """Read the voltage at pin 16 of the J1962 connector.

        Args:
            device_id (int): Handle to the previously opened device

        Returns:
            int: Pin 16 voltage, in mV
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
        """Read the programming voltage of the Pass-Thru device.

        Returns an `int` indicating the voltage in mV

        Args:
            device_id (int): Handle to the previously opened device

        Returns:
            int: Programming voltage, in mV
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
        """Initiate a five-baud initialization.

        Args:
            channel_id (int):
                Handle to the previously opened channel
            addr (int):
                Target address for initialization

        Returns:
            bytes: The response from the ECU
        """
        Input = SBYTE_ARRAY(bytes([addr]))
        Output = SBYTE_ARRAY(b'\xff\xff')
        self._dll.PassThruIoctl(
            channel_id,
            IoctlID.FIVE_BAUD_INIT,
            byref(Input),
            byref(Output)
        )

    def PassThruIoctlFastInit(self, channel_id, msg=None):
        """Initiate a fast initialization.

        Args:
            channel_id (int):
                Handle to the previously opened channel
            msg (:class:`.PASSTHRU_MSG`):
                Message to be sent to the ECU for initialization.

        Returns:
            :class:`.PASSTHRU_MSG`: If a response is expected, a
            :class:`.PASSTHRU_MSG` containing the response from the ECU,
            ``None`` otherwise.
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
        """Clear the transmit messages queue.

        Args:
            channel_id (int): Handle to the previously opened channel
        """
        self._dll.PassThruIoctl(
            channel_id,
            IoctlID.CLEAR_TX_BUFFER,
            None,
            None
        )

    def PassThruIoctlClearRxBuffer(self, channel_id):
        """Clear the received messages queue.

        Args:
            channel_id (int): Handle to the previously opened channel
        """
        self._dll.PassThruIoctl(
            channel_id,
            IoctlID.CLEAR_RX_BUFFER,
            None,
            None
        )

    def PassThruIoctlClearPeriodicMsgs(self, channel_id):
        """Clear all configured periodic messages.

        Args:
            channel_id (int): Handle to the previously opened channel
        """
        self._dll.PassThruIoctl(
            channel_id,
            IoctlID.CLEAR_PERIODIC_MSGS,
            None,
            None
        )

    def PassThruIoctlClearMsgFilters(self, channel_id):
        """Clear all configured filters.

        Args:
            channel_id (int): Handle to the previously opened channel
        """
        self._dll.PassThruIoctl(
            channel_id,
            IoctlID.CLEAR_MSG_FILTERS,
            None,
            None
        )

    def PassThruIoctlClearFunctMsgLookupTable(self, channel_id):
        """Clear the functional message look-up table.

        Args:
            channel_id (int): Handle to the previously opened channel
        """
        self._dll.PassThruIoctl(
            channel_id,
            IoctlID.CLEAR_FUNCT_MSG_LOOKUP_TABLE,
            None,
            None
        )

    def PassThruIoctlAddToFunctMsgLookupTable(self, channel_id, addrs):
        """Add addresses to the functional message look-up table.

        Args:
            channel_id (int):
                Handle to the previously opened channel
            addrs (list):
                list of int containing the addresses to be added
        """
        Input = SBYTE_ARRAY(bytes(addrs))
        self._dll.PassThruIoctl(
            channel_id,
            IoctlID.ADD_TO_FUNCT_MSG_LOOKUP_TABLE,
            byref(Input),
            None
        )

    def PassThruIoctlDeleteFromFunctMsgLookupTable(self, channel_id, addrs):
        """Delete addresses to the functional message look-up table

        Args:
            channel_id (int):
                Handle to the previously opened channel
            addrs (list):
                list of int containing the addresses to be deleted
        """
        Input = SBYTE_ARRAY(bytes(addrs))
        self._dll.PassThruIoctl(
            channel_id,
            IoctlID.DELETE_FROM_FUNCT_MSG_LOOKUP_TABLE,
            byref(Input),
            None
        )
