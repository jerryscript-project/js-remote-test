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
import lumpy
import os
import paths
import platform
import re
import shutil
import subprocess
import time


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


def patch(project, patch, revert=False):
    '''
    Apply the given patch to the given project.
    '''
    patch_cmd = ['patch', '-p1', '-d', project]
    dry_options = ['--dry-run', '-R', '-f', '-s', '-i']

    if not os.path.exists(patch):
        console.fail(patch + ' does not exist.')

    # First check if the patch can be applied to the project.
    patch_applicable = subprocess.call(patch_cmd + dry_options + [patch])

    # Apply the patch if project is clean and revert flag is not set.
    if not revert and patch_applicable:
        if subprocess.call(patch_cmd + ['-i', patch]):
            console.fail('Failed to apply ' + patch)

    # Revert the patch if the project already contains the modifications.
    if revert and not patch_applicable:
        if subprocess.call(patch_cmd + ['-i', patch, '-R']):
            console.fail('Failed to revert ' + patch)


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
    if exists(directory):
        return

    os.makedirs(directory)


def define_environment(env, value):
    '''
    Define environment.
    '''
    os.environ[env] = value


def get_environment(env):
    '''
    Get environment value.
    '''
    return os.environ.get(env)


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


def rmtree(path):
    '''
    Remove directory
    '''
    if exists(path):
        shutil.rmtree(path)


def get_section_sizes_from_map(mapfile):
    '''
    Returns the sizes of the main sections.
    '''

    archives = ['libhttpparser.a',
            'libiotjs.a',
            'libjerry-core.a',
            'libjerry-ext.a',
            'libjerry-port-default.a',
            'libjerry-port-default-minimal.a',
            'libtuv.a']

    data = lumpy.load_map_data(mapfile)

    sections = lumpy.parse_to_sections(data)
    # extract .rodata section from the .text section
    lumpy.hoist_section(sections, ".text", ".rodata")

    sizes = {
        "text": 0,
        "rodata": 0,
        "data": 0,
        "bss": 0,
    }

    for s in sections:
        for section_key in sizes:
            if s['name'] == ".%s" % section_key:
                for ss in s['contents']:
                    if ss['path'].endswith(".c.obj)") or \
                        len(filter(lambda ar: "/%s(" % ar in ss['path'], archives)):
                        sizes[section_key] += ss["size"]
                break

    sizes['total'] = sizes["text"] + sizes["data"] + sizes["rodata"]
    return sizes


def get_section_sizes(executable):
    '''
    Returns the sizes of the main sections.
    '''

    args = ['-A', executable]
    sections, _ = execute(os.curdir, 'arm-linux-gnueabi-size', args, quiet=True)

    sizes = {}
    for line in sections.splitlines():
        for key in ['text', 'data', 'rodata', 'bss']:
            if '.%s' % key in line:
                sizes[key] = line.split()[1]

    sizes['total'] = size(executable)

    return sizes


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

    git_flags = [
        'log',
        '-1',
        '--date=format-local:%Y-%m-%dT%H:%M:%SZ',
        '--format=%H%n%an <%ae>%n%cd%n%s'
    ]

    output, status_code = execute(git_repo_path, 'git', git_flags, quiet=True)
    output = output.splitlines()

    info['commit'] = output[0] if status_code == 0 else 'n/a'
    info['author'] = output[1] if status_code == 0 else 'n/a'
    info['date'] = output[2] if status_code == 0 else 'n/a'
    info['message'] = output[3] if status_code == 0 else 'n/a'

    return info


def to_int(value):
    '''
    Return the value as integer type.
    '''
    if isinstance(value, int):
        return value

    return 0


def get_standardized_date():
    '''
    Get the current date in standardized format.
    '''
    return time.strftime('%Y-%m-%dT%H:%M:%SZ')

def get_system():
    '''
    Get the underlying platform name.
    '''
    return platform.system()

def get_architecture():
    '''
    Get the architecture on platform.
    '''
    return platform.architecture()[0][:2]
