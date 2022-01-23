#  coding: utf-8
import socketserver
import re
from datetime import datetime
from os import getcwd
from pathlib import Path

# Copyright 2013 Abram Hindle, Eddie Antonio Santos
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
#
# Furthermore it is derived from the Python documentation examples thus
# some of the code is Copyright © 2001-2013 Python Software
# Foundation; All Rights Reserved
#
# http://docs.python.org/2/library/socketserver.html
#
# run: python freetests.py

# try: curl -v -X GET http://127.0.0.1:8080/


BASE_PATH = 'www'


class ContentType():
    HTML = 'text/html'
    CSS = 'text/css'
    JSON = 'text/json'
    PLAIN = 'text/plain'
    UTF8 = '; charset=UTF-8'

    @staticmethod
    def content_type(filepath):
        filepath = str(filepath)
        if re.search(r'.html?$', filepath):
            return ContentType.HTML
        elif re.search(r'.css$', filepath):
            return ContentType.CSS
        elif re.search(r'.json$', filepath):
            return ContentType.JSON
        else:
            return ContentType.PLAIN


class MyWebServer(socketserver.BaseRequestHandler):
    def handle(self):
        self.data = self.request.recv(1024).strip()
        header = MyWebServer.parse_header(self.data.decode('utf=8'))
        path = header['path']
        posix_path = Path(getcwd()) / BASE_PATH / path[1:]
        posix_path = posix_path.resolve()
        root = Path(f'{getcwd()}/{BASE_PATH}/')
        found = False
        if not is_child_dir(root, posix_path):
            self.code = 404
        elif posix_path.is_dir():
            posix_path = posix_path / 'index.html'
            if path[-1] == '/':
                self.code = 200
            else:
                self.code = 301
        else:
            self.code = 200
        if posix_path.exists():
            f = open(posix_path, 'rb')
            self.file = f.read()
            f.close()
            found = True
        if not found:
            self.code = 404
        if header['method'] != 'GET':
            self.code = 405
            found = False
        self.content_length = len(self.file) if found else 0
        response = MyWebServer.response_header(self.code,
                ContentType.content_type(posix_path) + ContentType.UTF8,
                self.content_length, header['path'])
        if found:
            response += self.file
        self.request.sendall(response)

    @staticmethod
    def parse_header(data):
        regex = [
            r'(\w+) (\/(?:[^\/?\s]+\/?)*)(?:\b|\s|\?)?(?:\?((?:\w+=\w+&?)+)?)?\s?HTTP\/(\d\.\d)\r\n',
            r'Host: (.+)\r\n',
            r'User-Agent: (.+)\r\n',
            r'Accept: (.+)'
        ]
        search = [re.search(r, data) for r in regex]
        return {
            'method': search[0].group(1),
            'path': search[0].group(2),
            'query': search[0].group(3),
            'version': search[0].group(4),
            'host': search[1].group(1),
            'user-agent': search[2].group(1),
            'accept': search[3].group(1) if search[3] else '*/*'
        }

    @staticmethod
    def response_header(status_code, content_type, content_length, location):
        curr_time = datetime.utcnow()
        resp = [
            f'HTTP/1.1 {status_code} {MyWebServer.code_msg(status_code)}',
            'Server: very not sketchy/1.0',
            f'Date: {curr_time.strftime("%a, %d %b %Y %H:%M:%S GMT")}',
            f'Connection: keep-alive',
        ]
        if status_code == 301:
            resp.append(f'Location: {location}/')
        if status_code < 400:
            resp += [
                f'Content-Type: {content_type}',
                f'Content-Length: {content_length}',
            ]
        endl = '\r\n'
        return bytearray(endl.join(resp) + (2 * endl), 'utf-8')

    def code_msg(status_code):
        if status_code == 200:
            return 'OK'
        elif status_code == 301:
            return 'Moved Permanently'
        elif status_code == 302:
            return 'Found'
        elif status_code == 404:
            return 'Not Found'
        elif status_code == 405:
            return 'Method Not Allowed'
        elif status_code == 502:
            return 'Bad Gateway'
        elif status_code == 503:
            return 'Service Unavailable'


def is_child_dir(path1, path2):
    path1 = str(path1)
    path2 = str(path2)
    return bool(re.match(path1, path2))


if __name__ == "__main__":
    HOST, PORT = "localhost", 8080

    socketserver.TCPServer.allow_reuse_address = True
    # Create the server, binding to localhost on port 8080
    server = socketserver.TCPServer((HOST, PORT), MyWebServer)

    # Activate the server; this will keep running until you
    # interrupt the program with Ctrl-C
    server.serve_forever()
