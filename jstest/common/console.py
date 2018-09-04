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

from __future__ import print_function

TERMINAL_RED = '\033[1;31m'
TERMINAL_BLUE = '\033[1;34m'
TERMINAL_GREEN = '\033[1;32m'
TERMINAL_EMPTY = '\033[0m'
TERMINAL_YELLOW = '\033[1;33m'


def log(msg='', color=TERMINAL_EMPTY):
    '''
    Print a message with the given color.
    '''
    print('%s%s%s' % (color, msg, TERMINAL_EMPTY))


def info(msg):
    '''
    Print debug message to the screen with green color.
    '''
    print('%s%s%s' % (TERMINAL_GREEN, msg, TERMINAL_EMPTY))


def fail(msg):
    '''
    Raises an error containing msg, which __main.py__ can catch and print out.
    '''
    raise SystemError(msg)
