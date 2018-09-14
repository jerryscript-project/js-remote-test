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

import json
from threading import Thread

from jstest.common import console
from jstest.testrunner.devices.device_base import RemoteDevice
from jstest.testrunner.devices.connections.sshcom import SSHConnection
from jstest.testrunner import utils as testrunner_utils


class SSHDevice(RemoteDevice):
    '''
    Common super class for ssh devices.
    '''
    def __init__(self, env, os):
        self.user = env.options.username
        self.ip = env.options.ip
        self.port = env.options.port
        RemoteDevice.__init__(self, env, os)

        data = {
            'username': self.user,
            'ip': self.ip,
            'port': self.port,
            'timeout': env.options.timeout
        }

        self.channel = SSHConnection(data)
        self.workdir = env.options.remote_workdir

    def check_args(self):
        '''
        Check that all the arguments are established.
        '''
        if not self.workdir:
            console.fail('Please use --remote-workdir for the device.')
        if not self.ip:
            console.fail('Please define the IP address of the device.')
        if not self.user:
            console.fail('Please define the username of the device.')

        if self.workdir == '/':
            console.fail('Please do not use the root folder as test folder.')

    def execute(self, testset, test):
        '''
        Run commands for the given app on the board.

        FIXME: Remove the external tester.py to eliminate code duplications.
               Instead, this function should send commands to the device.
        '''
        self.login()

        template = 'python %s/tester.py --cwd %s --cmd %s --testfile %s'
        # Absolute path to the test folder.
        testdir = '%s/tests' % self.workdir
        # Absolute path to the test file.
        testfile = '%s/%s/%s' % (testdir, testset, test['name'])
        # Absolute path to the application.
        # Create the command that the device will execute.
        if self.device == 'rpi2':
            apps = {
                'iotjs': '%s/iotjs' % self.workdir,
                'jerryscript': '%s/jerry' % self.workdir
            }
            command = template % (self.workdir, testdir, apps[self.app], testfile)
        else:
            iotjs = '%s/iotjs' % self.workdir
            command = template % (self.workdir, testdir, iotjs, testfile)

        if self.env.options.no_memstat:
            command += ' --no-memstat'

        if self.env.options.coverage and self.app == 'iotjs':
            port = testrunner_utils.read_port_from_url(self.env.options.coverage)
            command += ' --coverage-port %s' % port

            # Start the client script on a different thread for coverage.
            client_thread = Thread(target=testrunner_utils.run_coverage_script,
                                   kwargs={'env' :self.env})
            client_thread.daemon = True
            client_thread.start()

        stdout = self.channel.exec_command(command)

        # Since the stdout is a JSON text, parse it.
        result = json.loads(stdout)
        # Make HTML friendly stdout.
        result['output'] = result['output'].rstrip('\n').replace('\n', '<br>')

        self.logout()

        return result
