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

import binascii
import socket

from jstest.common import console, utils


def genromfs(**params):
    '''
    Create a romfs_img from the source directory that is
    converted to a header (byte array) file. Finally, add
    a `const` modifier to the byte array to be the data
    in the Read Only Memory.
    '''
    src = params['args'][0]
    dst = params['args'][1]

    romfs_img = utils.join(params['cwd'], 'romfs_img')

    utils.execute(params['cwd'], 'genromfs', ['-f', romfs_img, '-d', src])
    utils.execute(params['cwd'], 'xxd', ['-i', 'romfs_img', dst])
    utils.execute(params['cwd'], 'sed', ['-i', 's/unsigned/const\ unsigned/g', dst])

    utils.remove_file(romfs_img)


def config_internet(**params):
    '''
    Replace the Internet related symbols to concrete values in the NuttX config file.
    '''
    # IP is not provided, so the symbol is not resolved. In this case there is no
    # need to execute this function because serial config file is used.
    if params['args'][0] == '(ip-addr is not found)':
        return

    cwd = params['cwd']

    ip_addr = binascii.hexlify(socket.inet_aton(params['args'][0]))
    netmask = binascii.hexlify(socket.inet_aton(params['args'][1]))
    gateway = binascii.hexlify(socket.inet_aton(params['args'][2]))

    utils.execute(cwd, 'sed', ['-ie', 's/YOUR_IP_ADDR/0x%s/g' % ip_addr, 'defconfig'])
    utils.execute(cwd, 'sed', ['-ie', 's/YOUR_NETMASK/0x%s/g' % netmask, 'defconfig'])
    utils.execute(cwd, 'sed', ['-ie', 's/YOUR_ROUTER_ADDR/0x%s/g' % gateway, 'defconfig'])


def push_environment(**params):
    '''
    Define the environment variables globally, not just for a process.
    '''
    for key, value in params['env'].iteritems():
        utils.define_environment(key, value)


def print_message(**params):
    '''
    Print a message to the screen.
    '''
    console.log(params['args'][0])


NATIVES = {
  'print': print_message,
  'genromfs': genromfs,
  'config_internet': config_internet,
  'push_environment': push_environment
}


def get(command):
    '''
    Get a pointer to the given buil-in function.
    '''
    if command not in NATIVES:
        console.fail('%s built-in function is not found.')

    return NATIVES[command]
