from uuid import uuid1 as _uuid_generator
from datetime import datetime
from urllib.parse import urlencode, quote as urlquote
import json as _json
import warnings
import random
import typing
import base64
import time

from . import transmissions as _transmissions

def _base64_encode(s: str) -> str:
    return base64.b64encode(s.encode("utf-8")).decode("utf-8")

class _ProtocolsBase:
    """
    Base class for protocols.
    """

    NAME: str
    """Protocol Name"""

    id: int
    """Protocol ID in XUI database"""

    def __init__(
        self,
        upload: int = 0,
        download: int = 0,
        total_traffic: int = 0,
        remark: str = "",
        enabled: bool = True,
        expiry_time: typing.Union[datetime, int, float] = 0,
        listenning_ip: str = "",
        port: int = 0,
        tls: typing.Optional[_transmissions.TLS] = None,
        transmission: typing.Optional[_transmissions._TransmissionsBase] = None
    ) -> None:
        self.upload = int(upload) # Maybe parsed as string
        self.download = int(download) # Maybe parsed as string
        self.total_traffic = int(total_traffic) # Maybe parsed as string
        self.remark = remark

        self.enabled = enabled if type(enabled) == bool else (enabled == "true") # Maybe parsed as string
        
        self.expiry_time = int(expiry_time.timestamp()*1000) if isinstance(expiry_time, datetime) else expiry_time
        if isinstance(self.expiry_time, float):
            self.expiry_time = int(self.expiry_time*1000)

        self.listenning_ip = listenning_ip
        self.port = int(port) # Maybe parsed as string

        self.tls = tls
        self.transmission = transmission

        if self.tls and not self.transmission.SUPPORTED_SECURITY:
            raise TypeError(
                "Cannot use protocols.TLS or protocols.XTLS with %s transmisssion, is unsupported." %
                type(self.transmission).__name__
            )
        
        self.id = -1

    def set_random_port(self, force: bool = False) -> None:
        if force or self.port == 0:
            warnings.warn(
                "Please specify port - Maybe the random ports make some problems",
                category=RuntimeWarning, stacklevel=5
            )
            self.port = random.randint(10000, 65535)

    def _serialize(
        self,
        settings: dict,
        sniffing: typing.Optional[bool] = None
    ) -> dict:
        """
        Serialize as dict[str, Any] for HTTP request body.
        """
        self.set_random_port(force=False)
        
        data = {
            "up": str(self.upload),
            "down": str(self.download),
            "total": str(self.total_traffic),
            "remark": self.remark,
            "enable": self.enabled,
            "expiryTime": self.expiry_time,
            "listen": self.listenning_ip,
            "port": str(self.port),
            "protocol": self.NAME,
            "settings": _json.dumps(settings),
        }
        
        # stream settings
        data["streamSettings"] = {
            "network": self.transmission.NAME,
            self.transmission.NAME+"Settings": self.transmission._serialize()
        }

        if self.tls:
            data["streamSettings"]["security"] = self.tls.NAME
            data["streamSettings"][self.tls.NAME+"Settings"] = self.tls._serialize()
        else:
            data["streamSettings"]["security"] = "none"

        data["streamSettings"] = _json.dumps(data["streamSettings"])

        # sniffing
        if not (sniffing is None):
            data["sniffing"] = "{\"enabled\": %s, \"destOverride\":[\"http\", \"tls\"]}" % str(sniffing).lower()
        else:
            data["sniffing"] = "{}"

        return data

    def _unserialize_settings(self, data: dict) -> None:
        raise NotImplementedError
    
    def _unserialize_sniffing(self, enabled: bool) -> None:
        raise NotImplementedError("not supported (class %s)" % type(self).__name__)

    @classmethod
    def _unserialize(cls, data: dict):
        """
        Unserialize from dict[str, Any].
        """
        if data["protocol"] != cls.NAME:
            raise TypeError(
                "Invalid data for %r protocol (class %s) - this data is for %r" %
                (cls.NAME, cls.__name__, data["protocol"])
            )

        obj = cls()
        obj.upload = int(data["up"])
        obj.download = int(data["down"])
        obj.total_traffic = int(data["total"])
        obj.remark = data["remark"]
        obj.enabled = data["enable"] if type(data["enable"]) == bool else (data["enable"] == "true")
        obj.expiry_time = int(data["expiryTime"])
        obj.listenning_ip = data["listen"]
        obj.port = int(data["port"])

        # settings
        obj._unserialize_settings(_json.loads(data["settings"]))
        
        # transmission
        data["streamSettings"] = _json.loads(data["streamSettings"])

        t = _transmissions.TRANSMISSIONS[data["streamSettings"]["network"]]
        obj.transmission = t._unserialize(data["streamSettings"][t.NAME+"Settings"])

        if data["streamSettings"]["security"] == "none":
            obj.tls = None

        elif data["streamSettings"]["security"] == "tls":
            obj.tls = _transmissions.TLS._unserialize(data["streamSettings"]["tlsSettings"])
        
        elif data["streamSettings"]["security"] == "xtls":
            obj.tls = _transmissions.XTLS._unserialize(data["streamSettings"]["xtlsSettings"])
        
        # sniffing
        data["sniffing"] = _json.loads(data["sniffing"])
        if data["sniffing"]:
            obj._unserialize_sniffing(data["sniffing"]["enabled"])

        obj.id = data.get("id", -1)
        return obj
    
    def _generate_access_link(self, hostname: str, client_index: int = 0) -> str:
        raise NotImplementedError

    def generate_access_link(self, hostname: str, client_index: int = 0) -> str:
        self.set_random_port(force=False)
        return self._generate_access_link(hostname, client_index)
    
    def __repr__(self) -> str:
        return f"xuiclient.protocols.{type(self).__name__}(id={self.id}, remark={self.remark!r}, enabled={self.enabled})"

class ProtocolClient:
    """
    Client settings for protocols, which supported clients.
    """
    
    def __init__(
        self,
        email: str = "",
        ip_count_limit: int = 0,
        id: str = "", 
        alter_id: int = 0,
        total_traffic: int = 0,
        expiry_time: typing.Union[datetime, int, float] = 0,
        flow: str = ""
    ) -> None:
        self.email = email
        self.ip_count_limit = ip_count_limit
        self.id = id or str(_uuid_generator(int(time.time())))
        self.alter_id = alter_id
        self.total_traffic = total_traffic

        self.expiry_time = int(expiry_time.timestamp()*1000) if isinstance(expiry_time, datetime) else expiry_time
        if isinstance(self.expiry_time, float):
            self.expiry_time = int(self.expiry_time*1000)
    
        self.flow = flow or "xtls-rprx-direct"

    def _serialize(self, alter_id: bool = True, flow: bool = False):
        data = {
            "id": self.id,
            "email": self.email,
            "limitIp": self.ip_count_limit,
            "totalGB": self.total_traffic,
            "expiryTime": self.expiry_time
        }
        if alter_id:
            data["alterId"] = self.alter_id
        
        if flow:
            data["flow"] = self.flow
        
        return data
    
    @classmethod
    def _unserialize(cls, data: dict):
        return cls(
            data["email"], int(data["limitIp"]), data["id"],
            int(data.get("alterId", 0)), int(data["totalGB"]), int(data["expiryTime"] or 0),
            data.get("flow", "")
        )

class VMessProtocol(_ProtocolsBase):
    NAME = "vmess"

    def __init__(
        self, 
        upload: int = 0,
        download: int = 0,
        total_traffic: int = 0,
        remark: str = "",
        enabled: bool = True,
        expiry_time: typing.Union[datetime, int, float] = 0,
        listenning_ip: str = "",
        port: int = 0,
        tls: typing.Optional[_transmissions.TLS] = None,
        transmission: typing.Optional[_transmissions._TransmissionsBase] = None,
        sniffing: bool = True,
        clients: typing.Optional[typing.List[ProtocolClient]] = None,
        disable_insecure_encryption: bool = False
    ) -> None:
        if isinstance(tls, _transmissions.XTLS):
            raise TypeError(
                "Cannot use XTLS with VMess."
            )
        
        super().__init__(
            upload, download, total_traffic, remark, enabled, expiry_time, listenning_ip, port,
            tls, transmission or _transmissions.TCPTransmission()
        )

        self.sniffing = sniffing
        self.clients = clients or [ProtocolClient()]
        self.disable_insecure_encryption = disable_insecure_encryption

    def _serialize(self) -> dict:
        return super()._serialize(
            {"clients": list(i._serialize() for i in self.clients),
             "disableInsecureEncryption": self.disable_insecure_encryption},
            self.sniffing
        )
    
    def _unserialize_settings(self, data: dict) -> None:
        self.clients = list(ProtocolClient._unserialize(i) for i in data.get("clients", []))
        self.disable_insecure_encryption = data.get("disableInsecureEncryption", False)
    
    def _unserialize_sniffing(self, enabled: bool) -> None:
        self.sniffing = enabled

    def _generate_access_link(self, hostname: str, client_index: int = 0) -> str:
        network = self.transmission.NAME
        type = "none"
        host = ""
        path = ""

        if network == "tcp":
            type = "http" if self.transmission.isHTTP else "none"
            if type == "http":
                path = self.transmission.http_request.path
                host = self.transmission.http_request.headers.get("host", "")
        
        elif network == "kcp":
            type = self.transmission.camouflage
            path = self.transmission.password
        
        elif network == "ws":
            path = self.transmission.path
            host = self.transmission.headers.get("host", "")

        elif network == "http":
            network = "h2"
            path = self.transmission.path
            host = ",".join(self.transmission.hosts)
        
        elif network == "quic":
            type = self.transmission.camouflage
            host = self.transmission.encryption
            path = self.transmission.password
        
        elif network == "grpc":
            path = self.transmission.serviceName
        
        else:
            raise TypeError("unknown transmission type: %s" % network)

        if self.tls is not None and self.tls.serverName:
            hostname = self.tls.serverName

        return "vmess://" + _base64_encode(
            _json.dumps(
                {
                    "v": '2',
                    "ps": self.remark,
                    "add": hostname,
                    "port": self.port,
                    "id": self.clients[client_index].id,
                    "aid": self.clients[client_index].alter_id,
                    "net": network,
                    "type": type,
                    "host": host,
                    "path": path,
                    "tls": "none" if self.tls is None else self.tls.NAME,
                },
                indent=2
            )
        )

class Fallback:
    def __init__(self, name: str, alpn: str, path: str, dest: str) -> None:
        self.name = name
        self.alpn = alpn
        self.path = path
        self.dest = dest

    def _serialize(self) -> dict:
        return {"name": self.name, "alpn": self.alpn, "path": self.path, "dest": self.dest}

    @classmethod
    def _unserialize(cls, data: dict):
        return cls(data["name"], data["alpn"], data["path"], data["dest"])

class VLessProtocol(_ProtocolsBase):
    NAME = "vless"

    def __init__(
        self, 
        upload: int = 0,
        download: int = 0,
        total_traffic: int = 0,
        remark: str = "",
        enabled: bool = True,
        expiry_time: typing.Union[datetime, int, float] = 0,
        listenning_ip: str = "",
        port: int = 0,
        tls: typing.Optional[_transmissions.TLS] = None,
        transmission: typing.Optional[_transmissions._TransmissionsBase] = None,
        sniffing: bool = True,
        clients: typing.Optional[typing.List[ProtocolClient]] = None,
        fallbacks: typing.Optional[typing.List[Fallback]] = None
    ) -> None:
        super().__init__(
            upload, download, total_traffic, remark, enabled, expiry_time, listenning_ip, port,
            tls, transmission or _transmissions.TCPTransmission()
        )

        self.sniffing = sniffing
        self.clients = clients or [ProtocolClient()]
        self.fallbacks = fallbacks or []

    def _serialize(self) -> dict:
        flow = self.tls is not None
        
        return super()._serialize(
            {"clients": list(i._serialize(alter_id=False, flow=flow) for i in self.clients),
             "fallbacks": list(i._serialize() for i in self.fallbacks)},
            self.sniffing
        )
    
    def _unserialize_settings(self, data: dict) -> None:
        self.clients = list(ProtocolClient._unserialize(i) for i in data.get("clients", []))
        self.fallbacks = list(Fallback._unserialize(i) for i in data.get("fallbacks", []))
    
    def _unserialize_sniffing(self, enabled: bool) -> None:
        self.sniffing = enabled

    def _generate_access_link(self, hostname: str, client_index: int = 0) -> str:
        network = self.transmission.NAME
        params = {
            "type": network, "security": self.tls.NAME if self.tls is not None else "none"
        }

        if isinstance(self.transmission, _transmissions.TCPTransmission):
            if self.transmission.isHTTP:
                params["path"] = self.transmission.http_request.path

                h = self.transmission.http_request.headers.get("host", None)
                if h:
                    params["host"] = h
        
        elif isinstance(self.transmission, _transmissions.KCPTransmission):
            params["headerType"] = self.transmission.camouflage
            params["seed"] = self.transmission.password
        
        elif isinstance(self.transmission, _transmissions.WSTransmission):
            params["path"] = self.transmission.path

            h = self.transmission.headers.get("host", None)
            if h:
                params["host"] = h

        elif isinstance(self.transmission, _transmissions.HTTPTransmission):
            params["path"] = self.transmission.path
            params["host"] = ",".join(self.transmission.hosts)

        elif isinstance(self.transmission, _transmissions.QuicTransmission):
            params["quicSecurity"] = self.transmission.encryption
            params["key"] = self.transmission.password
            params["headerType"] = self.transmission.camouflage
        
        elif isinstance(self.transmission, _transmissions.GRPCTransmission):
            params["serviceName"] = self.transmission.serviceName
        
        else:
            raise TypeError("unknown transmission type: %s" % network)

        if self.tls is not None:
            if self.tls.serverName:
                hostname = self.tls.serverName
            
            if isinstance(self.tls, _transmissions.XTLS):
                params["flow"] = self.clients[client_index].flow

        return f"vless://{self.clients[client_index].id}@{hostname}:{self.port}?" \
            + urlencode(params) \
            + "#" + urlquote(self.remark)

class TrojanProtocol(_ProtocolsBase):
    NAME = "trojan"

    def __init__(
        self, 
        upload: int = 0,
        download: int = 0,
        total_traffic: int = 0,
        remark: str = "",
        enabled: bool = True,
        expiry_time: typing.Union[datetime, int, float] = 0,
        listenning_ip: str = "",
        port: int = 0,
        tls: typing.Optional[_transmissions.TLS] = None,
        tcp_accept_proxy_protocol: bool = False,
        password: typing.Optional[str] = None, # set None to generate random password
        sniffing: bool = True,
        fallbacks: typing.Optional[typing.List[Fallback]] = None
    ) -> None:
        super().__init__(
            upload, download, total_traffic, remark, enabled, expiry_time, listenning_ip, port,
            tls, _transmissions.TCPTransmission(tcp_accept_proxy_protocol)
        )

        self.password = password
        self.sniffing = sniffing
        self.fallbacks = fallbacks or []
    
    def set_random_password(self) -> None:
        self.password = "".join(
            random.choices("1234567890abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ", k=10)
        )
    
    def _serialize(self) -> dict:
        if self.password is None:
            # generate random password
            self.set_random_password()
        
        return super()._serialize(
            {"clients": [{"password":self.password, "flow":"xtls-rprx-direct"}],
             "fallbacks": list(i._serialize() for i in self.fallbacks)},
            sniffing=True
        )

    def _unserialize_settings(self, data: dict) -> None:
        self.password = data["clients"][0]["password"]
        self.fallbacks = list(Fallback._unserialize(i) for i in data.get("fallbacks", []))
    
    def _unserialize_sniffing(self, enabled: bool) -> None:
        self.sniffing = enabled
    
    def _generate_access_link(self, hostname: str, _: int = 0) -> str:
        return f"trojan://{self.password}@{hostname}:{self.port}#" + urlquote(self.remark)

class ShadowsocksProtocol(_ProtocolsBase):
    NAME = "shadowsocks"

    def __init__(
        self, 
        upload: int = 0,
        download: int = 0,
        total_traffic: int = 0,
        remark: str = "",
        enabled: bool = True,
        expiry_time: typing.Union[datetime, int, float] = 0,
        listenning_ip: str = "",
        port: int = 0,
        tls: typing.Optional[_transmissions.TLS] = None,
        transmission: typing.Optional[_transmissions._TransmissionsBase] = None,
        sniffing: bool = True,
        encryption: str = "aes-256-gcm", # 'aes-128-gcm', 'aes-256-gcm', 'chacha20-poly1305'
        password: typing.Optional[str] = None, # set None to generate random password
        network: str = "tcp,udp" # 'tcp', 'udp', 'tcp,udp'
    ) -> None:
        if isinstance(tls, _transmissions.XTLS):
            raise TypeError(
                "Cannot use XTLS with Shadowsocks."
            )
        
        super().__init__(
            upload, download, total_traffic, remark, enabled, expiry_time, listenning_ip, port,
            tls, transmission or _transmissions.TCPTransmission()
        )

        self.sniffing = sniffing
        self.encryption = encryption
        self.password = password
        self.network = network.replace("+", ",")
    
    def set_random_password(self) -> None:
        self.password = "".join(
            random.choices("1234567890abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ", k=10)
        )

    def _serialize(self) -> dict:
        if self.password is None:
            # generate random password
            self.set_random_password()
        
        return super()._serialize(
            {"method":self.encryption, "password":self.password, "network":self.network},
            self.sniffing
        )

    def _unserialize_settings(self, data: dict) -> None:
        self.encryption = data["method"]
        self.password = data["password"]
        self.network = data["network"]
    
    def _unserialize_sniffing(self, enabled: bool) -> None:
        self.sniffing = enabled

    def _generate_access_link(self, hostname: str, _: int = 0) -> str:
        if self.tls is not None and self.tls.serverName:
            hostname = self.tls.serverName
        
        b = _base64_encode(self.encryption + ":" + self.password + "@" \
                            + hostname + ":" + str(self.port))
        
        b = b.replace("+", "-").replace("=", "").replace("/", "_")

        return "ss://" + b + "#" + urlquote(self.remark)

class DokodemoDoorProtocol(_ProtocolsBase):
    NAME = "dokodemo-door"

    def __init__(
        self, 
        upload: int = 0,
        download: int = 0,
        total_traffic: int = 0,
        remark: str = "",
        enabled: bool = True,
        expiry_time: typing.Union[datetime, int, float] = 0,
        listenning_ip: str = "",
        port: int = 0,
        dest_address: typing.Optional[str] = None,
        dest_port: typing.Optional[int] = None,
        network: str = "tcp,udp" # 'tcp', 'udp', 'tcp,udp'
    ) -> None:
        super().__init__(
            upload, download, total_traffic, remark, enabled, expiry_time, listenning_ip, port,
            _transmissions.TLS(), _transmissions.TCPTransmission()
        )

        self.dest_address = dest_address
        self.dest_port = dest_port
        self.network = network.replace("+", ",")
    
    def _serialize(self) -> dict:
        settings = {"network": self.network}
        if not (self.dest_address is None):
            settings["address"] = self.dest_address
        
        if not (self.dest_port is None):
            settings["port"] = self.dest_port
        
        return super()._serialize(settings, None)

    def _unserialize_settings(self, data: dict) -> None:
        self.dest_address = data.get("address", None)
        self.dest_port = data.get("port", None)
        self.network = data["network"]

class SocksProtocol(_ProtocolsBase):
    NAME = "socks"

    def __init__(
        self, 
        upload: int = 0,
        download: int = 0,
        total_traffic: int = 0,
        remark: str = "",
        enabled: bool = True,
        expiry_time: typing.Union[datetime, int, float] = 0,
        listenning_ip: str = "",
        port: int = 0,
        username: typing.Optional[str] = None,
        password: typing.Optional[str] = None,
        use_udp: bool = False,
    ) -> None:
        super().__init__(
            upload, download, total_traffic, remark, enabled, expiry_time, listenning_ip, port,
            None, _transmissions.TCPTransmission()
        )

        self.username = username
        self.password = password
        self.use_udp = use_udp
    
    def set_random_password(self) -> None:
        self.password = "".join(
            random.choices("1234567890abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ", k=10)
        )

    def set_random_username(self) -> None:
        self.username = "".join(
            random.choices("1234567890abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ", k=10)
        )

    def _serialize(self) -> dict:
        auth = True if ((self.username is not None) and (self.password is not None)) else None

        settings = {}
        if auth:
            settings["auth"] = "password"
            settings["accounts"] = [{"user": self.username, "pass": self.password}]
        
        else:
            settings["auth"] = "noauth"
        
        settings["udp"] = self.use_udp
        settings["ip"] = "127.0.0.1"

        return super()._serialize(
            settings, None
        )
    
    def _unserialize_settings(self, data: dict) -> None:
        if data["auth"] == "password":
            self.username = data["accounts"][0]["user"]
            self.password = data["accounts"][0]["pass"]
        else:
            self.username = None
            self.password = None
        
        self.use_udp = data["udp"]
    
    def _generate_access_link(self, hostname: str, _: int = 0) -> str:
        if self.username and self.password:
            return f"socks5://{self.username}:{self.password}@{hostname}:{self.port}"
        
        return f"socks5://{hostname}:{self.port}"

class HTTPProtocol(_ProtocolsBase):
    NAME = "http"

    def __init__(
        self, 
        upload: int = 0,
        download: int = 0,
        total_traffic: int = 0,
        remark: str = "",
        enabled: bool = True,
        expiry_time: typing.Union[datetime, int, float] = 0,
        listenning_ip: str = "",
        port: int = 0,
        username: typing.Optional[str] = None, # set None to generate random
        password: typing.Optional[str] = None, # set None to generate random
    ) -> None:
        super().__init__(
            upload, download, total_traffic, remark, enabled, expiry_time, listenning_ip, port,
            None, _transmissions.TCPTransmission()
        )

        self.username = username
        self.password = password
    
    def set_random_password(self) -> None:
        self.password = "".join(
            random.choices("1234567890abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ", k=10)
        )

    def set_random_username(self) -> None:
        self.username = "".join(
            random.choices("1234567890abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ", k=10)
        )
    
    def _serialize(self) -> dict:
        if self.username is None:
            self.set_random_username()
        
        if self.password is None:
            self.set_random_password()

        return super()._serialize(
            {"accounts": [{"user": self.username, "pass": self.password}]}, None
        )

    def _unserialize_settings(self, data: dict) -> None:
        self.username = data["accounts"][0]["user"]
        self.password = data["accounts"][0]["pass"]
    
    def _generate_access_link(self, hostname: str, _: int = 0) -> str:
        if self.username and self.password:
            return f"http://{self.username}:{self.password}@{hostname}:{self.port}"
        
        return f"http://{hostname}:{self.port}"

PROTOCOLS = {
    "vmess": VMessProtocol, "vless": VLessProtocol, "trojan": TrojanProtocol,
    "shadowsocks": ShadowsocksProtocol, "dokodemo-door": DokodemoDoorProtocol,
    "socks": SocksProtocol, "http": HTTPProtocol
} # type: dict[str, _ProtocolsBase]
