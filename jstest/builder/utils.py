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

import os

from jstest.builder import lumpy
from jstest.common import utils


_LIBLIST = [
    'libhttpparser.a',
    'libiotjs.a',
    'libjerry-core.a',
    'libjerry-ext.a',
    'libjerry-port-default.a',
    'libjerry-port-default-minimal.a',
    'libtuv.a'
]


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

        submodules[name] = utils.last_commit_info(module['src'])

    # Merge the collected values into a result object.
    build_info = {
        'build-date': utils.current_date('%Y-%m-%dT%H.%M.%SZ'),
        'last-commit-date': submodules[app_name]['date'],
        'bin': bin_sizes,
        'submodules': submodules
    }

    utils.write_json_file(utils.join(build_path, 'build.json'), build_info)


def generate_romfs(src, dst):
    '''
    Create a romfs_img from the source directory that is
    converted to a header (byte array) file. Finally, add
    a `const` modifier to the byte array to be the data
    in the Read Only Memory.
    '''
    romfs_img = utils.join(os.curdir, 'romfs_img')

    utils.execute(os.curdir, 'genromfs', ['-f', romfs_img, '-d', src])
    utils.execute(os.curdir, 'xxd', ['-i', 'romfs_img', dst])
    utils.execute(os.curdir, 'sed', ['-i', 's/unsigned/const\ unsigned/g', dst])

    os.remove(romfs_img)


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

    mapfile = utils.join(builddir, 'linker.map')
    libdir = utils.join(builddir, 'libs')

    if not (utils.exists(mapfile) and utils.exists(libdir)):
        return section_sizes

    # Get the names of the object files that the static
    # libraries (libjerry-core.a, ...) have.
    objlist = read_objects_from_libs(libdir, _LIBLIST)

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


def read_objects_from_libs(libpath, liblist):
    '''
    Read all the names of the object files that are
    located in the archive files.
    '''
    objlist = []

    for object_file in os.listdir(libpath):
        if object_file not in liblist:
            continue

        output, _ = utils.execute(libpath, 'ar', ['t', object_file], quiet=True)
        objlist.extend(output.splitlines())

    return objlist
