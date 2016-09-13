#! /usr/bin/env python3

import argparse # for parsing the command line arguments
import threading # for running the server in multiple threads
import socketserver
import os # for joining file paths
from email.utils import formatdate # for formatting the current date according to RFC 1123
import mimetypes # for detecting the right MIME type of a requested file

# helper class for colored console output
class style:
    RESET = '\033[0m'
    BOLD = '\033[1m'
    INFO = '\033[34m'
    FAIL = '\033[91m'
    SUCCESS = '\033[92m'
    WARNING = '\033[93m'

class HttpHandler(socketserver.StreamRequestHandler):
    # names of the folders containing the served files and error/status messages
    DOCUMENT_ROOT_DIR = 'static'
    STATUS_DIR = 'status'

    # root directory based on path of server.py
    ROOT_DIR = os.path.abspath(os.path.join(os.path.abspath(__file__), os.pardir))

    def handle(self):
        # request will be a list of all data send by the client, till the server receives a newline
        self.request = []

        # make sure to get at least one line back from client
        while True:
            line = self.rfile.readline().strip().decode('UTF-8').split()
            if line:
                self.request.append(line)
                break

        # get additionl data, till a newline is received
        while True:
            line = self.rfile.readline().strip().decode('UTF-8').split()
            if line:
                self.request.append(line)
            else:
                break

        # checking for malformatted request, resulting in a 400 response
        if (len(self.request[0]) != 3 or
                self.request[0][0] != 'GET' or # not a GET request
                self.request[0][2] != 'HTTP/1.1' or # not HTTP 1.1
                '..' in self.request[0][1]): # path of requested file contains '..', which could be otherwise used to access files outside of the document root
            statusData = self.getStatusDataFromFile('400.html')

            self.writeHttpHeader('400 Bad Request', len(statusData))
            self.wfile.write(bytes('\n', 'UTF-8'))
            self.wfile.write(statusData)

            # log request to console
            self.logRequest('400 Bad Request', style.FAIL)
            return

        try:
            path = self.request[0][1]
            # if path ends with a '/', append 'index.html'
            if path.endswith('/'):
                path += 'index.html'

            try:
                requestedData = self.getStaticDataFromFile(path)
            except IsADirectoryError:
                # if the requested path is a directory, redirect to path + '/'
                status = self.getStatusDataFromFile('301.html').decode('UTF-8')

                # replace placeholder '{url}' in 301.html with real url
                status = status.replace('{url}', path + '/')
                statusData = status.encode('UTF-8')

                self.writeHttpHeader('301 Moved Permanently', len(statusData))
                self.wfile.write(bytes('Location: ' + path + '/', 'UTF-8'))
                self.wfile.write(bytes('\r\n\r\n', 'UTF-8'))
                self.wfile.write(statusData)

                # log request to console
                self.logRequest('301 Moved Permanently', style.WARNING)
                return

            # set MIME type based on requested path, 'text/html' will be used as default if no other type can be determined
            mime = mimetypes.guess_type(path)[0]
            mime = 'text/html' if mime == 0 else mime

            # guess the correct mime type when writing the http header
            self.writeHttpHeader('200 OK', len(requestedData), mime)
            self.wfile.write(bytes('\r\n', 'UTF-8'))
            self.wfile.write(requestedData)

            # log request to console
            self.logRequest('200 OK', style.SUCCESS)
            return
        except FileNotFoundError: # return a 404 page if the requested file couldn't be found
            statusData = self.getStatusDataFromFile('404.html')

            self.writeHttpHeader('404 Not Found', len(statusData))
            self.wfile.write(bytes('\r\n', 'UTF-8'))
            self.wfile.write(statusData)

            # log request to console
            self.logRequest('404 Not Found', style.FAIL)
            return

    def getStaticDataFromFile(self, path):
        '''Helper function that returns the requested file as bytes.

        Keyword arguments:
        path -- the path of the requested file relative to the document root (DOCUMENT_ROOT_DIR)
        '''

        # try to get the requested file, retry with added '/index.html' if requested file appears to be a directory
        with open(os.path.join(self.ROOT_DIR, self.DOCUMENT_ROOT_DIR) + path, 'rb') as requestedFile:
            requestedData = requestedFile.read()
        return requestedData

    def getStatusDataFromFile(self, statusPath):
        '''Helper function that returns a specific status message file as bytes.

        Keyword arguments:
        statusPath -- the path to the requested file relative to status folder (STATUS_DIR)
        '''
        with open(os.path.join(self.ROOT_DIR, self.STATUS_DIR, statusPath), 'r') as statusFile:
            status = statusFile.read()

        # replace placeholder '{server_address}', '{server_port}' and '{date}' in 404.html with ip address and port of the server, and the current date
        status = status.replace('{server_address}', self.server.server_address[0])
        status = status.replace('{server_port}', str(self.server.server_address[1]))
        status = status.replace('{date}', formatdate(timeval=None, localtime=False, usegmt=True))
        statusData = status.encode('UTF-8')

        return statusData

    def writeHttpHeader(self, status, contentLength=0, mimeType='text/html'):
        '''Helper function that writes the correct HTTP header as response to the client.

        Keyword arguments:
        status -- the HTTP status message, e.g. '200 OK'
        contentLength -- value for Content-Length header (default 0)
        mimeType -- MIME type of the requested file (default 'text/html')
        '''
        # replace placeholders for HTTP status, current date and content length with the correct values
        # if mimeType begins with 'text/', the charset will be set to UTF-8
        header = '''HTTP/1.1 %s
Server: YetAnotherHttpServer/1.0 (Unix)
Date: %s
Content-Length: %d
Connection: close
Content-Type: %s
'''.replace('\n', '\r\n') % (status, formatdate(timeval=None, localtime=False, usegmt=True), contentLength, (mimeType + '; charset=UTF-8' if mimeType.startswith('text/') else mimeType))
        # write header as response to client
        self.wfile.write(bytes(header, 'UTF-8'))
        return

    def logRequest(self, response, textStyle=''):
        '''Helper function that prints the current response as a log entry to the console.

        Keyword arguments:
        response -- the HTTP status message, e.g. '200 OK'
        textStyle -- the style defining how the status message should appear, e.g. style.SUCCESS (default '')
        '''
        print(style.INFO + str(self.client_address), style.RESET + str(self.request), textStyle + response + style.RESET)

class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    pass

def main():
    # command line argument parsing using argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--port', dest='port', type=int, help='defines the port the server should use; if no value is given, an arbitrary unused port will be used')
    args = parser.parse_args()

    # set host and port
    host = "localhost"
    port = args.port or 0 # if no port has been specified by the user, 'port 0' selects a random unused port

    # specify the request handler
    server = ThreadedTCPServer((host, port), HttpHandler)
    ip, port = server.server_address

    # start the server itself
    server_thread = threading.Thread(target=server.serve_forever)
    server_thread.daemon = True
    server_thread.start()

    # print status message
    print(style.BOLD + 'listening on port', port)
    print('press CTRL-C to shut down the server' + style.RESET)
    print()

    # wait for the user to press enter, then shut down
    try:
        while True:
            input()
    except KeyboardInterrupt:
        print()
        print(style.BOLD + 'shutting down server...' + style.RESET)
        server.shutdown()

if __name__ == '__main__':
    main()
