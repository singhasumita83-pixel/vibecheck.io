import os
import sys

# Ensure the root project directory is on sys.path
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from app import app as flask_app

class VercelPathFix:
    """
    WSGI Middleware to restore original request paths when running under Vercel rewrites.
    On Vercel, when a rewrite directs to /api/index, the original path is preserved in
    HTTP_X_MATCHED_PATH (or x-matched-path). If missing, /api/index is safely stripped.
    """
    def __init__(self, wsgi_app):
        self.wsgi_app = wsgi_app

    def __call__(self, environ, start_response):
        matched = environ.get("HTTP_X_MATCHED_PATH")
        path_info = environ.get("PATH_INFO", "")

        if matched:
            environ["PATH_INFO"] = matched
        elif path_info.startswith("/api/index"):
            cleaned = path_info[len("/api/index"):]
            if cleaned.startswith(".py"):
                cleaned = cleaned[3:]
            environ["PATH_INFO"] = cleaned if cleaned else "/"

        return self.wsgi_app(environ, start_response)

flask_app.wsgi_app = VercelPathFix(flask_app.wsgi_app)
app = flask_app
