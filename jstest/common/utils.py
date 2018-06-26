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
import re
import shutil
import subprocess
import time

from jstest.common import console, paths
from jstest.builder import lumpy

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

    console.info("Run: %s %s (%s)\n" % (cmd, ' '.join(args), cwd))

    if quiet or os.environ.get('QUIET', ''):
        stdout = subprocess.PIPE
        stderr = subprocess.STDOUT

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


def patch(project, patch, revert=False):
    '''
    Apply the given patch to the given project.
    '''
    patch_options = ['-p1', '-d', project]
    dry_options = ['--dry-run', '-R', '-f', '-s', '-i']

    if not os.path.exists(patch):
        console.fail(patch + ' does not exist.')

    # First check if the patch can be applied to the project.
    _, patch_applicable = execute('.', 'patch', patch_options + dry_options + [patch], strict=False)

    # Apply the patch if project is clean and revert flag is not set.
    if not revert and patch_applicable:
        _, exitcode = execute('.', 'patch', patch_options + ['-i', patch], strict=False)
        if exitcode:
            console.fail('Failed to apply ' + patch)

    # Revert the patch if the project already contains the modifications.
    if revert and not patch_applicable:
        _, exitcode = execute('.', 'patch', patch_options + ['-i', patch, '-R'], strict=False)
        if exitcode:
            console.fail('Failed to revert ' + patch)


def generate_romfs(src, dst):
    '''
    Create a romfs_img from the source directory that is
    converted to a header (byte array) file. Finally, add
    a `const` modifier to the byte array to be the data
    in the Read Only Memory.
    '''
    romfs_img = join(os.curdir, 'romfs_img')

    execute(os.curdir, 'genromfs', ['-f', romfs_img, '-d', src])
    execute(os.curdir, 'xxd', ['-i', 'romfs_img', dst])
    execute(os.curdir, 'sed', ['-i', 's/unsigned/const\ unsigned/g', dst])

    os.remove(romfs_img)


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


def join(path, *paths):
    '''
    Join one or more path components intelligently.
    '''
    return os.path.join(path, *paths)


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


_liblist = [
    'libhttpparser.a',
    'libiotjs.a',
    'libjerry-core.a',
    'libjerry-ext.a',
    'libjerry-port-default.a',
    'libjerry-port-default-minimal.a',
    'libtuv.a'
]


def calculate_section_sizes(builddir):
    '''
    Return the sizes of the main sections.
    '''
    section_sizes = {
        'bss': 0,
        'text': 0,
        'data': 0,
        'rodata': 0
    }

    mapfile = join(builddir, 'linker.map')
    libdir = join(builddir, 'libs')

    if not (exists(mapfile) and exists(libdir)):
        return section_sizes

    # Get the names of the object files that the static
    # libraries (libjerry-core.a, ...) have.
    objlist = read_objects_from_libs(libdir, _liblist)

    raw_data = lumpy.load_map_data(mapfile)
    sections = lumpy.parse_to_sections(raw_data)
    # Extract .rodata section from the .text section.
    lumpy.hoist_section(sections, '.text', '.rodata')

    for section in sections:
        section_name = section['name'][1:]
        # Skip sections that are not relevant.
        if section_name not in section_sizes.keys():
            continue

        for entry in section['contents']:
            if any(obj in entry['path'] for obj in objlist):
                section_sizes[section_name] += entry['size']

    return section_sizes


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


def get_standardized_date():
    '''
    Get the current date in standardized format.
    '''
    return time.strftime('%Y-%m-%dT%H.%M.%SZ')


def process_output(output):
    '''
    Extract the runtime memory information from the output of the test.
    '''
    exitcode = 0
    memstat = {
        'heap-jerry': 'n/a',
        'heap-system': 'n/a',
        'stack': 'n/a'
    }

    match = re.search(r'(IoT.js|JerryScript) [Rr]esult: (\d+)', output)

    if match:
        exitcode = int(match.group(2))

    if output.find('Heap stats:') != -1:
        # Process jerry-memstat output.
        match = re.search(r'Peak allocated = (\d+) bytes', output)

        if match:
            memstat['heap-jerry'] = int(match.group(1))

        # Process malloc peak output.
        match = re.search(r'Malloc peak allocated: (\d+) bytes', output)

        if match:
            memstat['heap-system'] = int(match.group(1))

        # Process stack usage output.
        match = re.search(r'Stack usage: (\d+)', output)

        if match:
            memstat['stack'] = int(match.group(1))

        # Remove memstat from the output.
        output, _ = output.split('Heap stats:', 1)

    return output, memstat, exitcode


def read_objects_from_libs(libpath, liblist):
    '''
    Read all the names of the object files that are
    located in the archive files.
    '''
    objlist = []

    for object_file in os.listdir(libpath):
        if object_file not in liblist:
            continue

        output, _ = execute(libpath, 'ar', ['t', object_file], quiet=True)
        objlist.extend(output.splitlines())

    return objlist


def read_port_from_url(url):
    '''
    Parse URL and return with the port number
    '''
    pattern = '(?:http.*://)?(?P<host>[^:/ ]+).?(?P<port>[0-9]*).*'

    match = re.search(pattern, url)

    if not match:
        console.fail('Invalid URL: %s' % url)

    return match.group('port')


def run_coverage_script(env):
    '''
    Start the client script.
    '''
    # Add latency because the start up of the debug server needs time.
    time.sleep(2)

    address = env['info']['coverage']
    iotjs = env['modules']['iotjs']
    coverage_client = iotjs['paths']['coverage-client']
    device = env['info']['device']
    app_name = env['info']['app']

    commit_info = last_commit_info(iotjs['src'])
    result_name = 'cov-%s-%s.json' % (commit_info['commit'], commit_info['date'])
    result_dir = join(paths.RESULT_PATH, '%s/%s/' % (app_name, device))
    result_path = join(result_dir, result_name)

    mkdir(result_dir)
    execute(paths.PROJECT_ROOT, coverage_client, ['--non-interactive',
                                                  '--coverage-output=%s' % result_path,
                                                   address])
