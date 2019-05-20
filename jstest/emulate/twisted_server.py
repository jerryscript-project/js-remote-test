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

import json
import os
from threading import Thread

from twisted.cred.portal import Portal
from twisted.conch.ssh.factory import SSHFactory
from twisted.internet import reactor
from twisted.conch.ssh.keys import Key
from twisted.cred.checkers import FilePasswordDB
from twisted.conch.interfaces import IConchUser
from twisted.conch.avatar import ConchUser
from twisted.conch.ssh.channel import SSHChannel
from twisted.internet.protocol import Protocol
from twisted.conch.ssh.session import SSHSessionProcessProtocol, wrapProtocol


class SimpleSession(SSHChannel):
    name = 'session'

    @staticmethod
    def set_prompt(prompt):
        SimpleSession.prompt = prompt

    #pylint: disable=invalid-name,unused-argument
    def channelOpen(self, specificData):
        self.write(SimpleSession.prompt)
    #pylint: enable=unused-argument

    def dataReceived(self, data):
        cmd = str(data)

        if 'iotjs_build_info' in cmd:
            result = {
                'builtins': {},
                'features': {},
                'stability': 'stable'
            }
        else:
            result = {
                'output': 'Hello from the emulated device',
                'memstat': {
                    'heap-system': 'n/a',
                    'heap-jerry': 'n/a',
                    'stack': 'n/a'
                },
                'exitcode': int('fail' in cmd)
            }

        self.write(json.dumps(result) + '\r\n')
        self.write(SimpleSession.prompt)

    # pylint: enable=invalid-name
    # pylint: disable=unused-argument
    def request_shell(self, data):
        protocol = Protocol()
        transport = SSHSessionProcessProtocol(self)
        protocol.makeConnection(transport)
        transport.makeConnection(wrapProtocol(protocol))
        self.client = transport
        return True

    @staticmethod
    def request_pty_req(data):
        return True
    # pylint: enable=unused-argument

class SimpleRealm(object):
    # pylint: disable=invalid-name,unused-argument
    @staticmethod
    def requestAvatar(avatar_id, mind, *interfaces):
        user = ConchUser()
        user.channelLookup['session'] = SimpleSession
        return IConchUser, user, lambda: None
    # pylint: enable=invalid-name,unused-argument

def run(device):
    '''
    Run a threaded server.
    '''
    prompts = {
        'rpi2': ':~$',
        'rpi3': ':~>'
    }
    this_dir = os.path.dirname(__file__)
    with open(os.path.join(this_dir, 'private.key')) as private_blob_file:
        private_blob = private_blob_file.read()
        private_key = Key.fromString(data=private_blob)

    with open(os.path.join(this_dir, 'public.key')) as public_blob_file:
        public_blob = public_blob_file.read()
        public_key = Key.fromString(data=public_blob)

    factory = SSHFactory()
    factory.privateKeys = {'ssh-rsa': private_key}
    factory.publicKeys = {'ssh-rsa': public_key}

    SimpleSession.set_prompt(prompts[device])
    factory.portal = Portal(SimpleRealm())
    factory.portal.registerChecker(FilePasswordDB(os.path.join(this_dir, 'ssh-passwords')))

    reactor.listenTCP(2022, factory, interface='127.0.0.1')
    thread = Thread(target=reactor.run, args=(False,))
    thread.daemon = True
    thread.start()


def stop():
    '''
    Stop the threaded server.
    '''
    reactor.callFromThread(reactor.stop)
