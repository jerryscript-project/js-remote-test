#!/usr/bin/env python

# Copyright 2018-present Samsung Electronics Co., Ltd. and other contributors
#
# Licensed under the Apache License, Version 2.0 (the 'License');
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an 'AS IS' BASIS
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import re
import subprocess

TOOLS_PATH = os.path.dirname(os.path.abspath(__file__))
JSREMOTE_ROOT = os.path.join(TOOLS_PATH, '..')

JSTEST_PATH = os.path.join(JSREMOTE_ROOT, 'jstest')

PYFILE_REGEX = r'^.*\.py$'

TERMINAL_RED = '\033[1;31m'
TERMINAL_YELLOW = '\033[1;33m'
TERMINAL_EMPTY = '\033[0m'

def recursive_check(directory=JSREMOTE_ROOT):
    '''
    Check all python files in the given directory recursively.
    '''
    exitcode = 0
    print('%s%s%s' % (TERMINAL_RED, directory, TERMINAL_EMPTY))

    for subdir, _, files in os.walk(directory):
        for f in files:
            if re.match(PYFILE_REGEX, f):
                path_to_check = os.path.join(subdir, f)
                print('%s%s%s' % (TERMINAL_YELLOW, path_to_check, TERMINAL_EMPTY))
                exitcode = subprocess.call(['python2', '-m', 'pylint', path_to_check]) or exitcode

    return exitcode


def main():
    exitcode = 0
    for path in [JSTEST_PATH, TOOLS_PATH]:
        exitcode = recursive_check(path) or exitcode

    exit(exitcode)


if __name__ == '__main__':
    main()
