"""
Vaxilu (v1) -> NidukaAkalanka (v2) ->
"""
from http.cookies import SimpleCookie
import aiohttp
import asyncio
import typing
import json

from . import types, inbounds

class LoginError(Exception):
    pass

class UnknownError(Exception):
    pass

class _GetCookies:
    def __init__(self) -> None:
        self.obj = {} # type: dict[str, str]
    
    def load(self, __iter: SimpleCookie[str]):
        for k,v in __iter.items():
            self.obj[k] = v.value
    
    def __dict__(self):
        return self.obj

def _load_cookies(filename: str) -> dict:
    try:
        with open(filename, "r") as f:
            data = f.read()
        
        return dict(i.split(":", 2) for i in data.splitlines())
    except FileNotFoundError:
        return {}

def _save_cookies(obj: dict, filename: str) -> None:
    with open(filename, "w") as f:
        f.write(
            "\n".join(
                f"{k}:{v}" for k,v in obj.items()
            )
        )

class VaxiluClient:
    """
    Vaxilu client
    """

    _VERSION_URLS = {
        "login" : ("POST", "/login"),
        "logout": ("GET", "/logout"),
        "get_status": ("POST", "/server/status"),
        "get_settings": ("POST", "/xui/setting/all"),
        "restart_panel": ("POST", "/xui/setting/restartPanel"),
        "get_inbounds_list": ("POST", "/xui/inbound/list"),
        "add_inbound": ("POST", "/xui/inbound/add"),
        "update_inbound": ("POST", "/xui/inbound/update/%d"),
        "delete_inbound": ("POST", "/xui/inbound/del/%d"),
    }

    def __init__(
        self,
        server_url: str,
        cookie_file: typing.Optional[str] = None,
        timeout: float = 20,
        loop: typing.Optional[asyncio.AbstractEventLoop] = None,
        **kwargs
    ) -> None:
        self.session = aiohttp.ClientSession(
            base_url=server_url,
            connector=aiohttp.TCPConnector(
                ssl=False, use_dns_cache=True, ttl_dns_cache=60
            ),
            timeout=aiohttp.ClientTimeout( # type: ignore
                total=timeout
            ),
            **kwargs
        )

        self.cookie_file = cookie_file
        
        if cookie_file:
            self.cookies = _load_cookies(cookie_file)
        else:
            self.cookies = {}

        self.loop = loop

    @property
    def server_url(self) -> str:
        return str(self.session._base_url)

    @property
    def loggined(self) -> bool:
        return bool(self.cookies)

    async def _send_request(
        self,
        urlkey: str,
        urlargs: typing.Tuple = (),
        *,
        params: typing.Optional[dict] = None,
        json: typing.Optional[dict] = None,
        allow_redirects: bool = False,
        cookiejar: typing.Optional[_GetCookies] = None
    ) -> typing.Any:
        method, url = self._VERSION_URLS[urlkey]
        async with self.session.request(
            method, url % urlargs, params=params, json=json,
            allow_redirects=allow_redirects, cookies=self.cookies
        ) as response:
            response.raise_for_status()

            # redirect status 310 > x >= 300
            if (310 > response.status >= 300) and response.headers["Location"] == "/":
                raise LoginError("login first")

            if cookiejar:
                cookiejar.load(response.cookies)

            return await response.json()

    async def login(self, username: str, password: str) -> None:
        """
        Logins to panel.

        - If session cookie is exist in cookie file, it will not be re-login.

        - Raises `LoginError` if login failed.
        """
        if self.loggined:
            return
        
        c = _GetCookies()

        data: dict = await self._send_request("login", json={"username": username, "password": password}, cookiejar=c)
        if not data.get("success", False):
            raise LoginError(
                f"cannot login - check your username and password: {username}/{password}"
            )
        
        # save cookies
        self.cookies = c.__dict__()
        if self.cookie_file:
            _save_cookies(self.cookies, self.cookie_file)

    async def logout(self) -> None:
        """
        Logout from panel.

        - If session cookie isn't exist in cookie file, it doesn't need to logout.

        - Raises `ValueError` if logout failed.
        """
        if not self.loggined:
            return
        
        try:
            await self._send_request("logout")
        except LoginError:
            pass
        else:
            raise ValueError("logout failed!")

        self.cookies.clear()
        if self.cookie_file:
            _save_cookies(self.cookies, self.cookie_file)

    async def get_server_status(self) -> types.ServerStatusResponse:
        data: dict = await self._send_request("get_status")
        if not data.get("success", False):
            raise UnknownError(data.get("msg", "").strip())

        return types.ServerStatusResponse(**data["obj"])

    async def get_settings(self) -> types.SettingsResponse:
        data: dict = await self._send_request("get_settings")
        if not data.get("success", False):
            raise UnknownError(data.get("msg", "").strip())

        return types.SettingsResponse(**data["obj"])

    async def restart_panel(self) -> None:
        data: dict = await self._send_request("restart_panel")
        if not data.get("success", False):
            raise UnknownError(data.get("msg", "").strip())

    async def get_inbounds_list(self) -> typing.AsyncGenerator[inbounds.Inbound, None]:
        data: dict = await self._send_request("get_inbounds_list")
        if not data.get("success", False):
            raise UnknownError(data.get("msg", "").strip())
    
        for i in data["obj"]:
            yield inbounds.Inbound(**i)

    async def add_inbound(self, obj: inbounds.Inbound) -> None:
        data: dict = await self._send_request("add_inbound", json=inbounds._cast_to_dict(obj))
        if not data.get("success", False):
            raise UnknownError(data.get("msg", "").strip())
    
    async def update_inbound(self, inbound_id: int, new_inbound: inbounds.Inbound) -> None:
        data: dict = await self._send_request(
            "update_inbound", (inbound_id,),
            json=inbounds._cast_to_dict(new_inbound)
        )
        if not data.get("success", False):
            raise UnknownError(data.get("msg", "").strip())

    async def delete_inbound(self, inbound_id: int) -> None:
        data: dict = await self._send_request("delete_inbound", (inbound_id,))
        if not data.get("success", False):
            raise UnknownError(data.get("msg", "").strip())

    async def close(self):
        await self.session.close()

    def __del__(self) -> None:
        if self.loop and not self.session.closed:
            self.loop.run_until_complete(self.session.close())

class NidukaAkalankaClient(VaxiluClient):
    def __init__(
        self,
        server_url: str,
        cookie_file: typing.Optional[str] = None,
        timeout: float = 20,
        loop: typing.Optional[asyncio.AbstractEventLoop] = None,
        **kwargs
    ) -> None:
        super().__init__(server_url, cookie_file, timeout, loop, **kwargs)
        self._VERSION_URLS["get_inbound"] = ("GET", "/xui/API/inbounds/get/%d")
        self._VERSION_URLS["get_client_ips"] = ("POST", "/xui/inbound/clientIps/%s")
        self._VERSION_URLS["clear_client_ips"] = ("POST", "/xui/inbound/clearClientIps/%s")
    
    async def get_inbound(self, inbound_id: int) -> inbounds.Inbound:
        data: dict = await self._send_request("get_inbound", (inbound_id,))
        if not data.get("success", False):
            raise UnknownError(data.get("msg", "").strip())

        return inbounds.Inbound(**data["obj"])
    
    async def get_client_ips(self, email: str) -> typing.List[str]:
        data: dict = await self._send_request("get_client_ips", (email,))
        if not data.get("success", False):
            raise UnknownError(data.get("msg", "").strip())

        return data["obj"] if isinstance(data, list) else []

    async def clear_client_ips(self, email: str) -> None:
        data: dict = await self._send_request("clear_client_ips", (email,))
        if not data.get("success", False):
            raise UnknownError(data.get("msg", "").strip())

class MHSanaeiClient(VaxiluClient):
    # TODO: add get_server_db
    # TODO: add import_server_db
    # TODO: add get_new_x25519cert
    # TODO: add create_backup

    _VERSION_URLS = {
        # login
        "login" : ("POST", "/login"),
        "logout": ("GET", "/logout"),

        # server
        "get_status": ("POST", "/server/status"),
        "get_server_log": ("POST", "/server/logs/%d"),
        "get_server_config": ("POST", "/server/getConfigJson"),

        # settings
        "get_settings": ("POST", "/panel/setting/all"),
        "restart_panel": ("POST", "/panel/setting/restartPanel"),

        # inbounds
        "get_inbounds_list": ("POST", "/panel/inbound/list"),
        "add_inbound": ("POST", "/panel/inbound/add"),
        "update_inbound": ("POST", "/panel/inbound/update/%d"),
        "delete_inbound": ("POST", "/panel/inbound/del/%d"),
        "get_inbound": ("GET", "/panel/api/inbounds/get/%d"),
        "get_client_traffics": ("GET", "/panel/api/inbounds/getClientTraffics/%s"),
        "get_client_ips": ("POST", "/panel/api/inbounds/clientIps/%s"),
        "clear_client_ips": ("POST", "/panel/api/inbounds/clearClientIps/%s"),
        "add_inbound_client": ("POST", "/panel/api/inbounds/addClient"),
        "delete_inbound_client": ("POST", "/panel/api/inbounds/%d/delClient/%s"),
        "update_inbound_client": ("POST", "/panel/api/inbounds/updateClient/%s"),
        "reset_client_traffic": ("POST", "/panel/api/inbounds/%d/resetClientTraffic/%s"),
        "delete_depleted_clients": ("POST", "/panel/api/inbounds/delDepletedClients/%d"),
    }

    async def get_server_log(self, limit: int = 1000) -> typing.List[str]:
        data: dict = await self._send_request("get_server_log", (limit,))
        if not data.get("success", False):
            raise UnknownError(data.get("msg", "").strip())

        return data["obj"]

    async def get_server_config(self) -> typing.Dict[str, typing.Any]:
        data: dict = await self._send_request("get_server_config")
        if not data.get("success", False):
            raise UnknownError(data.get("msg", "").strip())

        return data["obj"]

    async def get_inbound(self, inbound_id: int) -> inbounds.Inbound:
        data: dict = await self._send_request("get_inbound", (inbound_id,))
        if not data.get("success", False):
            raise UnknownError(data.get("msg", "").strip())

        return inbounds.Inbound(**data["obj"])

    async def get_client_traffics(self, email: str) -> inbounds.ClientStat:
        data: dict = await self._send_request("get_client_traffics", (email,))
        if not data.get("success", False):
            raise UnknownError(data.get("msg", "").strip())

        return inbounds.ClientStat(**data["obj"])

    async def get_client_ips(self, email: str) -> typing.List[str]:
        data: dict = await self._send_request("get_client_ips", (email,))
        if not data.get("success", False):
            raise UnknownError(data.get("msg", "").strip())

        return data["obj"] if isinstance(data, list) else []

    async def clear_client_ips(self, email: str) -> None:
        data: dict = await self._send_request("clear_client_ips", (email,))
        if not data.get("success", False):
            raise UnknownError(data.get("msg", "").strip())

    async def add_inbound_client(
        self,
        inbound_id: int,
        *_cli: typing.Union[inbounds.VLessClient, inbounds.VMessClient, inbounds.TrojanClient, inbounds.ShadowsocksClient]
    ) -> None:
        if not _cli:
            return

        jsondata = {
            "id": inbound_id,
            "settings": json.dumps({"clients": [inbounds._asdict_inner(c, dict, True) for c in _cli]})
        }
        data: dict = await self._send_request("add_inbound_client", json=jsondata)
        if not data.get("success", False):
            raise UnknownError(data.get("msg", "").strip())

    async def delete_inbound_client(self, inbound_id: int, client_id: str) -> None:
        data: dict = await self._send_request("delete_inbound_client", (inbound_id, client_id))
        if not data.get("success", False):
            raise UnknownError(data.get("msg", "").strip())

    async def update_inbound_client(
        self,
        inbound_id: int,
        client_id: str,
        _cli: typing.Union[inbounds.VLessClient, inbounds.VMessClient, inbounds.TrojanClient, inbounds.ShadowsocksClient]
    ) -> None:
        jsondata = {
            "id": inbound_id,
            "settings": json.dumps({"clients": [inbounds._asdict_inner(_cli, dict, True)]})
        }
        data: dict = await self._send_request("update_inbound_client", (client_id,), json=jsondata)
        if not data.get("success", False):
            raise UnknownError(data.get("msg", "").strip())
        
    async def reset_client_traffic(self, inbound_id: int, email: str) -> None:
        data: dict = await self._send_request("delete_client_traffic", (inbound_id, email))
        if not data.get("success", False):
            raise UnknownError(data.get("msg", "").strip())

    async def delete_depleted_clients(self, inbound_id: int) -> None:
        data: dict = await self._send_request("delete_depleted_clients", (inbound_id,))
        if not data.get("success", False):
            raise UnknownError(data.get("msg", "").strip())

class Alireza0Client(MHSanaeiClient):

    # TODO: add get_server_db
    # TODO: add import_server_db
    # TODO: add get_new_x25519cert
    # TODO: add create_backup

    _VERSION_URLS = {
        # login
        "login" : ("POST", "/login"),
        "logout": ("GET", "/logout"),

        # server
        "get_status": ("POST", "/server/status"),
        "get_server_log": ("POST", "/server/logs/%d"),
        "get_server_config": ("POST", "/server/getConfigJson"),

        # settings
        "get_settings": ("POST", "/xui/setting/all"),
        "restart_panel": ("POST", "/xui/setting/restartPanel"),

        # inbounds
        "get_inbounds_list": ("GET", "/xui/API/inbounds/"),
        "add_inbound": ("POST", "/xui/API/inbounds/add"),
        "update_inbound": ("POST", "/xui/API/inbounds/update/%d"),
        "delete_inbound": ("POST", "/xui/API/inbounds/del/%d"),
        "get_inbound": ("GET", "/xui/API/inbounds/get/%d"),
        "get_client_traffics": ("GET", "/xui/API/inbounds/getClientTraffics/%s"),
        "get_client_ips": ("POST", "/xui/API/inbounds/clientIps/%s"),
        "clear_client_ips": ("POST", "/xui/API/inbounds/clearClientIps/%s"),
        "add_inbound_client": ("POST", "/xui/API/inbounds/addClient"),
        "delete_inbound_client": ("POST", "/xui/API/inbounds/%d/delClient/%s"),
        "update_inbound_client": ("POST", "/xui/API/inbounds/updateClient/%s"),
        "reset_client_traffic": ("POST", "/xui/API/inbounds/%d/resetClientTraffic/%s"),
        "delete_depleted_clients": ("POST", "/xui/API/inbounds/delDepletedClients/%d"),
    }
