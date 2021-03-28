===========
Quick-start
===========

Use ``import PyJ2534`` to import all predefined enumerations along with two
helper functions to enumerate and instantiate a DLL wrapper.

Enumerating interfaces
----------------------
Use :func:`.get_interfaces` to enumerate all registered J2534 interfaces.

>>> import PyJ2534
>>> ifaces = PyJ2534.get_interfaces()
>>> ifaces
{'OpenPort 2.0 J2534 ISO/CAN/VPW/PWM': 'C:\\WINDOWS\\SysWOW64\\op20pt32.dll'}


Loading a DLL and opening a device
----------------------------------
Use :func:`.load_interface` to create a J2534 DLL wrapper instance.

>>> iface_names, iface_paths = list(ifaces.keys()), list(ifaces.values())
>>> iface = load_interface(iface_paths[0])
>>> iface
<J2534Dll: C:\WINDOWS\SysWOW64\op20pt32.dll>


Opening the device
------------------
>>> _devID = iface.PassThruOpen()
>>> _devID
c_ulong(1)


Opening a channel
-----------------
Open a channel using the predefined enumerations for protocols/flags (see
:class:`.ProtocolID` and :class:`.ProtocolFlags`).

>>> _chanID = iface.PassThruConnect(_devID, ProtocolID.ISO9141, ProtocolFlags.ISO9141_NO_CHECKSUM, 9600)
>>> _chanID
c_ulong(3)


Using Ioctl get/set
-------------------
Use :class:`.IoctlParameter` with the corresponding get/set functions.

``GET_CONFIG``
^^^^^^^^^^^^^^
Pass a list of :class:`.IoctlParameter` to query.

>>> iface.PassThruIoctlGetConfig(_chanID, [IoctlParameter.DATA_RATE, IoctlParameter.LOOPBACK, IoctlParameter.P1_MAX])
{<IoctlParameter.DATA_RATE: 1>: 9600, <IoctlParameter.LOOPBACK: 3>: 0, <IoctlParameter.P1_MAX: 7>: 40}


``SET_CONFIG``
^^^^^^^^^^^^^^
Pass a dictionary with mapping each :class:`.IoctlParameter` to its desired value.

>>> iface.PassThruIoctlSetConfig(_chanID, {IoctlParameter.DATA_RATE: 4800, IoctlParameter.P1_MAX: 100})
>>> iface.PassThruIoctlGetConfig(_chanID, [IoctlParameter.DATA_RATE, IoctlParameter.P1_MAX])
{<IoctlParameter.DATA_RATE: 1>: 4800, <IoctlParameter.P1_MAX: 7>: 100}
