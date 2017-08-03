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

import console
import json
import os
import shutil
import subprocess
import time
import re


class TimeoutException(Exception):
    '''
    Custom exception in case of timeout.
    '''
    pass


def execute(cwd, cmd, args=[], quiet=False):
    '''
    Run the given command.
    '''
    stdout = None
    stderr = None

    if quiet:
        stdout = subprocess.PIPE
        stderr = subprocess.STDOUT

    try:
        process = subprocess.Popen([cmd] + args, stdout=stdout,
                                   stderr=stderr, cwd=cwd)

        output = process.communicate()[0]
        exitcode = process.returncode

        if exitcode:
            raise Exception('Not null exit value')

        if quiet:
            output = re.sub(' +', ' ', output)
            output = re.sub('\n\n', '\n', output)
            output = re.sub('\n ', '\n', output)

        return output, exitcode

    except Exception as e:
        console.fail('[Failed - %s] %s' % (cmd, str(e)))


def generate_romfs(output_path, input_path):
    '''
    Create a ROMFS image from the contents of the given path.
    '''
    genromfs_flags = ['-f', 'romfs_img', '-d', input_path]
    xxd_flags = ['-i', 'romfs_img', 'nsh_romfsimg.h']
    sed_flags = ['-ie', 's/unsigned/const\ unsigned/g', 'nsh_romfsimg.h']

    execute(output_path, 'genromfs', genromfs_flags)
    execute(output_path, 'xxd', xxd_flags)
    execute(output_path, 'sed', sed_flags)


def write_json_file(filename, data):
    '''
    Write a JSON file from the given data.
    '''
    with open(filename, 'w') as filename_p:
        json.dump(data, filename_p)

        # Add a newline to the end of the line.
        filename_p.write('\n')


def copy_file(src, dst):
    '''
    Copy a single file to the given place.
    '''
    shutil.copy(src, dst)


def copy_files(src, dst):
    '''
    Copy files from a directory to an other directory.
    '''
    if not os.path.exists(dst):
        os.makedirs(dst)

    for file_name in os.listdir(src):
        shutil.copy(src + file_name, dst)


def move(src, dst):
    '''
    Move a file or directory to another location.
    '''
    shutil.move(src, dst)


def make_archive(folder, fmt):
    '''
    Create an archive file (eg. zip or tar)
    '''
    return shutil.make_archive(folder, fmt, folder)


def mkdir(directory):
    '''
    Create directory.
    '''
    os.makedirs(directory)


def define_environment(env, value):
    '''
    Define environment.
    '''
    os.environ[env] = value


def exists(path):
    '''
    Checks that the given path is exist.
    '''
    return os.path.exists(path)


def size(binary):
    '''
    Get the size of the given program.
    '''
    return os.path.getsize(binary)


def join(path, *paths):
    '''
    Join one or more path components intelligently.
    '''
    return os.path.join(path, *paths)


def dirname(file):
    '''
    Return the folder name.
    '''
    return os.path.dirname(file)


def basename(path):
    '''
    Return the base name of pathname path.
    '''
    return os.path.basename(path)


def abspath(path):
    '''
    Return the absolute path.
    '''
    return os.path.abspath(path)


def relpath(path, start):
    '''
    Return a relative filepath to path from the start directory.
    '''
    return os.path.relpath(path, start)


def last_commit_info(git_repo_path):
    '''
    Get last commit information about the submodules.
    '''
    info = {
        'message': None,
        'commit': None,
        'author': None,
        'date': None
    }

    # Linux repository isn't exist.
    if git_repo_path == 'linux':
        return info

    output, status_code = execute(git_repo_path, 'git', ['log', '-1'], quiet=True)

    for line in output.splitlines():
        if line.startswith('commit'):
            info['commit'] = line.split(' ')[1]

        elif line.startswith('Author'):
            info['author'] = ' '.join(line.split(' ')[1:])

        elif line.startswith('Date'):
                info['date'] = ' '.join(line.split(' ')[1:])

        elif line:
            # Save only the header of the commit message.
            info['message'] = line
            break

    return info


def get_standardized_date():
    '''
    Get the current date in standardized format.
    '''
    return time.strftime('%Y-%m-%dT%H:%M:%SZ')
