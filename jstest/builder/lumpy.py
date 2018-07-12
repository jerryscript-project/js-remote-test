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

# BSD 2-Clause License
#
# Copyright (c) 2017, elecro
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# * Redistributions of source code must retain the above copyright notice, this
#   list of conditions and the following disclaimer.
#
# * Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import argparse
import logging
import json
import re
import sys

logging.basicConfig(level=logging.ERROR)
LOG = logging.getLogger(__name__)


def load_map_data(filepath):
    with open(filepath, "r") as fp:
        return fp.readlines()


def get_memory_map_lines(data):
    map_started = False
    for i, line in enumerate(data):
        if not map_started:
            if line.startswith("Linker script and memory map"):
                map_started = True
                LOG.debug("Found memory map start at line %d", i + 1)
            continue

        yield i, line.rstrip()


def hoist_section(sections, from_section, to_section):
    matching_sections = [sec for sec in sections if sec["name"] == from_section]
    if not matching_sections:
        LOG.warning("Skipping '%s' section hoisting from '%s' as it was not found",
                    to_section, from_section)
        return None
    if len(matching_sections) > 1:
        LOG.warning("Matched multiple sections for '%s', using only the first one", from_section)

    start_idx = -1
    end_idx = 0
    section = matching_sections[0]
    for idx, entry in enumerate(section["contents"]):
        if entry["section_name"].startswith(to_section):
            if start_idx == -1:
                start_idx = idx
            end_idx = idx

    if start_idx == -1:
        LOG.debug("Section '%s' not found in '%s'", to_section, from_section)
        return False

    LOG.debug("Found '%s' section in '%s' in range [%d; %d]",
              to_section, from_section, start_idx, end_idx + 1)

    # construct the new section
    hoisted_section = {
        "name": to_section,
        "address": section["contents"][start_idx]["address"],
        "size": 0,
        "extra_info": "hoisted section from '{}'".format(from_section),
        "contents": section["contents"][start_idx:end_idx + 1]
    }
    start_address = int(hoisted_section["address"], base=16)
    last_entry = hoisted_section["contents"][-1]
    last_address = int(last_entry["address"], base=16)
    last_size = last_entry["size"]

    hoisted_section["size"] = last_address + last_size - start_address

    # remove the entries from the old section
    del section["contents"][start_idx:end_idx + 1]

    sections.append(hoisted_section)
    return True


# match top level sections in format: <dot><any non-whitespace charater>
_RE_SECTION_NAME = r"^(?P<name>\.\S+)"


def try_match_section(idx, data, line):
    skip_next = False
    match_section_start = re.match(_RE_SECTION_NAME, line)
    if not match_section_start:
        # match failed
        return False, False

    section_name = match_section_start.group('name')
    LOG.debug("Found section '%s'", section_name)

    if len(section_name) >= 14:
        LOG.debug("Section name too long. Maybe there is a wrapping")
        next_line = data[idx + 1]
        if next_line.startswith("  "):
            LOG.debug(" 99.0%% sure that there is wrapping")
            line += data[idx + 1]
            skip_next = True

    # format for section lines (should be): <section name> <address> <total size>
    address = 0
    total_size = 0
    extra_info = []
    contents = line.split(None, 3)
    contents_length = len(contents)
    # it is possible that there is only a section name
    if contents_length > 1:
        address = contents[1]
        # size is in hex with the format: 0x....
        total_size = int(contents[2], base=16)
        extra_info = contents[3:]

    section = {
        "name": section_name,
        "address": address,
        "size": total_size,
        "extra_info": " ".join(extra_info),
        "contents": [],
    }
    LOG.debug("Section parsed: %s", section)
    return section, skip_next


# match entry in format: <dot><space><any non-whitespace charater>
_RE_PART_NAME = r"(?P<name>(\.\S+|COMMON))"
_RE_PART_ENRTY = r"\s+(?P<address>0x[\da-fA-F]+)\s+(?P<size>0x[\da-fA-F]+)\s+(?P<path>.+)"
_RE_ENTRY_NAME = r"^ {}".format(_RE_PART_NAME)
_RE_WRAPPED_ENTRY_DATA = r"^  {}".format(_RE_PART_ENRTY)
_RE_ENTRY_DATA = r"^ {}{}".format(_RE_PART_NAME, _RE_PART_ENRTY)


def try_match_entry(idx, data, line):
    skip_next = False
    match_entry_start = re.match(_RE_ENTRY_NAME, line)
    if not match_entry_start:
        return False, False

    section_name = match_entry_start.group("name")
    LOG.debug("Found entry for '%s'", section_name)
    if len(section_name) >= 14:
        LOG.debug("Possible wrapped entry found")
        # It is possible that the ountents are wrapped, reading next line
        next_line = data[idx + 1]
        # if the next line starts with at least two spaces and an address
        # it is really just a wrapped line, we'll merge it to the current line
        match_entry = re.match(_RE_WRAPPED_ENTRY_DATA, next_line)
        if match_entry:
            LOG.debug(" Verified, entry was indeed wrapped")
            skip_next = True
    else:
        match_entry = re.match(_RE_ENTRY_DATA, line)

    if not match_entry:
        return False, False

    entry = {
        "section_name": section_name,
        "address": match_entry.group("address"),
        "size": int(match_entry.group("size"), base=16),
        "path": match_entry.group("path"),
        "symbols": [],
    }
    LOG.debug("Entry parsed: %s", entry)

    return entry, skip_next


# match symbols, format: <lots of spaces> <address> <symbol_name>
_RE_SYMBOL = r"^\s+(?P<address>0x[\da-fA-F]+)\s+(?P<symbol_name>.+)"


def try_match_symbol(line):
    match_symbol = re.match(_RE_SYMBOL, line)
    if not match_symbol:
        return False, False

    address = match_symbol.group("address")
    symbol_name = match_symbol.group("symbol_name")
    LOG.debug("Found symbol '%s'", symbol_name)

    if symbol_name == "(size before relaxing)":
        # this is not a true symbol, skipping
        LOG.debug("Skipping original size")
        return False, False

    symbol = {
        "name": symbol_name,
        "address": address,
    }

    return symbol, False


_RE_FILL_ENTRY = r"^ \*fill\*\s+(?P<address>0x[\da-fA-F]+)\s+(?P<size>0x[\da-fA-F]+)"


def try_match_fill(line):
    match_fill = re.match(_RE_FILL_ENTRY, line)
    if not match_fill:
        return False, False

    LOG.debug("Found a fill entry:' %s'", line)
    entry = {
        "section_name": "*fill*",
        "address": match_fill.group("address"),
        "size": int(match_fill.group("size"), base=16),
        "path": "",
    }
    LOG.debug("Fill entry parsed: %s", entry)
    return entry, False


def parse_to_sections(data):
    sections = []
    skip_next = False
    for i, line in get_memory_map_lines(data):
        if skip_next:
            # this line was already processed by a previous iteration
            skip_next = False
            continue

        # check if we have a top level section
        section, skip_next = try_match_section(i, data, line)
        if section:
            sections.append(section)
            continue

        # check if we have an entry
        entry, skip_next = try_match_entry(i, data, line)
        if not entry:
            # check if we have a *fill* entry
            entry, skip_next = try_match_fill(line)

        if entry:
            last_contents = sections[-1]["contents"]
            if last_contents:
                last_entry = last_contents[-1]
                if entry["address"] == last_entry["address"]:
                    LOG.debug("Detected same address for entry")

            sections[-1]["contents"].append(entry)
            continue

        # match address and symbol pairs
        symbol, skip_next = try_match_symbol(line)
        if symbol:
            # try to connect the symbol to the last object file
            if sections and sections[-1]["contents"]:
                if "symbols" in sections[-1]["contents"][-1]:
                    sections[-1]["contents"][-1]["symbols"].append(symbol)
                else:
                    LOG.warning("Tried to connect a smybol to a *fill* entry: '%s'", symbol)
            else:
                LOG.warning("Unable to connect symbol to object: '%s'", symbol)
            continue

    return sections


def dump_section_table(sections):
    for section in sections:
        size = 0
        for entry in section["contents"]:
            size += entry["size"]

        print("Section {name:17} reported size: {size:-7} bytes  "
              "calculated size: {calculated_size:-7} bytes (Diff: {size_diff:-7}) {extra_info}"
              .format(calculated_size=size, size_diff=section["size"] - size, **section))


def main():
    parser = argparse.ArgumentParser(description="LuMPy - Linker Map Parser")
    parser.add_argument("-o", "--output",
                        help="Output path for the JSON file (default: <input>.json) "
                             "If '-' is specified as output the stdout will be used")
    parser.add_argument("-v", "--verbose", dest="verbose", action='count')
    parser.add_argument("-q", "--quiet", dest="verbose", action="store_const", const=-1,
                        help="Suppress all output messages")
    parser.add_argument("mapfile", metavar="MAP_FILE", help="Input mapfile")
    args = parser.parse_args()

    use_stdout = False

    if args.output == "-":
        use_stdout = True
        args.verbose = -1

    verbose_levels = {
        -1: logging.CRITICAL,
        1: logging.INFO,
        2: logging.DEBUG,
    }
    if args.verbose:
        LOG.setLevel(verbose_levels.get(args.verbose, logging.DEBUG))

    LOG.info("Loading map file '%s'", args.mapfile)

    data = load_map_data(args.mapfile)
    LOG.info("Loaded %d lines", len(data))

    sections = parse_to_sections(data)
    # extract .rodata section from the .text section
    hoist_section(sections, ".text", ".rodata")

    if use_stdout:
        json.dump(sections, sys.stdout, indent=2)
    else:
        # print out things
        dump_section_table(sections)

        if args.output:
            output_path = args.output
        else:
            output_path = args.mapfile + ".json"

        with open(output_path, "w") as fp:
            json.dump(sections, fp, indent=2)
        LOG.info("JSON saved to '%s'", output_path)

if __name__ == "__main__":
    main()
