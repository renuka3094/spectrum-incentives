import os

from django import template
from django.contrib.staticfiles import finders
from django.templatetags.static import static

register = template.Library()


@register.simple_tag
def static_v(path):
    """Like the built-in {% static %}, but appends `?v=<source-file-mtime>`.

    Why this exists: a browser that has ever received this URL with a
    long-lived Cache-Control header (which WhiteNoise's production/manifest
    storage sets — "cache forever, it's safe, the filename is content-
    hashed") will keep reusing that cached copy forever afterwards, no
    matter what changes on the server: not a settings fix, not deleting a
    stale staticfiles/ folder, not restarting the dev server. The browser
    simply never asks again. Tying the query string to the source file's
    actual last-modified time means every real edit produces a brand new
    URL the browser has never seen before, so a stale cache can never mask
    a real change again — this is the definitive fix, independent of
    whatever caching behavior the browser or any middleware decides to use.

    `finders.find()` looks the file up the same way collectstatic/`{% static %}`
    resolution does — via STATICFILES_DIRS / app static dirs — and works the
    same whether DEBUG is True or False, so one implementation covers local
    dev and a real deploy.
    """
    url = static(path)
    version = "0"
    try:
        abs_path = finders.find(path)
        if abs_path:
            version = str(int(os.path.getmtime(abs_path)))
    except OSError:
        pass
    return f"{url}?v={version}"
