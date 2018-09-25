# Copyright 2017-present Samsung Electronics Co., Ltd. and other contributors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import socket
import paramiko

from jstest.common.utils import TimeoutException


class SSHConnection(object):
    '''
    The serial communication wrapper.
    '''
    def __init__(self, device_info):
        self.username = device_info['username']
        self.password = device_info['password']
        self.ip = device_info['ip']
        self.port = device_info['port']
        self.timeout = device_info['timeout']
        # FIXME: the exec_command method of paramiko.client.SSHClient cannot be used with the
        # emulated ssh server.
        self._no_exec_command = device_info['_no_exec_command']

        # Note: add your SSH key to the known host file
        # to avoid getting password.
        self.ssh = paramiko.client.SSHClient()
        if not self.password:
            self.ssh.load_system_host_keys()
        self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    def open(self):
        '''
        Open the ssh port.
        '''
        self.ssh.connect(hostname=self.ip, port=self.port, username=self.username,
                         password=self.password, look_for_keys=bool(self.password))

        if self._no_exec_command:
            self.chan = self.ssh.invoke_shell()
            self.chan_file = self.chan.makefile('r')

    def close(self):
        '''
        Close the ssh port.
        '''
        self.ssh.close()

    def exec_command(self, cmd):
        '''
        Send command over the serial port.
        '''
        try:
            if self._no_exec_command:
                self.send(cmd)
                response = self.receive()

            else:
                _, stdout, _ = self.ssh.exec_command(cmd, timeout=self.timeout)

                response = stdout.readline()

        except socket.timeout:
            raise TimeoutException

        return response

    def send(self, cmd):
        '''
        Send data over the ssh channel.
        '''
        self.chan.send(cmd + '\n')

    def receive(self):
        '''
        Receive data from the ssh channel.
        '''
        try:
            return self.chan_file.readline().strip('\r\n')
        except socket.timeout:
            raise TimeoutException
