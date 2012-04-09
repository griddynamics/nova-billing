import httplib
import json

import logging

from urlparse import urlparse


LOG = logging.getLogger(__name__)


class RestClient(object):
    debug = False
    auth_headers = {}
    management_url = ""
    
    def __init__(self, *args, **kwargs):
        for key, value in kwargs.iteritems():
            setattr(self, key, value)
    
    def http_log(self, args, kwargs, resp, body):
        if not self.debug:
            return

        string_parts = ["curl -i '%s' -X %s" % args]

        for element in kwargs['headers']:
            header = ' -H "%s: %s"' % (element, kwargs['headers'][element])
            string_parts.append(header)

        print "REQ: %s\n" % "".join(string_parts)
        if 'body' in kwargs:
            print "REQ BODY: %s\n" % (kwargs['body'])
        if resp:
            print "RESP: %s\nRESP BODY: %s\n" % (resp.status, body)

    def request(self, *args, **kwargs):
        kwargs.setdefault('headers', kwargs.get('headers', {}))
        if 'body' in kwargs:
            kwargs['headers']['Content-Type'] = 'application/json'
            kwargs['body'] = json.dumps(kwargs['body'])

        resp, body = None, None
        try:
            parsed = urlparse(args[0])
            client = httplib.HTTPConnection(parsed.netloc)
            request_uri = ("?".join([parsed.path, parsed.query])
                           if parsed.query
                           else parsed.path)
            client.request(args[1], request_uri, **kwargs)
            resp = client.getresponse()
            body = resp.read()
        finally:
            self.http_log(args, kwargs, resp, body)
        return (resp, body)

    def get(self, path):
        return self.request(self.management_url + path, "GET", headers=self.auth_headers)[1]

    def post(self, path, body):
        return self.request(self.management_url + path, "POST", body=body, headers=self.auth_headers)[1]

    def put(self, path, body):
        return self.request(self.management_url + path, "PUT", body=body, headers=self.auth_headers)[1]

    def delete(self, path):
        return self.request(self.management_url + path, "DELETE", headers=self.auth_headers)[1]


class BillingHeartClient(RestClient):
    def event(self, request):
        return self.post("/event", request)
