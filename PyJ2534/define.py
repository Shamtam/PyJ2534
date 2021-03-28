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

"""This module contains Python-native versions of all J2534 constructs."""

import ctypes as ct

from enum import IntEnum, IntFlag


class ProtocolID(IntEnum):
    J1850VPW        = 0x01
    J1850PWM        = 0x02
    ISO9141         = 0x03
    ISO14230        = 0x04
    CAN             = 0x05
    ISO15765        = 0x06
    SCI_A_ENGINE    = 0x07
    SCI_A_TRANS     = 0x08
    SCI_B_ENGINE    = 0x09
    SCI_B_TRANS     = 0x0A

    RESERVED        = 0x0B      # through 0x7FFF
    RESERVED_J2534_2 = 0x8000   # through 0xFFFF
    MFG_SPECIFIC    = 0x10000   # through 0xFFFFFFFF


class ProtocolFlags(IntFlag):
    ISO9141_K_LINE_ONLY = 0x1000
    CAN_ID_BOTH         = 0x800
    ISO9141_NO_CHECKSUM = 0x200
    CAN_29BIT_ID        = 0x100


class FilterType(IntEnum):
    PASS_FILTER         = 0x1
    BLOCK_FILTER        = 0x2
    FLOW_CONTROL_FILTER = 0x3

    RESERVED            = 0x4       # through 0x7FFF
    RESERVED_J2534_2    = 0x8000    # through 0xFFFF
    MFG_SPECIFIC        = 0x10000   # through 0xFFFFFFFF


class ProgrammingPin(IntEnum):
    AUX_OUTPUT  = 0
    PIN6        = 6
    PIN9        = 9
    PIN11       = 11
    PIN12       = 12
    PIN13       = 13
    PIN14       = 14
    PIN15       = 15


class ProgrammingVoltage(IntEnum):
    Voltage_05V     = 0x00001388    # 5000mV
    Voltage_20V     = 0x00004E20    # 20000mV
    MIN_VOLTAGE     = Voltage_05V
    MAX_VOLTAGE     = Voltage_20V
    SHORT_TO_GROUND = 0xFFFFFFFE
    VOLTAGE_OFF     = 0xFFFFFFFF


class RxFlags(IntFlag):
    CAN_29BIT_ID           = 0x100
    ISO15765_ADDR_TYPE     = 0x080
    ISO15765_PADDING_ERROR = 0x010
    TX_INDICATION          = 0x008
    RX_BREAK               = 0x004
    START_OF_MESSAGE       = 0x002
    TX_MSG_TYPE            = 0x001


class RxStatus(IntEnum):
    Normal      = 0x0
    RxStart     = RxFlags.START_OF_MESSAGE
    RxBreak     = RxFlags.RX_BREAK
    RxPadError  = RxFlags.ISO15765_PADDING_ERROR
    TxDone      = RxFlags.TX_INDICATION | RxFlags.TX_MSG_TYPE
    Loopback    = RxFlags.TX_MSG_TYPE


class TxFlags(IntFlag):
    SCI_TX_VOLTAGE      = 0x00800000
    SCI_MODE            = 0x00400000
    WAIT_P3_MIN_ONLY    = 0x00000200
    CAN_29BIT_ID        = 0x00000100
    ISO15765_ADDR_TYPE  = 0x00000080
    ISO15765_FRAME_PAD  = 0x00000040

    ISO15765_CAN_ID_29  = 0x00000140
    ISO15765_CAN_ID_11  = 0x00000040
    SWCAN_HV_TX         = 0x00000400
    TX_NORMAL_TRANSMIT  = 0x00000000


class IoctlID(IntEnum):
    GET_CONFIG                          = 0x01
    SET_CONFIG                          = 0x02
    READ_VBATT                          = 0x03
    FIVE_BAUD_INIT                      = 0x04
    FAST_INIT                           = 0x05
    # 0x06 unused
    CLEAR_TX_BUFFER                     = 0x07
    CLEAR_RX_BUFFER                     = 0x08
    CLEAR_PERIODIC_MSGS                 = 0x09
    CLEAR_MSG_FILTERS                   = 0x0A
    CLEAR_FUNCT_MSG_LOOKUP_TABLE        = 0x0B
    ADD_TO_FUNCT_MSG_LOOKUP_TABLE       = 0x0C
    DELETE_FROM_FUNCT_MSG_LOOKUP_TABLE  = 0x0D
    READ_PROG_VOLTAGE                   = 0x0E

    RESERVED_SAE                        = 0x0F      # through 0x7FFF

    RESERVED_SAE_J2534_2                = 0x8000    # through 0xFFFF

    RESERVED_MFG_SPECIFIC               = 0x10000   # through 0xFFFFFFFF


class IoctlNetworkLine(IntEnum):
    BUS_NORMAL  = 0
    BUS_PLUS    = 1
    BUS_MINUS   = 2


class IoctlParity(IntEnum):
    NO_PARITY   = 0
    ODD_PARITY  = 1
    EVEN_PARITY = 2


class Ioctl9141Bits(IntEnum):
    DataBits8 = 0
    DataBits7 = 1


class IoctlFiveBaudMod(IntEnum):
    ISO9141_2_14230_4   = 0
    ISO9141_InvertKey2  = 1
    ISO9141_InvertAddr  = 2
    ISO9141             = 3


class IoctlParameter(IntEnum):
    DATA_RATE           = 0x01
    # 0x02 reserved by SAE
    LOOPBACK            = 0x03
    NODE_ADDRESS        = 0x04
    NETWORK_LINE        = 0x05
    P1_MIN              = 0x06 # not to be used by application
    P1_MAX              = 0x07
    P2_MIN              = 0x08 # not to be used by application
    P2_MAX              = 0x09 # not to be used by application
    P3_MIN              = 0x0A
    P3_MAX              = 0x0B # not to be used by application
    P4_MIN              = 0x0C
    P4_MAX              = 0x0D # not to be used by application
    W0                  = 0x19
    W1                  = 0x0E
    W2                  = 0x0F
    W3                  = 0x10
    W4                  = 0x11
    W5                  = 0x12
    TIDLE               = 0x13
    TINIL               = 0x14
    TWUP                = 0x15
    PARITY              = 0x16
    BIT_SAMPLE_POINT    = 0x17
    SYNC_JUMP_WIDTH     = 0x18
    T1_MAX              = 0x1A
    T2_MAX              = 0x1B
    T3_MAX              = 0x24
    T4_MAX              = 0x1C
    T5_MAX              = 0x1D
    ISO15765_BS         = 0x1E
    ISO15765_STMIN      = 0x1F
    BS_TX               = 0x22
    STMIN_TX            = 0x23
    DATA_BITS           = 0x20
    FIVE_BAUD_MOD       = 0x21
    ISO15765_WFT_MAX    = 0x25


class PASSTHRU_MSG(ct.Structure):
    _fields_ = [
        ("_ProtocolID"       , ct.c_ulong),
        ("_RxStatus"         , ct.c_ulong),
        ("_TxFlags"          , ct.c_ulong),
        ("Timestamp"         , ct.c_ulong),
        ("DataSize"          , ct.c_ulong),
        ("ExtraDataIndex"    , ct.c_ulong),
        ("_Data"             , ct.c_ubyte*4128),
    ]

    def __init__(self, *args, **kwargs):
        """Initializer.

        To initialize a message for transmission, use the optional
        ``tx_flags`` and ``data`` keywords to initialize the message.

        Otherwise, for a dummy message container to be used for receive
        functions, initialize with no arguments or keywords.

        Args:
            protocol (:class:`.ProtocolID`):
                Protocol that is used by this message.
            tx_flags (:class:`.TxFlags`):
                Flags to be specified when creating a transmit message.
                Defaults to :data:`TxFlags.TX_NORMAL_TRANSMIT`
            data (bytes):
                Raw message byte data.
        """

        # empty initializer
        if not args and not kwargs:
            super(PASSTHRU_MSG, self).__init__()

        # standard initializer
        else:
            protocol = args[0]
            tx_flags = kwargs.pop('tx_flags', TxFlags.TX_NORMAL_TRANSMIT)
            data = kwargs.pop('data', b'')

            data_arr = (ct.c_ubyte*4128)(*data)
            super(PASSTHRU_MSG, self).__init__(
                protocol, 0x0, tx_flags, 0, len(data), len(data), data_arr
            )

    @property
    def ProtocolID(self):
        return ProtocolID(self._ProtocolID)

    @property
    def RxStatus(self):
        return RxStatus(self._RxStatus)

    @property
    def TxFlags(self):
        return TxFlags(self._TxFlags)

    @property
    def Timestamp(self):
        return self.Timestamp

    @property
    def DataSize(self):
        return self.DataSize

    @property
    def ExtraDataIndex(self):
        return self.ExtraDataIndex

    @property
    def Data(self):
        return bytes(self._Data[:self.ExtraDataIndex])

    @property
    def ExtraData(self):
        if self.ExtraDataIndex == self.DataSize:
            return b''
        else:
            return bytes(
                self._Data[self.ExtraDataIndex:self.DataSize]
            )


class SCONFIG(ct.Structure):
    """Ioctl interface config parameter structure.

    Initialize with :class:`.IoctlParameter`, ``int`` arguments.
    """

    _fields_ = [
        ("_Parameter", ct.c_ulong),
        ("Value"     , ct.c_ulong),
    ]

    @property
    def Parameter(self):
        return IoctlParameter(self._Parameter)


class SCONFIG_LIST(ct.Structure):
    _fields_ = [
        ("NumOfParams"  , ct.c_ulong),
        ("ConfigPtr"    , ct.POINTER(SCONFIG)),
    ]

    def __init__(self, sconfig_arr):
        """Initializer.

        Initialize with a ``list`` of :class:`.SCONFIG` instances.
        """
        Config = (SCONFIG*len(sconfig_arr))(*sconfig_arr)
        super(SCONFIG_LIST, self).__init__(
            len(sconfig_arr), ct.cast(Config, ct.POINTER(SCONFIG))
        )

    @property
    def Config(self):
        return [self.ConfigPtr[x] for x in range(self.NumOfParams)]


class SBYTE_ARRAY(ct.Structure):
    _fields_ = [
        ("NumOfBytes"   , ct.c_ulong),
        ("BytePtr"      , ct.c_char_p),
    ]

    def __init__(self, byte_arr=b'\x00'):
        """Initializer.

        Initialize with a ``bytes`` or ``bytearray``.
        """
        super(SBYTE_ARRAY, self).__init__(len(byte_arr), byte_arr)
