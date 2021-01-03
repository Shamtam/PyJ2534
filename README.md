# PyJ2534
A complete J2534 Pass-Thru DLL wrapper implementation

Developed and tested with Python 3.8.7 32-bit on Win10 x64.

# Usage

## Enumerating interfaces
```
>>> from PyJ2534 import get_interfaces, load_interface
>>> get_interfaces()
{'OpenPort 2.0 J2534 ISO/CAN/VPW/PWM': 'C:\\WINDOWS\\SysWOW64\\op20pt32.dll'}

```

## Loading a DLL and opening a device
```
>>> from PyJ2534 import get_interfaces, load_interface
>>> ifaces = get_interfaces()
>>> iface_names, iface_paths = list(ifaces.keys()), list(ifaces.values())
>>> iface = load_interface(iface_paths[0])
>>> _devID = iface.PassThruOpen()
>>> _devID
c_ulong(1)
```

## Opening a channel
```
>>> from PyJ2534 import *
>>> _chanID = iface.PassThruConnect(_devID, ProtocolID.ISO9141, ProtocolFlags.ISO9141_NO_CHECKSUM, 9600)
>>> _chanID
c_ulong(3)
```

## Ioctl `GET_CONFIG`
```
>>> iface.PassThruIoctlGetConfig(_chanID, [IoctlParameter.DATA_RATE, IoctlParameter.LOOPBACK, IoctlParameter.P1_MAX])
{<IoctlParameter.DATA_RATE: 1>: 9600, <IoctlParameter.LOOPBACK: 3>: 0, <IoctlParameter.P1_MAX: 7>: 40}
```

## Ioctl `SET_CONFIG`
```
>>> iface.PassThruIoctlSetConfig(_chanID, {IoctlParameter.DATA_RATE: 4800, IoctlParameter.P1_MAX: 100})
>>> iface.PassThruIoctlGetConfig(_chanID, [IoctlParameter.DATA_RATE, IoctlParameter.P1_MAX])
{<IoctlParameter.DATA_RATE: 1>: 4800, <IoctlParameter.P1_MAX: 7>: 100}
```

# Thanks
Thanks to @keenanlaws and @kekelele for their initial implementations

keenanlaws: https://github.com/keenanlaws/Python-J2534-Interface
kekelele: https://github.com/kekelele/python_j2534
