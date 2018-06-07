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
import pyrebase

from API.common import console, lumpy, paths


class TimeoutException(Exception):
    '''
    Custom exception in case of timeout.
    '''
    pass


def execute(cwd, cmd, args=None, quiet=False):
    '''
    Run the given command.
    '''

    if args is None:
        args = []

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
            raise Exception('Non-zero exit value.')

        return output, exitcode

    except Exception as e:
        console.fail('[Failed - %s %s] %s' % (cmd, ' '.join(args), str(e)))


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


def create_build_info(env):
    '''
    Write binary size and commit information into a file.
    '''
    app_name = env['info']['app']
    build_path = env['paths']['build']

    # Binary size information.
    minimal_builddir = env['paths']['build-minimal']
    target_builddir = env['paths']['build-target']

    bin_sizes = {
        'minimal-profile': calculate_section_sizes(minimal_builddir),
        'target-profile': calculate_section_sizes(target_builddir)
    }

    # Git commit information from the projects.
    submodules = {}

    for name, module in env['modules'].iteritems():
        # Don't duplicate the application information.
        if name == 'app':
            continue

        submodules[name] = last_commit_info(module['src'])

    # Merge the collected values into a result object.
    build_info = {
        'build-date': get_standardized_date(),
        'last-commit-date': submodules[app_name]['date'],
        'bin': bin_sizes,
        'submodules': submodules
    }

    write_json_file(join(build_path, 'build.json'), build_info)


def upload_data_to_firebase(env, test_info):
    '''
    Upload the results of the testrunner to the Firebase database.
    '''
    info = env['info']

    if not info['public']:
        return

    email = get_environment('FIREBASE_USER')
    password = get_environment('FIREBASE_PWD')

    if not (email and password):
        return

    config = {
        'apiKey': 'AIzaSyDMgyPr0V49Rdf5ODAU9nLY02ZGEUNoxiM',
        'authDomain': 'remote-testrunner.firebaseapp.com',
        'databaseURL': 'https://remote-testrunner.firebaseio.com',
        'storageBucket': 'remote-testrunner.appspot.com',
    }

    firebase = pyrebase.initialize_app(config)
    database = firebase.database()
    authentication = firebase.auth()

    user = authentication.sign_in_with_email_and_password(email, password)

    if env['info']['coverage']:
        # Identify the place where the data should be stored.
        database_path = 'coverage/%s/%s' % (info['app'], info['device'])
        database.child(database_path).remove(user['idToken'])
    else:
        database_path = '%s/%s' % (info['app'], info['device'])

    database.child(database_path).push(test_info, user['idToken'])

    if env['info']['coverage']:
        return

    # Update the status images.
    status = 'passed'
    for test in test_info['tests']:
        if test['result'] in ['fail', 'timeout']:
            status = 'failed'
            break

    # The storage service allows to upload images to Firebase.
    storage = firebase.storage()
    # Download the corresponding status badge.
    storage_status_path = 'status/%s.svg' % status
    storage.child(storage_status_path).download('status.svg')
    # Upload the status badge for the appropriate app-device pair.
    storage_badge_path = 'status/%s/%s.svg' % (info['app'], info['device'])
    storage.child(storage_badge_path).put('status.svg', user['idToken'])

    remove_file('status.svg')


def get_standardized_date():
    '''
    Get the current date in standardized format.
    '''
    return time.strftime('%Y-%m-%dT%H.%M.%SZ')


def read_test_files(env):
    '''
    Read all the tests from the given folder and create a
    dictionary similar to the IoT.js testsets.json file.
    '''
    testsets = {}
    # Read all the tests from the application.
    app = env['modules']['app']
    testpath = app['paths']['tests']

    for root, dirs, files in os.walk(testpath):
        # The name of the testset is always the folder name.
        testset = relpath(root, testpath)

        # Create a new testset entry if it doesn't exist.
        if testset not in testsets:
            testsets[testset] = []

        for filename in files:
            test = {
                'name': filename
            }

            if 'fail' in testset:
                test['expected-failure'] = True

            testsets[testset].append(test)

    return testsets


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


def parse_coverage_info(env, coverage_output):
    '''
    Parse and create coverage information
    '''
    coverage_info = {}

    iotjs = env['modules']['iotjs']
    js_folder = iotjs['paths']['js-sources']

    # Store line information from the JS sources.
    for js_file in os.listdir(js_folder):
        filename, _ = os.path.splitext(js_file)

        coverage_info[filename] = {}
        coverage_info[filename]['lines'] = []
        coverage_info[filename]['coverage'] = [0, 0]

        js_file_path = join(js_folder, js_file)

        with open(js_file_path, "r") as js_source:
            lines = js_source.readlines()

            for line in lines:
                # '0' indicates that the line has not been reached yet.
                coverage_info[filename]['lines'].append([line, '0'])

    with open(coverage_output, 'r') as cov_p:
        raw_data = json.load(cov_p)

        ignore_list = ['run_pass', 'run_fail', 'node', 'tools']

        for js_name in raw_data:
            # Skip empty key value.
            if not js_name:
                continue

            # Ignore test and tool files.
            if any(ignored_name in js_name for ignored_name in ignore_list):
                continue

            filename, _ = os.path.splitext(js_name)

            # Iterate reached js files.
            for line_number, line_value in raw_data[js_name].iteritems():
                if line_value:
                    # Increase covered lines.
                    coverage_info[filename]['coverage'][0] += 1
                    # '2' indicates that the line has been covered.
                    coverage_info[filename]['lines'][int(line_number)-1][1] = '2'
                else:
                     # '1' indicates that the line has not been covered.
                    coverage_info[filename]['lines'][int(line_number)-1][1] = '1'

                coverage_info[filename]['coverage'][1] += 1

    return coverage_info


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
