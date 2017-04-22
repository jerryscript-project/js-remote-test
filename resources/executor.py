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

import os
import re
import shutil
import subprocess

from . import console
from . import paths


def run_cmd(workdir, cmd, args=[]):
    '''
    Execute the given command.
    '''
    try:
        process = subprocess.Popen([cmd] + args, stdout=subprocess.PIPE,
                                   stderr=subprocess.STDOUT, cwd=workdir)
        output = process.communicate()[0]

        if process.returncode:
            raise Exception('The program returned with non zero exitcode.')

    except Exception as e:
        # Create a log file that contains the output of the last command.
        logfile = os.path.join(paths.PROJECT_ROOT, "failure.log")

        with open(logfile, 'w') as logfile_p:
            logfile_p.write(vars().get('output', ''))
            logfile_p.write('\n[%s] %s\n' % (cmd, str(e)))

        console.fail('[Failed - %s] %s' % (cmd, str(e)))

    # Eliminate unnecessary characters from the output.
    output = re.sub(' +', ' ', output)
    output = re.sub('\n\n', '\n', output)
    output = re.sub('\n ', '\n', output)

    return output


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


def copy_folder(src, dst):
    '''
    Copy a folder to the given place.
    '''
    shutil.copytree(src, dst)


def move(src, dst):
    '''
    Move a file or directory to another location.
    '''
    shutil.move(src, dst)


def remove(folder):
    '''
    Remove the entire directory.
    '''
    if os.path.exists(folder):
        shutil.rmtree(folder)


def exists(path):
    '''
    Checks that the given path is exist.
    '''
    return os.path.exists(path)


def mkdir(directory):
    '''
    Create directory.
    '''
    os.makedirs(directory)
