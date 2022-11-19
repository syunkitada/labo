#!/usr/bin/env python3

from sys import argv
from http.server import BaseHTTPRequestHandler, HTTPServer
from logging import getLogger, StreamHandler, DEBUG

logger = getLogger(__name__)
handler = StreamHandler()
handler.setLevel(DEBUG)
logger.setLevel(DEBUG)
logger.addHandler(handler)
logger.propagate = False

class DebugServer(BaseHTTPRequestHandler):
    def _set_response(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()

    def getHeadersText(self):
        headers = []
        for key, value in self.headers.items():
            headers.append("{0}: {1}".format(key, value))
        return "\n".join(headers)

    def do_GET(self):
        logger.info("\nGET {0}".format(self.getHeadersText()))
        self._set_response()
        self.wfile.write("GET request for {}".format(self.path).encode('utf-8'))

    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        headers = []
        logger.info("\nPOST {0}\nBody:\n{1}".format(self.getHeadersText(), post_data.decode('utf-8')))
        self._set_response()
        self.wfile.write("POST request for {}".format(self.path).encode('utf-8'))

def run(server_class=HTTPServer, handler_class=DebugServer, port=5001):
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    logger.info('Starting httpd...0.0.0.0:{0}\n'.format(port))
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    httpd.server_close()
    logger.info('Stopping httpd...\n')

if __name__ == '__main__':
    if len(argv) == 2:
        run(port=int(argv[1]))
    else:
        run()
