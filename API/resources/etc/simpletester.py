#!/usr/bin/env python


# Copyright 2018-present Samsung Electronics Co., Ltd. and other contributors
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
import subprocess


def execute(cwd, cmd, testfile):
    '''
    Run the given command and return its output.
    '''
    stdout = subprocess.PIPE
    stderr = subprocess.STDOUT

    process = subprocess.Popen([cmd, testfile], stdout=stdout, stderr=stderr, cwd=cwd)

    output = process.communicate()[0]
    exitcode = process.returncode

    return {
        'output': str(output),
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

    return parser.parse_args()


def main():
    '''
    Main function of the tester script.
    '''
    arguments = parse_arguments()

    results = execute(arguments.cwd, arguments.cmd, arguments.testfile)
    results['memstat'] = {
        'heap-jerry': 'n/a',
        'heap-system': 'n/a',
        'stack': 'n/a'
    }

    # Don't remove this print function. The result will be on the
    # SSH socket when testing remotely.
    print(json.dumps(results))


if __name__ == '__main__':
    main()
