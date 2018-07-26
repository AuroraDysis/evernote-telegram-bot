import http.client
import json
import re
import traceback
import ssl
from datetime import datetime
from os.path import exists
from os.path import dirname
from os.path import join
from os.path import realpath
from urllib.parse import parse_qs
from urllib.parse import urlencode
from urllib.parse import urlparse
from urllib.parse import parse_qsl

from util.cli import Console
from util.router import UrlRouter


class Request:
    def __init__(self, wsgi_environ):
        self.init_time = datetime.now()
        self.input = wsgi_environ.get('wsgi.input')
        self.method = wsgi_environ.get('REQUEST_METHOD')
        self.query_string = wsgi_environ.get('QUERY_STRING')
        self.GET = {}
        if self.query_string:
            for name, value in parse_qsl(self.query_string):
                self.GET[name] = value
        self.raw_uri = wsgi_environ.get('RAW_URI')
        self.server_protocol = wsgi_environ.get('SERVER_PROTOCOL')
        self.user_agent = wsgi_environ.get('HTTP_USER_AGENT')
        self.path = wsgi_environ.get('PATH_INFO')

    def read(self):
        if not self.input:
            return
        self.body = self.input.read()
        return self.body

    def json(self):
        data = self.body.decode()
        return json.loads(data)


class Response:
    statuses = {
        200: 'OK',
        301: 'Moved Permanently',
        302: 'Found',
        404: 'Not Found',
        500: 'Internal Server Error',
    }

    def __init__(self, body, status_code=200, headers=None):
        self.body = body if body else b''
        if headers is None:
            self.headers = [
                ('Content-Type', 'text/plain'),
                ('Content-Length', str(len(self.body))),
            ]
        if isinstance(self.body, str):
            self.body = self.body.encode() 
        status_message = self.statuses.get(status_code, 'Unknown')
        self.status_code = status_code
        self.status = '{0} {1}'.format(status_code, status_message)


class HTTPFound(Response):
    def __init__(self, redirect_url):
        headers = [('Location', redirect_url)]
        super().__init__(b'', 302, headers)


class HttpApplication:
    def __init__(self, config):
        self.config = config
        self.router = UrlRouter(config)
        self.console = Console()
        self.debug = config.get('debug', False)

    def handle_request(self, wsgi_environ):
        try:
            request = Request(wsgi_environ)
            request.read()
            handler = self.router.get_handler(request.path, request.method)
            if handler:
                request.app = self
                response = handler(request)
                if not isinstance(response, Response):
                    response = Response(body=response)
            else:
                response = Response(body=b'Page not found', status_code=404) # TODO: log to file
        except Exception:
            response = Response(body=b'Oops. Server error.', status_code=500) # TODO: log to file
        if self.debug:
            self.console_log(request, response)
        return response.status, response.headers, response.body

    def console_log(self, request, response):
        colors_map = {
            200: self.console.green,
            404: self.console.yellow,
            500: self.console.red,
        }
        message = '{0} {1} - {2}'.format(request.method, request.path, response.status)
        color = colors_map.get(response.status_code, self.console.white)
        print(color(message))


def make_request(url, method='GET', params=None, body=None, headers=None):
    parse_result = urlparse(url)
    protocol = parse_result.scheme
    hostname = parse_result.netloc
    if protocol == 'https':
        context = ssl.SSLContext()
        conn = http.client.HTTPSConnection(hostname, context=context)
    elif protocol == 'http':
        conn = http.client.HTTPConnection(hostname)
    else:
        raise Exception('Unsupported protocol {}'.format(protocol))
    if headers is None:
        headers = {}
    if method == 'POST':
        if 'Content-Type' not in headers:
            headers['Content-Type'] = 'application/x-www-form-urlencoded'
        if params and not body:
            body = urlencode(params)
    request_url = '{0}?{1}'.format(parse_result.path, parse_result.query)
    conn.request(method, request_url, body, headers)
    response = conn.getresponse()
    data = response.read()
    conn.close()
    return data
