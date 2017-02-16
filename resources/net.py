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

import re
import signal
import telnetlib

from . import console
from . import paths


class TimeoutException(Exception):
    '''
    A basic timeout exception.
    '''
    pass


def alarm_handler(signum, frame):
    '''
    Throw exception when alarm happens.
    '''
    raise TimeoutException


class Telnet(object):
    '''
    Test specific telnet class.
    '''
    def __init__(self, ip_addr, timeout):
        self.device_ip = ip_addr
        self.timeout = timeout
        self.outputs = {}
        self.telnet = telnetlib.Telnet()
        self.is_alive = False

        signal.signal(signal.SIGALRM, alarm_handler)

    def close_connection(self):
        '''
        Close connection.
        '''
        self.is_alive = False

        self.telnet.close()

    def create_connection(self):
        '''
        Create connection.
        '''
        if self.is_alive:
            self.telnet.close()

        try:
            self.telnet.open(self.device_ip)
            self.telnet.read_until('nsh> ')

            self.is_alive = True

        except Exception as e:
            console.fail('[Failed - Telnet] %s.' % e.strerror)

    def run_cmd(self, cmd, args=[], timeout=None):
        '''
        Execute the given command.
        '''
        arguments = ' '.join(args).encode('utf8')

        self.telnet.write('%s %s\n' % (cmd, arguments))

        # Set a timeout and waiting for the prompt.
        signal.alarm(timeout or self.timeout)

        response = self.telnet.read_until('nsh> ')

        signal.alarm(0)

        # Eliminate unnecessary characters from the response.
        response = re.sub('\n\rnsh> ', '', response)
        response = re.sub('nsh> ', '', response)

        self.outputs[cmd] = response
