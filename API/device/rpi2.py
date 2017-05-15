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

import base

import json
import paramiko

from ..common import console
from ..common import paths
from ..common import utils


class Device(base.DeviceBase):
    '''
    Device class for the stm32f4-discovery board.
    '''
    def __init__(self):
        super(self.__class__, self).__init__('rpi2')

        # Create SSH connection to the device.
        self.client = paramiko.client.SSHClient()
        self.client.load_system_host_keys()

        self.connected = False

    def install_dependencies(self):
        '''
        Install dependencies of the board.
        '''
        pass

    def flash(self, os):
        '''
        Send the application and the testsuite to the device with SFTP.
        '''
        if not self.connected:
            # Note: add your SSH key to the Raspberry Pi 2 known host file
            # to avoid getting password.
            self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            self.client.connect(self.address, username=self.username)

        app = os.get_app()

        local_app = app.get_image()
        local_testsuite = utils.make_archive(app.get_test_dir(), 'tar')

        remote_app = utils.join(self.root_path, app.get_cmd())
        remote_testsuite = utils.join(self.root_path, 'test.tar')

        # Clean up in the remote folder.
        self.client.exec_command('rm -f %s' % remote_app)
        self.client.exec_command('rm -f %s' % remote_testsuite)
        self.client.exec_command('rm -rf %s' % self.get_test_path())

        # Get an SFTP session to send the application and the test files to the device.
        sftp = self.client.open_sftp()

        try:
            sftp.put(local_app, remote_app)
            sftp.put(local_testsuite, remote_testsuite)
        except Exception as e:
            console.fail('[Failed - sftp] %s' % str(e))

        sftp.close()

        # Prepare for the testing.
        self.client.exec_command('chmod 770 %s' % remote_app)
        self.client.exec_command('mkdir %s' % self.get_test_path())
        self.client.exec_command('tar -xf %s -C %s' % (remote_testsuite, self.get_test_path()))

    def execute(self, cmd, args=[]):
        '''
        Run the given command on the board.
        '''
        command_template = 'python {root}/tester.py --cwd {cwd} --cmd {app} --testfile {file}'

        command = command_template.format(root=self.root_path,
                                          cwd=self.get_test_path(),
                                          app=utils.join(self.root_path, cmd),
                                          file=''.join(args))

        stdin, stdout, stderr = self.client.exec_command(command)

        # Since the stdout is a JSON text, parse it.
        result = json.loads(stdout.readline())

        # Make HTML friendly stdout.
        stdout = result['output'].rstrip('\n').replace('\n', '<br>')

        return result['exitcode'], stdout, result['mempeak']
