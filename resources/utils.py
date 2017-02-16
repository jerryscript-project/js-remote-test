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

import json
import os
import time

from . import executor
from . import paths


def read_file(filename):
    '''
    Read a JSON file and provide the content as dictionary.
    '''
    with open(filename, 'r') as filename_p:
        data = filename_p.read()

    return json.loads(data)


def write_file(filename, data, serializer=None):
    '''
    Write a JSON file from the given data.
    '''
    with open(filename, 'w') as filename_p:
        json.dump(data, filename_p, cls=serializer)

        # Add a newline to the end of the line.
        filename_p.write('\n')


def shoud_test():
    '''
    Skip testing if no new commit.

    Read the latest testresult iotjs hash and compare it to the current one.
    '''
    index_file = os.path.join(paths.WEB_DATA_PATH, 'index.json')

    if not executor.exists(index_file):
        return True

    iotjs_info = get_submodule_info(paths.IOTJS_PATH)
    iotjs_hash = iotjs_info['commit']

    filenames = read_file(index_file)
    testresult = os.path.join(paths.WEB_DATA_PATH, filenames[0])
    testresults = read_file(testresult)

    if testresults['submodules']['iotjs']['commit'] == iotjs_hash:
        return False

    return True


def get_current_date():
    '''
    Get the current date in standardized format.
    '''
    return time.strftime('%Y-%m-%dT%H:%M:%SZ')


def get_submodule_info(path):
    '''
    Get last commit information about the submodules.
    '''
    output = executor.run_cmd(path, 'git', ['log', '-1'])

    info = {
        'message': None,
        'commit': None,
        'author': None,
        'date': None
    }

    for line in output.splitlines():
        if line.startswith('commit'):
            info['commit'] = line.split(' ')[1]

        elif line.startswith('Author'):
            info['author'] = ' '.join(line.split(' ')[1:])

        elif line.startswith('Date'):
                info['date'] = ' '.join(line.split(' ')[1:])

        else:
            # Save only the header of the commit message.
            info['message'] = line
            break

    return info


def get_binary_info():
    '''
    Get binary size information from iotjs.
    '''
    result = {
        'rodata': '0',
        'total': '0',
        'text': '0',
        'data': '0',
        'bss': '0'
    }

    size_cmd = 'arm-linux-gnueabi-size'
    size_args = ['-A', 'iotjs']

    output = executor.run_cmd(paths.IOTJS_BUILD_PATH, size_cmd, size_args)

    for line in output.splitlines():
        if line.startswith('.text'):
            result['text'] = line.split(' ')[1]

        elif line.startswith('.data'):
            result['data'] = line.split(' ')[1]

        elif line.startswith('.rodata'):
            result['rodata'] = line.split(' ')[1]

        elif line.startswith('.bss'):
            result['bss'] = line.split(' ')[1]

    binary_size = os.path.getsize(paths.IOTJS_BUILD_PATH + '/iotjs')
    result['total'] = str(binary_size)

    return result


def publish_data(filename):
    '''
    Publish testresults to the web.
    '''
    executor.run_cmd(paths.WEB_PATH, 'git', ['add', 'data/' + filename])
    executor.run_cmd(paths.WEB_PATH, 'git', ['add', '-u'])
    executor.run_cmd(paths.WEB_PATH, 'git', ['commit', '--amend', '--no-edit'])
    executor.run_cmd(paths.WEB_PATH, 'git', ['push', '-f'])
