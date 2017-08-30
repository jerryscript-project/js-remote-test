#!/usr/bin/env python

# Copyright 2017-present Samsung Electronics Co., Ltd. and other contributors
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

from __future__ import print_function

import argparse
import os
import sys

from common_py.system.executor import Executor as ex


TESTS=['signed-off']

def parse_option():
    parser = argparse.ArgumentParser(
         description='JS-remote-test precommit script.',
         epilog='If no arguments are given, run all tests.')
    parser.add_argument('--test', choices=TESTS, action='append')

    option = parser.parse_args(sys.argv[1:])
    if option.test is None:
        option.test = TESTS
    return option


if __name__ == '__main__':
    option = parse_option()

    build_args = []

    for test in option.test:
        if test == 'signed-off':
            args = []
            if os.getenv('TRAVIS') is not None:
                args = ['--travis']
            ex.check_run_cmd('tools/check_signed_off.sh', args)
