# Copyright 2018-present Samsung Electronics Co., Ltd. and other contributors
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

from jstest.common.utils import TimeoutException
from jstest.common import console

def alarm_handler(_signum, _frame):
    '''
    Throw exception when alarm happens.
    '''
    raise TimeoutException


class TelnetConnection(object):
    '''
    The telnet communication wrapper.
    '''
    def __init__(self, device_info):
        self.ip = device_info['ip']
        self.timeout = device_info['timeout']
        self.prompt = device_info['prompt']

        self.telnet = telnetlib.Telnet()

        signal.signal(signal.SIGALRM, alarm_handler)

    def open(self):
        '''
        Open the serial port.
        '''
        try:
            self.telnet.open(self.ip)
            self.telnet.read_until(self.prompt)
        except Exception as e:
            console.fail(str(e))

    def close(self):
        '''
        Close the telnet communication.
        '''
        self.telnet.close()

    def exec_command(self, cmd):
        '''
        Send command over the serial port.
        '''
        if isinstance(cmd, unicode):
            cmd = cmd.encode('utf8')
        try:
            self.telnet.write('%s\n' % cmd)
        except Exception as e:
            console.fail(str(e))

        return self._read_data()

    def _read_data(self):
        '''
        Waiting for the prompt and removing that characters from the output.
        '''
        signal.alarm(self.timeout)

        stdout = self.telnet.read_until(self.prompt)

        signal.alarm(0)

        stdout = re.sub('\n\r' + self.prompt, '', stdout)
        stdout = re.sub(self.prompt, '', stdout)

        return stdout
