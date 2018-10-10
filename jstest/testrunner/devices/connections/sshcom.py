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
        self.prompt = device_info['prompt']

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
                         password=self.password, look_for_keys=not bool(self.password))

        self.chan = self.ssh.invoke_shell()
        self.read_until(self.prompt)

    def close(self):
        '''
        Close the ssh port.
        '''
        self.ssh.close()

    def exec_command(self, cmd):
        '''
        Send command over the serial port.
        '''
        self.chan.settimeout(self.timeout)
        try:
            self.send(cmd)
            data = self.read_until(self.prompt)
        except socket.timeout:
            raise TimeoutException

        return data

    def send(self, cmd):
        '''
        Send data over the ssh channel.
        '''
        self.chan.send(cmd + '\n')

    def read_until(self, expected):
        '''
        Receive data from the server until we get the expected pattern.
        '''
        temp = ''
        while expected not in temp:
            temp += self.chan.recv(1)

        temp = temp.split('\r\n')
        try:
            temp.pop()
            return temp[-1]
        except IndexError:
            pass
