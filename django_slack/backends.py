import pprint

from six.moves import urllib

from . import app_settings
from .utils import Backend, from_dotted_path

class UrllibBackend(Backend):
    def send(self, url, data):
        r = urllib.request.urlopen(urllib.request.Request(
            url,
            urllib.parse.urlencode(data).encode('utf-8'),
        ))

        result = r.read().decode('utf-8')

        self.validate(r.headers['content-type'], result)

class RequestsBackend(Backend):
    def __init__(self):
        # Lazily import to avoid dependency
        import requests

        self.session = requests.Session()

    def send(self, url, data):
        r = self.session.post(url, data=data, verify=False)

        self.validate(r.headers['Content-Type'], r.text)

class ConsoleBackend(Backend):
    def send(self, url, data):
        print("I: Slack message:")
        pprint.pprint(data, indent=4)
        print("-" * 79)

class DisabledBackend(Backend):
    def send(self, url, data):
        pass

try:
    from celery import shared_task
except ImportError:
    pass
else:
    @shared_task
    def celery_send(*args, **kwargs):
        from_dotted_path(app_settings.BACKEND_FOR_QUEUE)().send(*args, **kwargs)

    class CeleryBackend(Backend):
        def __init__(self):
            # Check we can import our specified backend up-front
            from_dotted_path(app_settings.BACKEND_FOR_QUEUE)()

        def send(self, *args, **kwargs):
            # Send asynchronously via Celery
            celery_send.delay(*args, **kwargs)

Urllib2Backend = UrllibBackend # For backwards-compatibility
