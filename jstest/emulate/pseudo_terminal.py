# Copyright 2018-present Samsung Electronics Co., Ltd. and other contributors
#
# Licensed under the Apache License, Version 2.0 (the 'License');
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an 'AS IS' BASIS
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import pty
import threading
import serial


def open_pseudo_terminal(device):
    '''
    Create a pseudo terminal.
    '''
    prompts = {
        'stm32f4dis': 'nsh> ',
        'artik053': 'TASH>>'
    }
    master, slave = pty.openpty()
    thread = threading.Thread(target=_listener, args=[master, prompts[device]])
    thread.start()

    return os.ttyname(slave)


def close_pseudo_terminal(env):
    '''
    Close the pseudo terminal.
    '''
    ser = serial.Serial(port=env['info']['device_id'], baudrate=env['info']['baud'],
                        timeout=env['info']['timeout'])
    ser.write('kill_thread\n')
    ser.close()


def _listener(port, prompt):
    '''
    Listen to commands on the master device.
    '''
    while True:
        res = ''
        while not res.endswith('\n'):
            res += os.read(port, 1)
            if res == '\n':
                # When logging in to the board, accept three \n characters instead of just one.
                res += os.read(port, 2)

        if not res.endswith('\r\n'):
            res = res.replace('\n', '\r\n')

        if 'kill_thread' in res:
            return

        if 'echo $?' in res:
            output = '0'
        elif 'iotjs_build_info' in res:
            output = '{ "builtins": {}, "features": {}, "stability": "stable" }'
        else:
            output = 'Hello world from the emulated device!'

        # Output data in the expected format.
        os.write(port, res)
        os.write(port, output + '\r\n')
        os.write(port, prompt)
