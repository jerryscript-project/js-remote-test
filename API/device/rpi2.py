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
import connection
import os
import json

from API.common import console, paths, utils


class Device(base.DeviceBase):
    '''
    Device class for the rpi2 board.
    '''
    def __init__(self, options):
        super(self.__class__, self).__init__('rpi2', remote_path=options.remote_path)

        self.ssh = connection.sshcom.Connection(options)

    def init_os(self):
        '''
        Initialize the used OS.
        '''
        return os.linux.OperatingSystem()

    def install_dependencies(self):
        '''
        Install dependencies of the board.
        '''
        pass

    def flash(self, app):
        '''
        Send the application and the testsuite to the device with SFTP.
        '''
        lpath_app = app.get_image()
        lpath_testsuite = utils.make_archive(app.get_test_dir(), 'tar')

        rpath_app = utils.join(self.remote_path, app.get_cmd())
        rpath_testsuite = utils.join(self.remote_path, 'test.tar')

        # Freya cross build.
        utils.copy_file(utils.join(paths.TOOLS_PATH, 'freya-cross-build.sh'), paths.FREYA_PATH)
        utils.execute(paths.FREYA_PATH, './freya-cross-build.sh')

        freya_dir = utils.join(paths.FREYA_PATH, 'valgrind_freya')
        lpath_freya = utils.make_archive(freya_dir, 'tar')
        rpath_freya = utils.join(self.remote_path, 'valgrind_freya.tar')

        lpath_resources = utils.make_archive(paths.RESOURCES_PATH, 'tar')
        rpath_resources = utils.join(self.remote_path, 'resources.tar')

        self.ssh.open()

        # Clean up in the remote folder.
        self.ssh.exec_command('rm -f ' + rpath_app)
        self.ssh.exec_command('rm -f ' + rpath_testsuite)
        self.ssh.exec_command('rm -f ' + rpath_freya)
        self.ssh.exec_command('rm -f ' + rpath_resources)
        self.ssh.exec_command('rm -rf ' + self.get_test_path())

        # Send the application, the testsuite, the valgrind and the resource files.
        self.ssh.send_file(lpath_app, rpath_app)
        self.ssh.send_file(lpath_testsuite, rpath_testsuite)
        self.ssh.send_file(lpath_freya, rpath_freya)
        self.ssh.send_file(lpath_resources, rpath_resources)

        # Let the iotjs to be runnable and extract the tests and valgrind files.
        self.ssh.exec_command('chmod 770 ' + rpath_app)
        self.ssh.exec_command('mkdir ' + self.get_test_path())
        self.ssh.exec_command('mkdir ' + utils.join(self.remote_path, 'valgrind_freya'))
        self.ssh.exec_command('tar -xmf ' + rpath_testsuite + ' -C ' + self.get_test_path())
        self.ssh.exec_command('tar -xmf ' + rpath_freya + ' -C ' + utils.join(self.remote_path, 'valgrind_freya'))
        self.ssh.exec_command('tar -xmf ' + rpath_resources + ' -C ' + self.remote_path)

    def reset(self):
        '''
        Since the SSH library stops the process in case of timeout, don't need any reset.
        '''
        pass

    def execute(self, app, args=[]):
        '''
        Run commands for the given app on the board.
        '''
        command_template = 'python {root}/tester.py --cwd {cwd} --cmd {app} --testfile {file}'

        command = command_template.format(root=self.remote_path,
                                          cwd=self.get_test_path(),
                                          app=utils.join(self.remote_path, app.get_cmd()),
                                          file=''.join(args))

        stdout = self.ssh.exec_command(command)

        # Since the stdout is a JSON text, parse it.
        result = json.loads(stdout)

        # Make HTML friendly stdout.
        result['output'] = result['output'].rstrip('\n').replace('\n', '<br>')

        return result
