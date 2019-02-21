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
import subprocess


TRAVIS_BUILD_PATH = os.environ['TRAVIS_BUILD_DIR']

DOCKER_IMAGE_NAME = 'iotjs/js_remote_test:0.6'
DOCKER_NAME = 'jsremote_docker'
DOCKER_USERNAME = 'travis'
DOCKER_WORKDIR = '/home/%s' % DOCKER_USERNAME

# The path to js-remote-test in Docker.
DOCKER_JSREMOTE_PATH = DOCKER_WORKDIR + '/js-remote-test/'

# Commonly used commands and arguments.
BASE_COMMAND = ['python', '-m', 'jstest']
RELEASE_ARG = ['--buildtype', 'release']
DEBUG_ARG = ['--buildtype', 'debug']
COMMON_ARGS = ['--emulate', '--no-memstat', '--quiet']

DEVICES = ['rpi2', 'artik530', 'artik053', 'stm32f4dis']


def parse_option():
    '''
    Parse the given options.
    '''
    parser = argparse.ArgumentParser(description='JS-remote-test Travis script.')

    parser.add_argument('--check-signoff', action='store_true')
    parser.add_argument('--check-pylint', action='store_true')
    parser.add_argument('--device', choices=DEVICES, action='append')
    parser.add_argument('--app', choices=['iotjs', 'jerryscript'], action='append')

    return parser.parse_args()


def build_app(option):
    '''
    Build jerry or iotjs for the given device, both release and debug.
    '''
    app_arg = ['--app', option.app[0]]
    device_arg = ['--device', option.device[0]]

    release_command = BASE_COMMAND + app_arg + RELEASE_ARG + device_arg + COMMON_ARGS
    debug_command = BASE_COMMAND + app_arg + DEBUG_ARG + device_arg + COMMON_ARGS

    exec_docker(release_command)
    exec_docker(debug_command)


def run_docker():
    '''
    Create the Docker container where we will run the builds.
    '''
    exec_command('docker', ['run', '-dit', '--privileged',
                            '--name', DOCKER_NAME,
                            '--user', DOCKER_USERNAME,
                            '-w', DOCKER_WORKDIR,
                            '-v', '%s:%s' % (TRAVIS_BUILD_PATH, DOCKER_JSREMOTE_PATH),
                            '--env', 'PYTHONPATH=%s:$PYTHONPATH' % DOCKER_JSREMOTE_PATH,
                            '--env', 'HOME=%s' % DOCKER_WORKDIR,
                            DOCKER_IMAGE_NAME])


def exec_command(cmd, args):
    '''
    Execute the given command.
    '''
    if not args:
        args = []

    print_command('.', cmd, args)

    exitcode = subprocess.call([cmd] + args)

    if exitcode != 0:
        print('[Failed - %s] %s %s' % (exitcode, cmd, ' '.join(args)))
        exit(1)


def exec_docker(cmd):
    '''
    Execute the given command in Docker.
    '''
    exec_cmd = ' '.join(cmd)
    exec_command('docker', ['exec', '-it', DOCKER_NAME, '/bin/bash', '-c', exec_cmd])


def print_command(cwd, cmd, args):
    '''
    Helper function to print commands.
    '''
    terminal_empty = '\033[0m'
    terminal_green = '\033[1;32m'
    terminal_yellow = '\033[1;33m'

    rpath = os.path.relpath(cwd, DOCKER_JSREMOTE_PATH)
    # Resolve the current folder character to the appropriate folder name.
    if rpath == os.curdir:
        rpath = os.path.basename(os.path.abspath(os.curdir))

    cmd_info = [
        '%s[%s]' % (terminal_yellow, rpath),
        '%s%s' % (terminal_green, cmd),
        '%s%s' % (terminal_empty, ' '.join(args))
    ]

    print(' '.join(cmd_info))


def main():
    option = parse_option()

    if option.check_signoff:
        args = []
        if os.getenv('TRAVIS') is not None:
            args = ['--travis']
        exec_command('tools/check_signed_off.sh', args)

    if option.check_pylint:
        exec_command('python', ['tools/check_pylint.py'])

    if option.app and option.device:
        run_docker()
        build_app(option)


if __name__ == "__main__":
    main()
