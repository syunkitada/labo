#!/usr/bin/env python3

from sys import argv
import logging
import urllib.request
from http.server import BaseHTTPRequestHandler, HTTPServer

class DebugServer(BaseHTTPRequestHandler):
    def _set_response(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()

    def do_GET(self):
        logging.info("GET request,\nPath: %s\nHeaders:\n%s\n", str(self.path), str(self.headers))
        self._set_response()
        self.wfile.write("GET request for {}".format(self.path).encode('utf-8'))

    def do_POST(self):
        content_length = int(self.headers['Content-Length']) # <--- Gets the size of data
        post_data = self.rfile.read(content_length) # <--- Gets the data itself
        logging.info("POST request,\nPath: %s\nHeaders:\n%s\nBody:\n%s\n",
                str(self.path), str(self.headers), post_data.decode('utf-8'))
        self._set_response()

        url = 'http://localhost:9093/api/v2/alerts'
        headers = {
            'Content-Type': 'application/json',
        }
        req = urllib.request.Request(url, post_data, headers)
        with urllib.request.urlopen(req) as res:
            body = res.read()
            print("DEBUG body", res.status, body)

        self.wfile.write(body)

def run(server_class=HTTPServer, handler_class=DebugServer, port=19093):
    logging.basicConfig(level=logging.INFO)
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    logging.info('Starting httpd...0.0.0.0:{0}\n'.format(port))
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    httpd.server_close()
    logging.info('Stopping httpd...\n')

if __name__ == '__main__':
    if len(argv) == 2:
        run(port=int(argv[1]))
    else:
        run()
