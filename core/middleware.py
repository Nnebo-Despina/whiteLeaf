import base64
import hmac

from django.conf import settings
from django.http import HttpResponse


class StagingPasswordMiddleware:
    """Optional password gate for a staging site.

    Only active when STAGING_PASSWORD is set in the environment. The browser shows its own
    username/password box, so your client enters it once and you don't touch any page code.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        password = getattr(settings, "STAGING_PASSWORD", "")
        if not password or request.path.startswith("/static/"):
            return self.get_response(request)
        username = getattr(settings, "STAGING_USERNAME", "client")
        header = request.META.get("HTTP_AUTHORIZATION", "")
        if header.startswith("Basic "):
            try:
                given_user, _, given_pass = base64.b64decode(header[6:]).decode("utf-8").partition(":")
            except Exception:
                given_user = given_pass = ""
            if hmac.compare_digest(given_user, username) and hmac.compare_digest(given_pass, password):
                return self.get_response(request)
        response = HttpResponse("This preview is private. Please sign in.", status=401)
        response["WWW-Authenticate"] = 'Basic realm="Preview", charset="UTF-8"'
        return response
