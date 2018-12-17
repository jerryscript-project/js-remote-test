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

from cmd import Cmd

import argparse
import re
import select
import socket
import struct
import sys
import json
import os

# Expected debugger protocol version.
JERRY_DEBUGGER_VERSION = 8

# Messages sent by the server to client.
JERRY_DEBUGGER_CONFIGURATION = 1
JERRY_DEBUGGER_PARSE_ERROR = 2
JERRY_DEBUGGER_BYTE_CODE_CP = 3
JERRY_DEBUGGER_PARSE_FUNCTION = 4
JERRY_DEBUGGER_BREAKPOINT_LIST = 5
JERRY_DEBUGGER_BREAKPOINT_OFFSET_LIST = 6
JERRY_DEBUGGER_SOURCE_CODE = 7
JERRY_DEBUGGER_SOURCE_CODE_END = 8
JERRY_DEBUGGER_SOURCE_CODE_NAME = 9
JERRY_DEBUGGER_SOURCE_CODE_NAME_END = 10
JERRY_DEBUGGER_FUNCTION_NAME = 11
JERRY_DEBUGGER_FUNCTION_NAME_END = 12
JERRY_DEBUGGER_RELEASE_BYTE_CODE_CP = 14
JERRY_DEBUGGER_BREAKPOINT_HIT = 16
JERRY_DEBUGGER_EXCEPTION_HIT = 17
JERRY_DEBUGGER_EXCEPTION_STR = 18
JERRY_DEBUGGER_EXCEPTION_STR_END = 19

# Debugger option flags
JERRY_DEBUGGER_LITTLE_ENDIAN = 0x1

# Messages sent by the client to server.
JERRY_DEBUGGER_FREE_BYTE_CODE_CP = 1
JERRY_DEBUGGER_UPDATE_BREAKPOINT = 2
JERRY_DEBUGGER_PARSER_CONFIG = 4
JERRY_DEBUGGER_CONTINUE = 12

MAX_BUFFER_SIZE = 128
WEBSOCKET_BINARY_FRAME = 2
WEBSOCKET_FIN_BIT = 0x80

# Debugger action types
DEBUGGER_ACTION_NONE = 0
DEBUGGER_ACTION_END = 1
DEBUGGER_ACTION_WAIT = 2
DEBUGGER_ACTION_PROMPT = 3


def arguments_parse():
    parser = argparse.ArgumentParser(description="Coverage Client")

    parser.add_argument("address", action="store", nargs="?", default="localhost:5001",
                        help="specify the network address for connection (default: %(default)s)")
    parser.add_argument("--coverage-output", action="store", default="coverage_output.json",
                        help="specify the output file for coverage (default: %(default)s)")

    args = parser.parse_args()

    return args


class JerryBreakpoint(object):
    def __init__(self, line, offset, function):
        self.line = line
        self.offset = offset
        self.function = function
        self.active_index = -1


class JerryFunction(object):
    def __init__(self, is_func, byte_code_cp, source, source_name,
                 line, column, name, lines, offsets):
        self.is_func = bool(is_func)
        self.byte_code_cp = byte_code_cp
        self.source = re.split("\r\n|[\r\n]", source)
        self.source_name = source_name
        self.name = name
        self.lines = {}
        self.offsets = {}
        self.line = line
        self.column = column
        self.first_breakpoint_offset = offsets[0]

        if len(self.source) > 1 and not self.source[-1]:
            self.source.pop()

        for i, _line in enumerate(lines):
            offset = offsets[i]
            breakpoint = JerryBreakpoint(_line, offset, self)
            self.lines[_line] = breakpoint
            self.offsets[offset] = breakpoint


class Multimap(object):
    def __init__(self):
        self.map = {}

    def get(self, key):
        if key in self.map:
            return self.map[key]
        return []

    def insert(self, key, value):
        if key in self.map:
            self.map[key].append(value)
        else:
            self.map[key] = [value]

    def delete(self, key, value):
        items = self.map[key]

        if len(items) == 1:
            del self.map[key]
        else:
            del items[items.index(value)]

    def __repr__(self):
        return "Multimap(%r)" % (self.map)


class JerryDebugger(object):
    # pylint: disable=too-many-statements
    def __init__(self, address, coverage_output):

        if ":" not in address:
            self.host = address
            self.port = 5001  # use default port
        else:
            self.host, self.port = address.split(":")
            self.port = int(self.port)

        print("Connecting to: %s:%s" % (self.host, self.port))

        self.message_data = b""
        self.prompt = False
        self.function_list = {}
        self.source = ''
        self.source_name = ''
        self.exception_string = ''
        self.line_list = Multimap()
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.connect((self.host, self.port))
        self.coverage_info = {}

        if os.path.isfile(coverage_output):
            with open(coverage_output) as data:
                self.coverage_info = json.load(data)

        self.send_message(b"GET /jerry-debugger HTTP/1.1\r\n" +
                          b"Upgrade: websocket\r\n" +
                          b"Connection: Upgrade\r\n" +
                          b"Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==\r\n\r\n")
        result = b""
        expected = (b"HTTP/1.1 101 Switching Protocols\r\n" +
                    b"Upgrade: websocket\r\n" +
                    b"Connection: Upgrade\r\n" +
                    b"Sec-WebSocket-Accept: s3pPLMBiTxaQ9kYGzzhZRbK+xOo=\r\n\r\n")

        len_expected = len(expected)

        while len(result) < len_expected:
            result += self.client_socket.recv(1024)

        len_result = len(result)

        if result[0:len_expected] != expected:
            raise Exception("Unexpected handshake")

        if len_result > len_expected:
            result = result[len_expected:]
        else:
            result = b""

        len_expected = 10
        # Network configurations, which has the following struct:
        # header [2] - opcode[1], size[1]
        # type [1]
        # configuration [1]
        # version [4]
        # max_message_size [1]
        # cpointer_size [1]

        while len(result) < len_expected:
            result += self.client_socket.recv(1024)

        len_result = len(result)

        expected = struct.pack("BBB",
                               WEBSOCKET_BINARY_FRAME | WEBSOCKET_FIN_BIT,
                               8,
                               JERRY_DEBUGGER_CONFIGURATION)

        if result[0:3] != expected:
            raise Exception("Unexpected configuration")

        self.little_endian = ord(result[3]) & JERRY_DEBUGGER_LITTLE_ENDIAN
        self.max_message_size = ord(result[8])
        self.cp_size = ord(result[9])

        if self.little_endian:
            self.byte_order = "<"
        else:
            self.byte_order = ">"

        if self.cp_size == 2:
            self.cp_format = "H"
        else:
            self.cp_format = "I"

        self.idx_format = "I"

        self.version = struct.unpack(self.byte_order + self.idx_format, result[4:8])[0]
        if self.version != JERRY_DEBUGGER_VERSION:
            raise Exception("Incorrect debugger version from target: %d expected: %d" %
                            (self.version, JERRY_DEBUGGER_VERSION))

        if len_result > len_expected:
            self.message_data = result[len_expected:]

    def get_coverage_info(self):
        return self.coverage_info

    def __del__(self):
        self.client_socket.close()

    def get_continue(self):
        self.prompt = False
        self.send_command(JERRY_DEBUGGER_CONTINUE)


    def send_breakpoint(self, breakpoint):
        message = struct.pack(self.byte_order + "BBIBB" + self.cp_format + self.idx_format,
                              WEBSOCKET_BINARY_FRAME | WEBSOCKET_FIN_BIT,
                              WEBSOCKET_FIN_BIT + 1 + 1 + self.cp_size + 4,
                              0,
                              JERRY_DEBUGGER_UPDATE_BREAKPOINT,
                              int(breakpoint.active_index >= 0),
                              breakpoint.function.byte_code_cp,
                              breakpoint.offset)
        self.send_message(message)

    def send_bytecode_cp(self, byte_code_cp):
        message = struct.pack(self.byte_order + "BBIB" + self.cp_format,
                              WEBSOCKET_BINARY_FRAME | WEBSOCKET_FIN_BIT,
                              WEBSOCKET_FIN_BIT + 1 + self.cp_size,
                              0,
                              JERRY_DEBUGGER_FREE_BYTE_CODE_CP,
                              byte_code_cp)
        self.send_message(message)

    def send_command(self, command):
        message = struct.pack(self.byte_order + "BBIB",
                              WEBSOCKET_BINARY_FRAME | WEBSOCKET_FIN_BIT,
                              WEBSOCKET_FIN_BIT + 1,
                              0,
                              command)
        self.send_message(message)

    def send_message(self, message):
        size = len(message)
        while size > 0:
            bytes_send = self.client_socket.send(message)
            if bytes_send < size:
                message = message[bytes_send:]
            size -= bytes_send


    def get_message(self, blocking):
        # Connection was closed
        if self.message_data is None:
            return None

        while True:
            if len(self.message_data) >= 2:
                if ord(self.message_data[0]) != WEBSOCKET_BINARY_FRAME | WEBSOCKET_FIN_BIT:
                    raise Exception("Unexpected data frame")

                size = ord(self.message_data[1])
                if size == 0 or size >= 126:
                    raise Exception("Unexpected data frame")

                if len(self.message_data) >= size + 2:
                    result = self.message_data[0:size + 2]
                    self.message_data = self.message_data[size + 2:]
                    return result

            if not blocking:
                select_result = select.select([self.client_socket], [], [], 0)[0]
                if self.client_socket not in select_result:
                    return b''

            data = self.client_socket.recv(MAX_BUFFER_SIZE)

            if not data:
                self.message_data = None
                return None
            self.message_data += data

    def process_messages(self):

        while True:
            data = self.get_message(False)
            if data == b'':
                return DEBUGGER_ACTION_PROMPT if self.prompt else DEBUGGER_ACTION_WAIT

            if not data:  # Break the while loop if there is no more data.
                return DEBUGGER_ACTION_END

            buffer_type = ord(data[2])

            if buffer_type in [JERRY_DEBUGGER_PARSE_ERROR,
                               JERRY_DEBUGGER_BYTE_CODE_CP,
                               JERRY_DEBUGGER_PARSE_FUNCTION,
                               JERRY_DEBUGGER_BREAKPOINT_LIST,
                               JERRY_DEBUGGER_SOURCE_CODE,
                               JERRY_DEBUGGER_SOURCE_CODE_END,
                               JERRY_DEBUGGER_SOURCE_CODE_NAME,
                               JERRY_DEBUGGER_SOURCE_CODE_NAME_END,
                               JERRY_DEBUGGER_FUNCTION_NAME,
                               JERRY_DEBUGGER_FUNCTION_NAME_END]:
                self._parse_source(data)

            elif buffer_type == JERRY_DEBUGGER_RELEASE_BYTE_CODE_CP:
                self._release_function(data)
            elif buffer_type in [JERRY_DEBUGGER_BREAKPOINT_HIT, JERRY_DEBUGGER_EXCEPTION_HIT]:
                if buffer_type == JERRY_DEBUGGER_EXCEPTION_HIT:
                    if self.exception_string:
                        self.exception_string = ""
                breakpoint_data = struct.unpack(self.byte_order + self.cp_format + self.idx_format,
                                                data[3:])
                breakpoint = self._get_breakpoint(breakpoint_data)

                src_name = str(breakpoint[0].function.source_name)
                self.coverage_info[src_name][str(breakpoint[0].line)] = True
                self.send_breakpoint(breakpoint[0])

                self.prompt = True

                return DEBUGGER_ACTION_NONE
            elif buffer_type == JERRY_DEBUGGER_EXCEPTION_STR:
                self.exception_string += data[3:]

            elif buffer_type == JERRY_DEBUGGER_EXCEPTION_STR_END:
                self.exception_string += data[3:]

            else:
                raise Exception("Unknown message")

        return DEBUGGER_ACTION_NONE

    # pylint: disable=too-many-statements
    def _parse_source(self, data):
        source_code = ""
        source_code_name = ""
        function_name = ""
        stack = [{"line": 1,
                  "column": 1,
                  "name": "",
                  "lines": [],
                  "offsets": []}]
        new_function_list = {}

        while True:
            if data is None:
                return "Error: connection lost during source code receiving"

            buffer_type = ord(data[2])
            buffer_size = ord(data[1]) - 1

            if buffer_type == JERRY_DEBUGGER_PARSE_ERROR:
                return ""

            elif buffer_type in [JERRY_DEBUGGER_SOURCE_CODE, JERRY_DEBUGGER_SOURCE_CODE_END]:
                source_code += data[3:]

            elif buffer_type in [JERRY_DEBUGGER_SOURCE_CODE_NAME,
                                 JERRY_DEBUGGER_SOURCE_CODE_NAME_END]:
                source_code_name += data[3:]

            elif buffer_type in [JERRY_DEBUGGER_FUNCTION_NAME, JERRY_DEBUGGER_FUNCTION_NAME_END]:
                function_name += data[3:]

            elif buffer_type == JERRY_DEBUGGER_PARSE_FUNCTION:
                position = struct.unpack(self.byte_order + self.idx_format + self.idx_format,
                                         data[3: 3 + 4 + 4])

                stack.append({"source": source_code,
                              "source_name": source_code_name,
                              "line": position[0],
                              "column": position[1],
                              "name": function_name,
                              "lines": [],
                              "offsets": []})
                function_name = ""

            elif buffer_type in [JERRY_DEBUGGER_BREAKPOINT_LIST,
                                 JERRY_DEBUGGER_BREAKPOINT_OFFSET_LIST]:
                name = "lines"
                if buffer_type == JERRY_DEBUGGER_BREAKPOINT_OFFSET_LIST:
                    name = "offsets"

                buffer_pos = 3
                while buffer_size > 0:
                    line = struct.unpack(self.byte_order + self.idx_format,
                                         data[buffer_pos: buffer_pos + 4])
                    stack[-1][name].append(line[0])
                    buffer_pos += 4
                    buffer_size -= 4

            elif buffer_type == JERRY_DEBUGGER_BYTE_CODE_CP:
                byte_code_cp = struct.unpack(self.byte_order + self.cp_format,
                                             data[3: 3 + self.cp_size])[0]

                func_desc = stack.pop()

                # We know the last item in the list is the general byte code.
                if not stack:
                    func_desc["source"] = source_code
                    func_desc["source_name"] = source_code_name

                function = JerryFunction(stack,
                                         byte_code_cp,
                                         func_desc["source"],
                                         func_desc["source_name"],
                                         func_desc["line"],
                                         func_desc["column"],
                                         func_desc["name"],
                                         func_desc["lines"],
                                         func_desc["offsets"])

                new_function_list[byte_code_cp] = function

                if not stack:
                    break

            elif buffer_type == JERRY_DEBUGGER_RELEASE_BYTE_CODE_CP:
                # Redefined functions are dropped during parsing.
                byte_code_cp = struct.unpack(self.byte_order + self.cp_format,
                                             data[3: 3 + self.cp_size])[0]

                if byte_code_cp in new_function_list:
                    del new_function_list[byte_code_cp]
                    self.send_bytecode_cp(byte_code_cp)
                else:
                    self._release_function(data)

            else:
                raise Exception("Unexpected message")

            data = self.get_message(True)

        # Copy the ready list to the global storage.
        self.function_list.update(new_function_list)

        for function in new_function_list.values():
            if str(function.source_name) not in self.coverage_info:
                self.coverage_info[str(function.source_name)] = {}

            for line, breakpoint in function.lines.items():
                self.line_list.insert(line, breakpoint)

                if str(breakpoint.line) not in self.coverage_info[str(function.source_name)]:
                    self.coverage_info[function.source_name][str(breakpoint.line)] = False

    def _release_function(self, data):
        byte_code_cp = struct.unpack(self.byte_order + self.cp_format,
                                     data[3: 3 + self.cp_size])[0]

        del self.function_list[byte_code_cp]
        self.send_bytecode_cp(byte_code_cp)


    def _get_breakpoint(self, breakpoint_data):
        function = self.function_list[breakpoint_data[0]]
        offset = breakpoint_data[1]

        if offset in function.offsets:
            return (function.offsets[offset], True)

        if offset < function.first_breakpoint_offset:
            return (function.offsets[function.first_breakpoint_offset], False)

        nearest_offset = -1

        for current_offset in function.offsets:
            if current_offset <= offset and current_offset > nearest_offset:
                nearest_offset = current_offset

        return (function.offsets[nearest_offset], False)


class DebuggerPrompt(Cmd):
    def __init__(self, debugger):
        Cmd.__init__(self)
        self.debugger = debugger

    def do_continue(self, _):
        """ Continue execution """
        self.debugger.get_continue()
    do_c = do_continue


def main():
    args = arguments_parse()

    debugger = JerryDebugger(args.address, args.coverage_output)

    prompt = DebuggerPrompt(debugger)

    while True:
        result = debugger.process_messages()

        if result == DEBUGGER_ACTION_END:
            break
        elif result == DEBUGGER_ACTION_PROMPT:
            prompt.onecmd('c')

        continue

    # Save coverage information into the output file
    with open(args.coverage_output, 'w') as outfile:
        coverage_info = debugger.get_coverage_info()
        for func_name in coverage_info:
            breakpoints = coverage_info[func_name]
            coverage_info[func_name] = {int(k) : v for k, v in breakpoints.items()}

        json.dump(coverage_info, outfile)
        print("Finished the execution.")


if __name__ == "__main__":
    try:
        main()
    except socket.error as error_msg:
        ERRNO = error_msg.errno
        MSG = str(error_msg)
        if ERRNO == 111:
            sys.exit("Failed to connect to the JerryScript debugger.")
        elif ERRNO == 32 or ERRNO == 104:
            sys.exit("Connection closed.")
        else:
            sys.exit("Failed to connect to the JerryScript debugger.\nError: %s" % (MSG))
