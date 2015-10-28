# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.


import exception
import time

from VirtualBox_client import vboxServiceLocator
from VirtualBox_client import IWebsessionManager_logonRequestMsg
from VirtualBox_client import IVirtualBox_getVersionRequestMsg
from VirtualBox_client import IVirtualBox_findMachineRequestMsg
from VirtualBox_client import IWebsessionManager_getSessionObjectRequestMsg
from VirtualBox_client import IMachine_launchVMProcessRequestMsg
from VirtualBox_client import ISession_getConsoleRequestMsg
from VirtualBox_client import IConsole_powerDownRequestMsg
from VirtualBox_client import ISession_unlockMachineRequestMsg
from VirtualBox_client import IMachine_lockMachineRequestMsg
from VirtualBox_client import IManagedObjectRef_releaseRequestMsg
from VirtualBox_client import IVirtualBox_getMachineStatesRequestMsg
from VirtualBox_client import IMachine_getBootOrderRequestMsg
from VirtualBox_client import IMachine_setBootOrderRequestMsg
from VirtualBox_client import ISession_getMachineRequestMsg
from VirtualBox_client import IMachine_saveSettingsRequestMsg
from VirtualBox_client import IMachine_attachDeviceRequestMsg
from VirtualBox_client import IMachine_detachDeviceRequestMsg
from VirtualBox_client import IVirtualBox_openMediumRequestMsg
from VirtualBox_client import IMachine_getFirmwareTypeRequestMsg
from VirtualBox_client import IMachine_setFirmwareTypeRequestMsg
from VirtualBox_client import IMachine_getMediumRequestMsg
from VirtualBox_client import IMedium_getLocationRequestMsg


STATE_POWERED_OFF = 'PoweredOff'
STATE_POWERED_ON = 'Running'
STATE_ERROR = 'Error'

DEVICE_NETWORK = 'Network'
DEVICE_FLOPPY = 'Floppy'
DEVICE_CDROM = 'DVD'
DEVICE_DISK = 'HardDisk'

LOCKTYPE_SHARED = 1
LOCKTYPE_WRITE = 2

ACCESS_READONLY = 1
ACCESS_READWRITE = 2

FIRMWARE_BIOS = 'BIOS'
FIRMWARE_EFI = 'EFI'

DEVICE_TO_CONTROLLER_MAP = {
                            DEVICE_DISK: 'SATA',
                            DEVICE_FLOPPY: 'SATA',
                            DEVICE_CDROM: 'IDE'
                           }


class VirtualBoxHost:

    def __init__(self, **kwargs):

        host = kwargs.get('host', '10.0.2.2')
        username = kwargs.get('username', '')
        password = kwargs.get('password', '')
        port = kwargs.get('port', 18083)

        url = "http://%(host)s:%(port)s" % {'host': host, 'port': port}

        self.port = vboxServiceLocator().getvboxServicePort(url)

        if not (host):
            raise exception.InvalidInput("'host' is missing")

        req = IWebsessionManager_logonRequestMsg()
        req._this = None
        req._username = username
        req._password = password
        val = self.run_command('IWebsessionManager_logon', req)

        self.handle = val._returnval


    def run_command(self, command, request):

        method = getattr(self.port, command)
        try:
            return method(request)
        except Exception as e:
            raise exception.PyRemoteVBoxException(e)


    def get_version(self):

        req = IVirtualBox_getVersionRequestMsg()
        req._this = self.handle
        val = self.run_command('IVirtualBox_getVersion', req)
        return val._returnval

    def find_vm(self, vmname):

        req = IVirtualBox_findMachineRequestMsg()
        req._this = self.handle
        req._nameOrId = vmname
        val = self.run_command('IVirtualBox_findMachine', req)
        return VirtualBoxVm(self, val._returnval)

    def _open_medium(self, device_type, location):

        req = IVirtualBox_openMediumRequestMsg()
        req._this = self.handle
        req._location = location
        req._deviceType = device_type
        req._accessMode = ACCESS_READONLY
        req._forceNewUuid = False

        val = self.run_command('IVirtualBox_openMedium', req)
        return val._returnval

    def _get_medium_location(self, medium_id):

        req = IMedium_getLocationRequestMsg()
        req._this = medium_id
        val = self.run_command('IMedium_getLocation', req)
        return val._returnval

class VirtualBoxVm:

    def __init__(self, virtualboxhost, handle):

        self.host = virtualboxhost
        self.handle = handle


    def get_power_status(self):

        req = IVirtualBox_getMachineStatesRequestMsg()
        req._this = self.host.handle
        req._machines = [self.handle]
        val = self.host.run_command('IVirtualBox_getMachineStates', req)
        state = val._returnval[0]
        if state not in [STATE_POWERED_OFF, STATE_POWERED_ON]:
            return STATE_ERROR
        return state


    def get_boot_device(self, position=1):

        req = IMachine_getBootOrderRequestMsg()
        req._this = self.handle
        req._position = position
        val = self.host.run_command('IMachine_getBootOrder', req)
        return val._returnval


    def _get_session_id(self):

        req = IWebsessionManager_getSessionObjectRequestMsg()
        req._this = None
        req._refIVirtualBox = self.host.handle
        val = self.host.run_command('IWebsessionManager_getSessionObject', req)
        session_id = val._returnval
        return session_id


    def _lock_machine(self, session_id, lock_type=LOCKTYPE_SHARED):

        req = IMachine_lockMachineRequestMsg()
        req._this = self.handle
        req._session = session_id
        req._lockType = lock_type
        val = self.host.run_command('IMachine_lockMachine', req)


    def _get_mutable_machine(self, session_id):

        # Lock machine
        self._lock_machine(session_id, LOCKTYPE_WRITE)

        # Get mutable machine
        req = ISession_getMachineRequestMsg()
        req._this = session_id
        val = self.host.run_command('ISession_getMachine', req)
        mutable_machine_id = val._returnval
        return mutable_machine_id


    def _save_settings(self, mutable_machine_id):

        req = IMachine_saveSettingsRequestMsg()
        req._this = mutable_machine_id
        val = self.host.run_command('IMachine_saveSettings', req)


    def _unlock_machine(self, session_id):

        req = ISession_unlockMachineRequestMsg()
        req._this = session_id
        val = self.host.run_command('ISession_unlockMachine', req)


    def attach_device(self, device_type, location):

        if self.get_power_status() == STATE_POWERED_ON:
            raise exception.VmInWrongPowerState(operation='attach_device',
                                                state='powered on')

        try:
            self.detach_device(device_type)
        except Exception:
            pass

        # Get mutable machine
        session_id = self._get_session_id()

        controller_name = DEVICE_TO_CONTROLLER_MAP[device_type]
        medium_id = self.host._open_medium(device_type, location)

        mutable_machine_id = self._get_mutable_machine(session_id)
        try:
            req = IMachine_attachDeviceRequestMsg()
            req._this = mutable_machine_id
            req._name = controller_name
            req._controllerPort=0
            req._device = 0
            req._type = device_type
            req._medium = medium_id

            val = self.host.run_command('IMachine_attachDevice', req)

            # Save settings and unlock
            self._save_settings(mutable_machine_id)

        finally:
            self._unlock_machine(session_id)


    def detach_device(self, device_type):

        if self.get_power_status() == STATE_POWERED_ON:
            raise exception.VmInWrongPowerState(operation='detach_device',
                                                state='powered on')

        session_id = self._get_session_id()

        controller_name = DEVICE_TO_CONTROLLER_MAP[device_type]

        mutable_machine_id = self._get_mutable_machine(session_id)
        try:
            req = IMachine_detachDeviceRequestMsg()
            req._this = mutable_machine_id
            req._name = controller_name
            req._controllerPort=0
            req._device = 0
            req._type = device_type

            val = self.host.run_command('IMachine_detachDevice', req)

            # Save settings and unlock
            self._save_settings(mutable_machine_id)

        finally:
            self._unlock_machine(session_id)


    def get_attached_device(self, device_type):

        session_id = self._get_session_id()

        controller_name = DEVICE_TO_CONTROLLER_MAP[device_type]

        req = IMachine_getMediumRequestMsg()
        req._this = self.handle
        req._name = controller_name
        req._controllerPort=0
        req._device = 0

        val = None
        try:
            val = self.host.run_command('IMachine_getMedium', req)
        except exception.PyRemoteVBoxException as e:
            if 'No storage device attached' in str(e):
                return None

        return self.host._get_medium_location(val._returnval)


    def set_boot_device(self, device, position=1):

        if self.get_power_status() == STATE_POWERED_ON:
            raise exception.VmInWrongPowerState(operation='set_boot_device',
                                                state='powered on')

        # Get mutable machine
        session_id = self._get_session_id()
        mutable_machine_id = self._get_mutable_machine(session_id)

        # Change boot order
        req = IMachine_setBootOrderRequestMsg()
        req._this = mutable_machine_id
        req._position = position
        req._device = device
        val = self.host.run_command('IMachine_setBootOrder', req)

        # Save settings and unlock
        self._save_settings(mutable_machine_id)
        self._unlock_machine(session_id)


    def get_firmware_type(self):

        session_id = self._get_session_id()

        req = IMachine_getFirmwareTypeRequestMsg()
        req._this = self.handle

        val = self.host.run_command('IMachine_getFirmwareType', req)
        return val._returnval


    def set_firmware_type(self, firmware_type):

        if self.get_power_status() == STATE_POWERED_ON:
            raise exception.VmInWrongPowerState(operation='set_firmware_type',
                                                state='powered on')

        session_id = self._get_session_id()

        mutable_machine_id = self._get_mutable_machine(session_id)
        try:
            req = IMachine_setFirmwareTypeRequestMsg()
            req._this = mutable_machine_id
            req._firmwareType = firmware_type

            val = self.host.run_command('IMachine_setFirmwareType', req)

            # Save settings and unlock
            self._save_settings(mutable_machine_id)

        finally:
            self._unlock_machine(session_id)


    def start(self, vm_type="gui"):

        if self.get_power_status() == STATE_POWERED_ON:
            return

        session_id = self._get_session_id()

        req = IMachine_launchVMProcessRequestMsg()
        req._this = self.handle
        req._type = vm_type
        req._environment = ""
        req._session = session_id
        val=self.host.run_command('IMachine_launchVMProcess', req)

        for i in range(1, 10):
            time.sleep(2)
            try:
                self._unlock_machine(session_id)
                break
            except Exception:
                pass
        else:
            raise exception.PyRemoteVBoxException("Failed to unlock machine "
                                                  "after 10 attempts.")


    def stop(self):

        if self.get_power_status() == STATE_POWERED_OFF:
            return

        session_id = self._get_session_id()
        self._lock_machine(session_id, LOCKTYPE_SHARED)

        req = ISession_getConsoleRequestMsg()
        req._this = session_id
        val = self.host.run_command('ISession_getConsole', req)
        console_id = val._returnval

        req = IConsole_powerDownRequestMsg()
        req._this = console_id
        val = self.host.run_command('IConsole_powerDown', req)

        # Give a while for VirtualBox to unlock the machine.
        time.sleep(1)

