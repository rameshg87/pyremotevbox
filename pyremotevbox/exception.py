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


class PyRemoteVBoxException(Exception):

    message = "An exception occured in PyRemoteVBox Module."

    def __init__(self, message=None):
        super(PyRemoteVBoxException, self).__init__(message)


class VmInWrongPowerState(Exception):

    message = ("Operation '%(operation)s' cannot be performed when "
               "vm is %(state)s.")

    def __init__(self, **kwargs):
        message = self.message % kwargs
        super(VmInWrongPowerState, self).__init__(message)

