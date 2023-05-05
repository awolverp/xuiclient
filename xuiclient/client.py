from urllib.parse import urlparse
import os.path
import typing

from . import connection, types, protocols

class LoginError(Exception):
    pass

class UnknownError(Exception):
    pass

class Client:
    def __init__(
        self, server_url: str, cookie_file: typing.Optional[str] = None, timeout: float = 30
    ) -> None:
        """
        XUI client - control your xui panel.

        `server_url` is your server address, e.g. 'http://127.0.0.1:54321'.
        do not set '/' end of server address.
        
        `cookie_file` is file address that client saves cookies into it
        to prevent loginning each times. can be `None`.

        you can specify requests timeout by `timeout` parameter.
        """
        self.server_url = server_url

        s = urlparse(self.server_url)
        self.hostname = s.hostname
        self.port = s.port

        self.cookies = connection.LWPCookieJar(cookie_file)
        self._load_cookies()

        self.timeout = timeout
    
    def _load_cookies(self):
        """
        Loads cookies from file.
        """
        if self.cookies.filename and os.path.exists(self.cookies.filename):
            self.cookies.load()

    def _save_cookies(self):
        """
        Saves cookies into file.
        """
        if self.cookies.filename:
            self.cookies.save()
    
    def _is_success(self, data: dict) -> bool:
        data["msg"] = data.get("msg", "").strip(": \n")
        return data.get("success", False)

    def _request(
        self, method: str, path: str, data: dict = None, redirects: bool = True, asjson: bool = True
    ) -> typing.Union[dict, list, int]:
        """
        Sends request and returns response.
        """
        try:
            resp = connection.dial(
                connection.build_request(
                    method, self.server_url+path, data=data
                ),
                cookies=self.cookies,
                raise_for_error=asjson,
                redirects=redirects,
                timeout=self.timeout
            )
        except connection.HTTPError as e:
            if e.headers["Location"] == "/":
                raise LoginError("Please login first.") from None

            raise UnknownError(
                f"Unknown error occurred (path '{path}')"
            )

        if asjson:
            res = connection.to_json(resp)
        else:
            res = resp.status

        resp.close()
        return res
    
    @property
    def loggined(self) -> bool:
        """
        Returns `True` if loggined.
        """
        for c in self.cookies:
            if c.name == "session":
                return True
        
        return False

    def login(self, username: str, password: str) -> None:
        """
        Login into panel.

        *If session cookie is exist in cookie file, it will not be re-login.

        *Raises `LoginError` if login failed.
        """
        if self.loggined:
            return
        
        data = self._request("POST", "/login", {"username":username,"password":password})
        if not data.get("success", False):
            raise LoginError(
                f"cannot login - check your username and password: {username}/{password}"
            )

        self._save_cookies()

    def logout(self) -> None:
        """
        Logout from panel.

        *If session cookie isn't exist in cookie file, it doesn't need to logout.

        *Raises `ValueError` if logout failed.
        """
        if not self.loggined:
            return None
        
        status_code = self._request("GET", "/logout", redirects=False, asjson=False)
        if status_code != 307:
            raise ValueError(
                "Logout failed!"
            )

        self.cookies.clear()
        self._save_cookies()

    def get_status(self) -> types.Status:
        """
        Returns server status.
        """
        data = self._request("POST", "/server/status")
        return types.Status(**data["obj"])
    
    def get_settings(self) -> types.Settings:
        """
        Returns settings information.
        """
        data = self._request("POST", "/xui/setting/all")
        return types.Settings(**data["obj"])

    def get_lastest_xray_version(self) -> str:
        """
        Returns latest XRay service version.
        """
        data = self._request("POST", "/server/getXrayVersion")
        if self._is_success(data):
            return data["obj"][0]
        
        raise UnknownError(data["msg"])
    
    def is_xray_latest_version(self) -> bool:
        return self.get_status().xray.version == self.get_lastest_xray_version()

    def install_new_xray_service(self, version: str):
        """
        Installs new XRay service.
        """
        data = self._request("POST", "/server/installXray/"+version)
        if self._is_success(data):
            return data["obj"]
        
        raise UnknownError(data["msg"])
    
    def update_settings(self, settings: types.Settings) -> None:
        """
        Updates settings.

        *Recommend to use `get_settings()` and use `Settings` type to update settings.
        With this function may loss data.

        Example::

            setting = cli.get_settings()
            # your changes
            cli.update_settings(setting)
        """
        body = {
            "webListen": settings.webListen,
            "webPort": str(settings.webPort),
            "webCertFile": settings.webCertFile,
            "webKeyFile": settings.webKeyFile,
            "webBasePath": settings.webBasePath,
            "tgBotEnable": str(settings.tgBotEnable).lower(),
            "tgBotToken": settings.tgBotToken,
            "tgBotChatId": str(settings.tgBotChatId),
            "tgRunTime": settings.tgRunTime,
            "xrayTemplateConfig": settings.xrayTemplateConfig,
            "timeLocation": settings.timeLocation
        }
        data = self._request("POST", "/xui/setting/update", body)
        if not self._is_success(data):
            raise UnknownError(data["msg"])

    def update_user(
        self, current_username: str, current_password: str,
        new_username: str, new_password: str
    ) -> None:
        """
        Updates username and password.

        *After update, it tries to logout and login with new username and password to avoid some problems.
        """
        data = self._request("POST", "/xui/setting/updateUser", {
            "oldUsername": current_username, "oldPassword": current_password,
            "newUsername": new_username, "newPassword": new_password
        })
        
        if not self._is_success(data):
            raise UnknownError(
                f"cannot update user - check your current username and password: {current_username}/{current_password}"
            )
        
        self.logout()
        self.login(new_username, new_password)
    
    def get_email_ips(self, email: str) -> typing.List[str]:
        """
        Returns IPs of an email.
        """
        data = self._request("POST", "/xui/inbound/clientIps/" + email)
        return data["obj"] if isinstance(data["obj"], list) else []

    def clear_email_ips(self, email: str) -> bool:
        """
        Clears IPs of an email.
        """
        data = self._request("POST", "/xui/inbound/clearClientIps/" + email)
        return data["success"]

    def get_all_inbounds(self) -> typing.Generator[protocols._ProtocolsBase, None, None]:
        """
        Returns all inbounds.
        """
        data = self._request("POST", "/xui/inbound/list")
        return (protocols.PROTOCOLS[d["protocol"]]._unserialize(d) for d in data["obj"])

    def get_inbound(self, id: int) -> typing.Union[protocols._ProtocolsBase, None]:
        """
        *Only 'NidukaAkalanka/x-ui-english' supported this.

        Returns the inbound which has specified id.

        *Returns `None` if not exists.
        """
        data = self._request("GET", "/xui/API/inbounds/get/" + str(id))
        if not data["success"]:
            return None
        
        return protocols.PROTOCOLS[data["obj"]["protocol"]]._unserialize(data["obj"])

    def add_inbound(self, inbound: protocols._ProtocolsBase) -> int:
        """
        Adds new inbound and returns id of that.
        """
        data = self._request("POST", "/xui/inbound/add", inbound._serialize())
        if not self._is_success(data):
            if "端口已存在" in data["msg"]:
                raise ValueError(
                    f"port is exists: {inbound.port}"
                )
            
            raise UnknownError(data["msg"])
        
        return data["obj"]["id"]
    
    def add_inbounds_many(self, *inbounds: protocols._ProtocolsBase) -> typing.List[int]:
        """
        Adds new inbounds and returns list of ids.
        """
        ids = []
        for i in inbounds:
            ids.append(self.add_inbound(i))
        
        return ids

    def delete_inbound(self, id: int) -> None:
        """
        Deletes inbound which has specified id.
        """
        self._request("POST", "/xui/inbound/del/"+str(id))

    def update_inbound(self, id: int, inbound: protocols._ProtocolsBase) -> int:
        """
        Changes one inbound which has specified id to another that you specified.
        """
        data = self._request("POST", "/xui/inbound/update/"+str(id), inbound._serialize())
        return data["success"]
