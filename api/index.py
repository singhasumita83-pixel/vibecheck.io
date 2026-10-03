import os
import sys
import urllib.parse

# Ensure the root project directory is on sys.path
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from app import app as flask_app

class VercelPathFix:
    """
    WSGI Middleware to restore original request paths when running under Vercel rewrites.
    Vercel passes the original matched path via the __path__ query parameter or headers.
    """
    def __init__(self, wsgi_app):
        self.wsgi_app = wsgi_app

    def __call__(self, environ, start_response):
        qs = environ.get("QUERY_STRING", "")
        if "__path__=" in qs:
            params = []
            for part in qs.split("&"):
                if part.startswith("__path__="):
                    val = urllib.parse.unquote(part[9:])
                    while val.startswith("//"):
                        val = val[1:]
                    environ["PATH_INFO"] = val if val else "/"
                elif part:
                    params.append(part)
            environ["QUERY_STRING"] = "&".join(params)
        elif environ.get("PATH_INFO", "").startswith("/api/index"):
            sub = environ["PATH_INFO"][len("/api/index"):]
            if sub.startswith(".py"):
                sub = sub[3:]
            environ["PATH_INFO"] = sub if sub else "/"

        return self.wsgi_app(environ, start_response)

flask_app.wsgi_app = VercelPathFix(flask_app.wsgi_app)
app = flask_app
