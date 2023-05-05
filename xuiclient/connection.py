import urllib.request
import urllib.parse
from urllib.error import HTTPError
import http.client
import json as _json
import typing

# cookies
from http.cookiejar import (
    CookieJar, LWPCookieJar, Cookie as _CookieObject
)

class _NoRedirectionHandler(urllib.request.HTTPErrorProcessor):
    def http_response(self, _, response):
        return response

    https_response = http_response

class _HTTPErrorHandler(urllib.request.BaseHandler):
    def http_error_default(self, req, fp, code, msg, hdrs):
        return HTTPError(req.full_url, code, msg, hdrs, fp)

def _prepare_url(url: str, params: typing.MutableMapping[str, str] = {}) -> str:
    splitedurl = urllib.parse.urlparse(url.lstrip())

    if splitedurl.username and splitedurl.password:
        import warnings
        warnings.warn(
            "don't use username and password in url, those are ignored.", category=UserWarning
        )

    if not splitedurl.scheme:
        raise ValueError(
            f"Invalid URL {url!r}: No scheme supplied. "
            f"Perhaps you meant http://{url}?"
        )
    
    if not splitedurl.scheme in ("https", "http"):
        raise ValueError(
            f"Invalid URL {url!r}: Supported only https and http protocols."
        )

    scheme, host, port, path, query, fragment = (
        splitedurl.scheme, splitedurl.hostname, splitedurl.port,
        splitedurl.path, splitedurl.query, splitedurl.fragment
    )

    if not host:
        raise ValueError(f"Invalid URL {url!r}: No host supplied")
    
    if not path:
            path = "/"
    
    if params:
        params = urllib.parse.urlencode(params)

        if query:
            query = f"{query}&{params}"
        else:
            query = params
    
    if port:
        host += ":" + str(port)
    
    return urllib.parse.urlunparse((scheme, host, path, None, query, fragment))

def build_request(
    method: str, url: str, data: typing.Union[str, dict, bytes, None] = None,
    json: typing.Optional[dict] = None, params: typing.MutableMapping[str, str] = {},
    headers: typing.MutableMapping[str, str] = {},
    proxy: typing.Optional[typing.Tuple[str, str]] = None
) -> urllib.request.Request:
    """
    urllib.request.Request builder.
    """
    if json is not None and data is None:
        data = _json.dumps(json)
    
    if isinstance(data, bytes):
        data = data
    elif isinstance(data, str):
        data = data.encode("utf-8")
    elif isinstance(data, dict):
        data = urllib.parse.urlencode(data).encode("utf-8")

    req = urllib.request.Request(
        _prepare_url(url, params), data, headers, method=method
    )
    if proxy:
        req.set_proxy(*proxy)
    
    return req

def dial(
    req: urllib.request.Request, auth: typing.Optional[typing.Tuple[str, str]] = None,
    cookies: typing.Union[dict, CookieJar, None] = None, raise_for_error: bool = False,
    redirects: bool = True, timeout: float = 30, debuglevel: bool = False
) -> http.client.HTTPResponse:
    """
    Sends request and returns response.
    """
    opener = urllib.request.OpenerDirector()
    
    # Default handlers
    if hasattr(http.client, "HTTPSConnection"):
        opener.add_handler(urllib.request.HTTPSHandler(debuglevel=int(debuglevel)))
    
    opener.add_handler(urllib.request.HTTPHandler(debuglevel=int(debuglevel)))
    opener.add_handler(urllib.request.DataHandler())
    opener.add_handler(urllib.request.ProxyHandler())
    opener.add_handler(urllib.request.UnknownHandler())
    opener.add_handler(urllib.request.HTTPErrorProcessor())

    # Error handler
    opener.add_handler(urllib.request.HTTPDefaultErrorHandler() if raise_for_error else _HTTPErrorHandler())

    if not redirects:
        opener.add_handler(_NoRedirectionHandler())
    else:
        opener.add_handler(urllib.request.HTTPRedirectHandler())

    # authorization handler
    if auth:
        authorization = urllib.request.HTTPPasswordMgrWithDefaultRealm()
        authorization.add_password(None, req._full_url, auth[0], auth[1])
        opener.add_handler(urllib.request.HTTPBasicAuthHandler(authorization))
    
    if cookies:
        if isinstance(cookies, CookieJar):
            pass
        else:
            _cookies = CookieJar()
            for k, v in cookies.items():
                _cookies.set_cookie(
                    _CookieObject(0, k, v, None, False, "", False, False, "/", True, True, None, False, None, None, {}, False)
                )
            
            cookies = _cookies
    
    if not cookies is None:
        opener.add_handler(
            urllib.request.HTTPCookieProcessor(cookies)
        )
    
    return opener.open(req, timeout=timeout)

def to_json(resp) -> typing.Union[list, dict]:
    """
    Shorthand for `json.loads(resp.read())`.
    """
    return _json.loads(resp.read())
