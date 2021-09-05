#!/usr/bin/env python3

from sys import argv
import urllib.request
from http.server import BaseHTTPRequestHandler, HTTPServer
from logging import getLogger, StreamHandler, DEBUG

logger = getLogger(__name__)
handler = StreamHandler()
handler.setLevel(DEBUG)
logger.setLevel(DEBUG)
logger.addHandler(handler)
logger.propagate = False

destPort = 5001

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

        # proxy
        url = 'http://127.0.0.1:{0}{1}'.format(destPort, self.path)
        try:
            req = urllib.request.Request(url, None, self.headers)
            with urllib.request.urlopen(req) as res:
                body = res.read()
                logger.info("\nPOST {0}\nRepStatus: {1}\nRepBody:\n{2}".format(
                    self.getHeadersText(), res.status, body.decode('utf-8')))
        except Exception as e:
            logger.info("\nPOST {0}\nBody:\n{1}\nerr={2}".format(self.getHeadersText(), post_data.decode('utf-8'), e))

        self._set_response()
        self.wfile.write("GET request for {}".format(self.path).encode('utf-8'))

    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)

        # proxy
        url = 'http://127.0.0.1:{0}{1}'.format(destPort, self.path)
        try:
            req = urllib.request.Request(url, post_data, self.headers)
            with urllib.request.urlopen(req) as res:
                body = res.read()
                logger.info("\nPOST {0}\nBody:\n{1}\nRepStatus: {2}\nRepBody:\n{3}".format(
                    self.getHeadersText(), post_data.decode('utf-8'), res.status, body.decode('utf-8')))
        except Exception as e:
            logger.info("\nPOST {0}\nBody:\n{1}\nerr={2}".format(self.getHeadersText(), post_data.decode('utf-8'), e))

        self._set_response()
        self.wfile.write(body)

def run(server_class=HTTPServer, handler_class=DebugServer, port=5000):
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
    if len(argv) == 3:
        port = int(argv[1])
        destPort = int(argv[2])
        run(port=port)
    else:
        run()
