#!/usr/bin/env python


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

import argparse
import errno
import json
import os
import re
import subprocess
import sys


# Recommended build command for IoT.js on RPi2:
#
# tools/build.py --target-board=rpi2
#                --buildtype=release
#                --jerry-cmake-param="-DFEATURE_VALGRIND_FREYA=ON"
#                --compile-flag="-g"
#                --jerry-compile-flag="-g"

REMOTE_TESTRUNNER_PATH = os.path.abspath(os.path.dirname(__file__))

FREYA_BIN = os.path.join(REMOTE_TESTRUNNER_PATH, 'valgrind_freya', 'vg-in-place')
FREYA_LOG = os.path.join(REMOTE_TESTRUNNER_PATH, 'freya.log')
FREYA_CONFIG = os.path.join(REMOTE_TESTRUNNER_PATH, 'iotjs-freya.config')


def is_executable(fpath):
    '''
    Check whether the file is executable.
    '''
    return os.path.isfile(fpath) and os.access(fpath, os.X_OK)


def is_readable(fpath):
    '''
    Check whether the file is readable.
    '''
    return os.path.isfile(fpath) and os.access(fpath, os.R_OK)


def check_tools(options):
    '''
    Checking resources before testing.
    '''
    if not is_executable(FREYA_BIN):
        sys.exit('The Freya tool is not suitable for testing!')

    if not is_readable(FREYA_CONFIG):
        sys.exit('The Freya config file is not available!')

    if not is_executable(options.cmd):
        sys.exit('The application is not suitable for testing!')

    if not is_readable(options.testfile):
        sys.exit('Testfile is not readable!')

    # Remove the last Freya log file.
    if os.path.exists(FREYA_LOG):
        os.remove(FREYA_LOG)


def execute(cwd, cmd, args=[]):
    '''
    Run the given command and return its output.
    '''
    stdout = subprocess.PIPE
    stderr = subprocess.STDOUT

    process = subprocess.Popen([cmd] + args, stdout=stdout, stderr=stderr, cwd=cwd)

    output = process.communicate()[0]
    exitcode = process.returncode

    return output, exitcode


def process_freya_output():
    '''
    Process the Freya log file to get the peak memory usage.
    '''
    if not is_readable(FREYA_LOG):
        sys.exit('Missing Freya log file!')

    measurement = open(FREYA_LOG, 'r').read()

    pattern = re.compile('\[0\] Peak:.*?(\d+)b.*\nGroup: Total')
    match = pattern.search(measurement)

    if match:
        mempeak = int(match.group(1))
    else:
        mempeak = 'n/a'

    return mempeak


def run_jerry(options):
    '''
    Run JerryScript with memcheck.
    '''
    output, exitcode = execute(options.cwd, options.cmd, [options.testfile, '--mem-stats'])

    # Process the memstat to get the peak memory.
    match = re.search(r'Peak allocated = (\d+) bytes', str(output))

    if match:
        mempeak = match.group(1)
    else:
        mempeak = 'n/a'

    output = output.rsplit("Heap stats",1)[0]

    return { 'exitcode': exitcode, 'output': output, 'mempeak': mempeak }


def run_iotjs(options):
    '''
    Run IoT.js with Freya.
    '''
    valgrind_options = [
        '--tool=freya',
        '--freya-out-file=%s' % FREYA_LOG,
        '--config=%s' % FREYA_CONFIG,
        options.cmd,
        options.testfile
    ]

    # 1. Run IoT.js without Freya to get its output and exit value.
    output, exitcode = execute(options.cwd, options.cmd, [options.testfile])

    # 2. Update the configuration file of Freya:
    ldd_output, _ = execute(options.cwd, 'ldd', ['--version'])
    gnu_libc_version = ldd_output.splitlines()[0].split()[-1]

    sed_options = ['-ie', 's/YOUR_GLIBC_VERSION/%s/g' % gnu_libc_version, 'iotjs-freya.config']
    execute(REMOTE_TESTRUNNER_PATH, 'sed', sed_options)

    # 3. Run IoT.js with Freya to create a log file with the memory information.
    execute(options.cwd, FREYA_BIN, valgrind_options)

    # 4. Process the created log file to get the peak memory.
    mempeak = process_freya_output()

    return { 'exitcode': exitcode, 'output': output, 'mempeak': mempeak }


def parse_arguments():
    '''
    Parse the given arguments.
    '''
    parser = argparse.ArgumentParser('Tester script for the remote testrunner.')

    parser.add_argument('--cwd', metavar='path',
                        help='current working directory to run tests')

    parser.add_argument('--cmd', metavar='path',
                        help='path to the binary')

    parser.add_argument('--testfile', metavar='file',
                        help='Test file with path')

    return parser.parse_args()


def main():
    '''
    Main function of the tester script.
    '''
    arguments = parse_arguments()

    check_tools(arguments)

    if arguments.cmd.endswith('iotjs'):
        results = run_iotjs(arguments)

    if arguments.cmd.endswith('jerry'):
        results = run_jerry(arguments)

    # Don't remove this print function. The result will be on the
    # SSH socket when testing remotely.
    print(json.dumps(results))


if __name__ == '__main__':
    main()
