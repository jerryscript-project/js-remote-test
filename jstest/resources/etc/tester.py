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
    if options.cmd.endswith('iotjs'):
        if not options.no_memstat and not is_executable(FREYA_BIN):
            sys.exit('The Freya tool is not suitable for testing!')

        if not options.no_memstat and not is_readable(FREYA_CONFIG):
            sys.exit('The Freya config file is not available!')

        # Remove the last Freya log file.
        if os.path.exists(FREYA_LOG):
            os.remove(FREYA_LOG)

    if not is_executable(options.cmd):
        sys.exit('The application is not suitable for testing!')

    if not is_readable(options.testfile):
        sys.exit('Testfile is not readable!')


def execute(cwd, cmd, args=None):
    '''
    Run the given command and return its output.
    '''
    if args is None:
        args = []

    stdout = subprocess.PIPE
    stderr = subprocess.STDOUT

    process = subprocess.Popen([cmd] + args, stdout=stdout, stderr=stderr, cwd=cwd)

    output = process.communicate()[0]
    exitcode = process.returncode

    return output.decode('utf-8'), exitcode


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

    args = [options.testfile]
    if not options.no_memstat:
        args.append('--mem-stats')

    if options.debug_port:
        args.append('--start-debug-server')
        args.append('--debug-port')
        args.append('%s' % options.debug_port)

    output, exitcode = execute(options.cwd, options.cmd, args)

    mempeak = 'n/a'
    stack = 'n/a'

    if output.find('Heap stats:') != -1:
        # Process jerry-memstat output.
        match = re.search(r'Peak allocated = (\d+) bytes', output)

        if match:
            mempeak = int(match.group(1))

        # Process stack usage output.
        match = re.search(r'Stack usage: (\d+)', output)

        if match:
            stack = int(match.group(1))

        # Remove memstat from the output.
        output, _ = output.split('Heap stats:', 1)

    return {
        'memstat': {
            'heap-jerry': mempeak,
            'heap-system': 'n/a',
            'stack': stack
        },
        'output': output,
        'exitcode': exitcode,
    }


def run_iotjs(options):
    '''
    Run IoT.js
    '''
    args = []

    if not options.no_memstat:
        args.append('--mem-stats')

    if options.debug_port:
        args.append('--start-debug-server')
        args.append('--debug-port')
        args.append('%s' % options.debug_port)

    args.append(options.testfile)

    # 1. Run IoT.js without Freya to get its output and exit value.
    output, exitcode = execute(options.cwd, options.cmd, args)

    jerry_peak_alloc = 'n/a'
    stack_peak = 'n/a'
    malloc_peak = 'n/a'

    if options.iotjs_build_info:
        return json.loads(output.split('\n')[0])

    if output.find('Heap stats:') != -1:
        # Process jerry-memstat output.
        match = re.search(r'Peak allocated = (\d+) bytes', str(output))

        if match:
            jerry_peak_alloc = int(match.group(1))

        # Process stack usage output.
        match = re.search(r'Stack usage: (\d+)', str(output))

        if match:
            stack_peak = int(match.group(1))

        # Remove memstat from the output.
        output, _ = output.split("Heap stats:", 1)

    if not options.no_memstat:
        # Setup the valgrind options
        valgrind_options = [
            '--tool=freya',
            '--freya-out-file=%s' % FREYA_LOG,
            '--config=%s' % FREYA_CONFIG,
            options.cmd,
            options.testfile
        ]

        # 2. Update the configuration file of Freya:
        ldd_output, _ = execute(options.cwd, 'ldd', ['--version'])
        gnu_libc_version = ldd_output.splitlines()[0].split()[-1]

        sed_options = ['-ie', 's/%%{glibc-version}/%s/g' % gnu_libc_version, 'iotjs-freya.config']
        execute(REMOTE_TESTRUNNER_PATH, 'sed', sed_options)

        # 3. Run IoT.js with Freya to create a log file with the memory information.
        execute(options.cwd, FREYA_BIN, valgrind_options)

        # 4. Process the created log file to get the peak memory.
        malloc_peak = process_freya_output()

    return {
        'memstat': {
            'heap-jerry': jerry_peak_alloc,
            'heap-system': malloc_peak,
            'stack': stack_peak
        },
        'output': output,
        'exitcode': exitcode,
    }


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

    parser.add_argument('--debug-port',
                        metavar='PORT',
                        help='Specify the PORT for jerry-debugger')

    parser.add_argument('--no-memstat',
                        action='store_true', default=False,
                        help='do not measure memory statistics (default: %(default)s)')

    parser.add_argument('--iotjs-build-info',
                        action='store_true', default=False,
                        help='Run the buildinfo script for iotjs')

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
