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
import shutil
import subprocess
import time

from jstest.common import console, paths


class TimeoutException(Exception):
    '''
    Custom exception in case of timeout.
    '''
    pass


def execute(cwd, cmd, args=None, quiet=False, strict=True):
    '''
    Run the given command.
    '''
    if args is None:
        args = []

    stdout = None
    stderr = None

    if quiet or os.environ.get('QUIET', ''):
        stdout = subprocess.PIPE
        stderr = subprocess.STDOUT

    if not quiet and os.environ.get('QUIET', ''):
        print_command(cwd, cmd, args)

    try:
        process = subprocess.Popen([cmd] + args, stdout=stdout,
                                   stderr=stderr, cwd=cwd)

        output = process.communicate()[0]
        exitcode = process.returncode

        if strict and exitcode:
            raise Exception('Non-zero exit value.')

        return output, exitcode

    except Exception as e:
        console.fail('[Failed - %s %s] %s' % (cmd, ' '.join(args), str(e)))


def print_command(cwd, cmd, args):
    '''
    Helper function to print commands.
    '''
    rpath = relpath(cwd, paths.PROJECT_ROOT)
    # Resolve the current folder character to the appropriate folder name.
    if rpath == os.curdir:
        rpath = basename(abspath(os.curdir))

    cmd_info = [
        '%s[%s]' % (console.TERMINAL_YELLOW, rpath),
        '%s%s' % (console.TERMINAL_GREEN, cmd),
        '%s%s' % (console.TERMINAL_EMPTY, ' '.join(args))
    ]

    console.log(' '.join(cmd_info))


def patch(project, patch_file, revert=False):
    '''
    Apply the given patch to the given project.
    '''
    patch_options = ['-p1', '-d', project]
    dry_options = ['--dry-run', '-R', '-f', '-s', '-i']

    if not os.path.exists(patch_file):
        console.fail(patch_file + ' does not exist.')

    # First check if the patch can be applied to the project.
    patch_cmd_args = patch_options + dry_options + [patch_file]
    _, patch_applicable = execute('.', 'patch', patch_cmd_args, strict=False, quiet=True)

    # Apply the patch if project is clean and revert flag is not set.
    if not revert and patch_applicable:
        patch_cmd_args = patch_options + ['-i', patch_file]
        _, exitcode = execute('.', 'patch', patch_cmd_args, strict=False, quiet=True)
        if exitcode:
            console.fail('Failed to apply ' + patch_file)

    # Revert the patch if the project already contains the modifications.
    if revert and not patch_applicable:
        patch_cmd_args = patch_options + ['-i', patch_file, '-R']
        _, exitcode = execute('.', 'patch', patch_cmd_args, strict=False, quiet=True)
        if exitcode:
            console.fail('Failed to revert ' + patch_file)


def write_json_file(filename, data):
    '''
    Write a JSON file from the given data.
    '''
    mkdir(dirname(filename))

    with open(filename, 'w') as filename_p:
        json.dump(data, filename_p, indent=2)

        # Add a newline to the end of the line.
        filename_p.write('\n')


def read_json_file(filename):
    '''
    Read JSON file.
    '''
    with open(filename, 'r') as json_file:
        return json.load(json_file)


def copy(src, dst):
    '''
    Copy src to dst.
    '''
    if not exists(src):
        return

    if os.path.isdir(src):
        # Remove dst folder because copytree function
        # fails when is already exists.
        if exists(dst):
            shutil.rmtree(dst)

        shutil.copytree(src, dst, symlinks=False, ignore=None)

    else:
        # Create dst if it does not exist.
        basedir = dirname(dst)
        if not exists(basedir):
            mkdir(basedir)

        shutil.copy(src, dst)


def move(src, dst):
    '''
    Move a file or directory to another location.
    '''
    if not exists(src):
        return

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
    os.environ[env] = str(value)


def get_environment(env):
    '''
    Get environment value.
    '''
    return os.environ.get(env)


def unset_environment(env):
    '''
    Unset environment.
    '''
    os.unsetenv(env)


def exists(path):
    '''
    Checks that the given path is exist.
    '''
    return os.path.exists(path)


def exist_files(path, files):
    '''
    Checks that all files in the list exist relative to the given path.
    '''
    for f in files:
        if not exists(join(path, f)):
            return False

    return True


def size(binary):
    '''
    Get the size of the given program.
    '''
    return os.path.getsize(binary)


def join(path, *paths_to_join):
    '''
    Join one or more path components intelligently.
    '''
    return os.path.join(path, *paths_to_join)


def dirname(file_path):
    '''
    Return the folder name.
    '''
    return os.path.dirname(file_path)


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


def remove_file(filename):
    '''
    Remove the given file.
    '''
    try:
        os.remove(filename)
    except OSError:
        pass


def last_commit_info(gitpath):
    '''
    Get last commit information about the submodules.
    '''
    info = {
        'message': 'n/a',
        'commit': 'n/a',
        'author': 'n/a',
        'date': 'n/a'
    }

    options = [
        'log',
        '-1',
        '--date=format-local:%Y-%m-%dT%H:%M:%SZ',
        '--format=%H%n%an <%ae>%n%cd%n%s'
    ]

    output, exitcode = execute(gitpath, 'git', options, quiet=True)

    if exitcode == 0:
        output = output.splitlines()

        info['commit'] = output[0]
        info['author'] = output[1]
        info['date'] = output[2]
        info['message'] = output[3]

    return info


def current_date(date_format):
    '''
    Format the current datetime by the given pattern.
    '''
    return time.strftime(date_format)


def symlink(src, dst):
    '''
    Create a symlink at dst pointing to src
    '''
    if not exists(src):
        return

    # Normalizing path for symlink.
    src = os.path.normpath(src)
    dst = os.path.normpath(dst)

    # Existing dst needs to be deleted, since symlink requires non-existing dst.
    if exists(dst):
        if os.path.islink(dst):
            os.unlink(dst)
        elif os.path.isfile(dst):
            remove_file(dst)
        else:
            rmtree(dst)

    os.symlink(src, dst)
