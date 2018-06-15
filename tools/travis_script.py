#!/usr/bin/env python

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

from __future__ import print_function

import argparse
import os
import sys

from common_py.system.executor import Executor as ex

TRAVIS_BUILD_PATH = os.environ['TRAVIS_BUILD_DIR']

DOCKER_IMAGE_NAME = 'iotjs/js_remote_test:0.2'
DOCKER_NAME = 'jsremote_docker'
DOCKER_ROOT_PATH = '/root'

# The path to js-remote-test in Docker.
DOCKER_JSREMOTE_PATH = DOCKER_ROOT_PATH + '/js-remote-test/'

# Commonly used commands and arguments.
BASE_COMMAND = ['python', '-u', DOCKER_JSREMOTE_PATH + 'driver.py']
RELEASE_ARG = ['--buildtype', 'release']
DEBUG_ARG = ['--buildtype', 'debug']
COMMON_ARGS = ['--no-flash', '--no-test', '--no-memstat']

DEVICES = ['rpi2', 'artik530', 'artik053', 'stm32f4dis']

def parse_option():
    parser = argparse.ArgumentParser(
         description='JS-remote-test Travis script.')

    parser.add_argument('--check-signoff', action='store_true')
    parser.add_argument('--device', choices=DEVICES, action='append')
    parser.add_argument('--app', choices=['iotjs', 'jerryscript'], action='append')

    option = parser.parse_args()
    return option

def build_app(option):
    '''
    Build jerry or iotjs for the given device, both release and debug.
    '''
    app_arg = ['--app', option.app[0]]
    device_arg = ['--device', option.device[0]]

    # Redirect stdout to /dev/null to decrease log size.
    # FIXME make some kind of quiet option in driver.py to do this.
    release_command = BASE_COMMAND + app_arg + RELEASE_ARG + device_arg + COMMON_ARGS + ['1>/dev/null']
    debug_command = BASE_COMMAND + app_arg + DEBUG_ARG + device_arg + COMMON_ARGS + ['1>/dev/null']

    exec_docker(release_command)
    exec_docker(debug_command)

def run_docker():
    '''
    Create the Docker container where we will run the builds.
    '''
    ex.check_run_cmd('docker', ['run', '-dit', '--privileged',
                                '--name', DOCKER_NAME,
                                '-v', '%s:%s' % (TRAVIS_BUILD_PATH, DOCKER_JSREMOTE_PATH),
                                DOCKER_IMAGE_NAME])

def exec_docker(cmd):
    '''
    Execute the given command in Docker.
    '''
    exec_cmd = ' '.join(cmd)
    ex.check_run_cmd('docker', ['exec', '-it', DOCKER_NAME, '/bin/bash', '-c', exec_cmd])

if __name__ == '__main__':
    option = parse_option()

    if option.check_signoff:
        args = []
        if os.getenv('TRAVIS') is not None:
            args = ['--travis']
        ex.check_run_cmd('tools/check_signed_off.sh', args)

    if option.app and option.device:
        run_docker()
        build_app(option)
