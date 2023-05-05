import typing

class _TransmissionsBase:
    """
    Base class for transmissions such as TCP, WS, HTTP, ...
    """

    NAME: str
    """Transmission Name"""

    SUPPORTED_SECURITY: bool = True
    """are tls and xtls supported with this protocol?"""

    def _serialize(self) -> dict:
        raise NotImplementedError

    @classmethod
    def _unserialize(cls, data: dict):
        raise NotImplementedError

class TLS:
    """
    tls settings class.
    """

    NAME = "tls"
    """Security Name"""

    def __init__(self, serverName: str = "", alpn: str = "", certFile: str = "", keyFile: str = "") -> None:
        self.serverName = serverName
        self.alpn = alpn
        self.certFile = certFile
        self.keyFile = keyFile
    
    def _serialize(self) -> dict:
        return {
            "serverName": self.serverName, "alpn": [] if not self.alpn else [self.alpn],
            "certificates": [{"certificateFile": self.certFile, "keyFile": self.keyFile}]
        }

    @classmethod
    def _unserialize(cls, data: dict):
        return cls(
            data["serverName"],
            data["alpn"][0] if len(data["alpn"]) == 1 else "",
            data["certificates"][0]["certificateFile"],
            data["certificates"][0]["keyFile"]
        )

class XTLS(TLS):
    """
    xtls settings class.
    """

    NAME = "xtls"

class HTTPRequestSettings:
    def __init__(self, method: str = "GET", path: str = "/", headers: dict = {}) -> None:
        self.method = method
        self.path = path
        self.headers = headers

class HTTPResponseSettings:
    def __init__(self, version: str = "1.1", status: int = 200, reason: str = "OK", headers: dict = {}) -> None:
        self.version = version
        self.status = status
        self.reason = reason
        self.headers = headers

class TCPTransmission(_TransmissionsBase):
    NAME = "tcp"

    def __init__(
        self,
        accept_proxy_protocol: bool = False,
        isHTTP: bool = False,
        http_request: typing.Optional["HTTPRequestSettings"] = None,
        http_response: typing.Optional["HTTPResponseSettings"] = None,
    ) -> None:
        self.accept_proxy_protocol = accept_proxy_protocol
        self.isHTTP = isHTTP
        self.http_request = http_request
        self.http_response = http_response

        if isHTTP:
            if http_response is None:
                self.http_response = HTTPResponseSettings()
            
            if http_request is None:
                self.http_request = HTTPRequestSettings()
    
    def _serialize(self) -> dict:
        data = {"acceptProxyProtocol": self.accept_proxy_protocol,
                "header": {"type": "http" if self.isHTTP else "none"}}

        if self.isHTTP:
            data["header"]["request"] = {
                "method": self.http_request.method,
                "path": [self.http_request.path], "headers": self.http_request.headers
            }
            data["header"]["response"] = {
                "version": self.http_response.version, "reason": self.http_response.reason,
                "status": str(self.http_response.status), "headers": self.http_response.headers
            }
        
        return data
    
    @classmethod
    def _unserialize(cls, data: dict):
        obj = cls(data["acceptProxyProtocol"], data["header"]["type"] == "http")
        
        if data["header"]["type"] == "http":
            obj.http_request = HTTPRequestSettings(
                data["header"]["request"]["method"], data["header"]["request"]["path"][0],
                data["header"]["request"]["headers"],
            )
            obj.http_response = HTTPResponseSettings(
                data["header"]["response"]["version"], int(data["header"]["response"]["status"]),
                data["header"]["response"]["reason"], data["header"]["response"]["headers"]
            )
        
        return obj

class WSTransmission(_TransmissionsBase):
    NAME = "ws"

    def __init__(
        self, accept_proxy_protocol: bool = False, path: str = "/", headers: dict = {},
    ) -> None:
        self.accept_proxy_protocol = accept_proxy_protocol
        self.path = path
        self.headers = headers
    
    def _serialize(self) -> dict:
        return {"acceptProxyProtocol": self.accept_proxy_protocol,
                "path": self.path, "headers": self.headers}

    @classmethod
    def _unserialize(cls, data: dict):
        return cls(data["acceptProxyProtocol"], data["path"], data["headers"])

class KCPTransmission(_TransmissionsBase):
    NAME = "kcp"

    SUPPORTED_SECURITY = False

    def __init__(
        self, password: str, camouflage: str = "none", mtu: int = 1350, tti: int = 20,
        uplink_capacity: int = 5, downlink_capacity: int = 20, congestion: bool = False,
        read_buffer_size: int = 5, write_buffer_size: int = 5
    ) -> None:
        """
        camouflages: 'srtp', 'utp', 'wechat-video', 'dtls', 'wireguard'

        *TLS and XTLS are unsupported.
        """
        self.password = password
        self.camouflage = camouflage
        self.mtu = mtu
        self.tti = tti
        self.uplink_capacity = uplink_capacity
        self.downlink_capacity = downlink_capacity
        self.congestion = congestion
        self.read_buffer_size = read_buffer_size
        self.write_buffer_size = write_buffer_size

    def _serialize(self) -> dict:
        return {
                "mtu": self.mtu, "tti": self.tti, "uplinkCapacity": self.uplink_capacity,
                "downlinkCapacity": self.downlink_capacity, "congestion": self.congestion, 
                "readBufferSize": self.read_buffer_size, "writeBufferSize": self.write_buffer_size,
                "header": {"type": self.camouflage}, "seed": self.password
            }
        
    
    @classmethod
    def _unserialize(cls, data: dict):
        return cls(
            data["seed"], data["header"]["type"], data["mtu"], data["tti"], data["uplinkCapacity"],
            data["downlinkCapacity"], data["congestion"], data["readBufferSize"], data["writeBufferSize"]
        )

class HTTPTransmission(_TransmissionsBase):
    NAME = "http"

    def __init__(
        self, path: str = "/", hosts: typing.List[str] = []
    ) -> None:
        self.path = path
        self.hosts = hosts
    
    def _serialize(self) -> dict:
        return {"path": self.path, "host": self.hosts}
    
    @classmethod
    def _unserialize(cls, data: dict):
        return cls(data["path"], data["host"])

class QuicTransmission(_TransmissionsBase):
    NAME = "quic"

    def __init__(
        self, encryption: str = "none", password: str = "", camouflage: str = "none"
    ) -> None:
        """
        encryptions: 'aes-128-gcm', 'chacha20-poly1305'

        camouflages: 'srtp', 'utp', 'wechat-video', 'dtls', 'wireguard'
        """
        self.encryption = encryption
        self.password = password
        self.camouflage = camouflage

    def _serialize(self) -> dict:
        return {"security": self.encryption, "key": self.password,
                "header": {"type": self.camouflage}}
    
    @classmethod
    def _unserialize(cls, data: dict):
        return cls(data["security"], data["key"], data["header"]["type"])

class GRPCTransmission(_TransmissionsBase):
    NAME = "grpc"

    def __init__(self, serviceName: str = "") -> None:
        self.serviceName = serviceName

    def _serialize(self) -> dict:
        return {"serviceName": self.serviceName}
    
    @classmethod
    def _unserialize(cls, data: dict):
        return cls(data["serviceName"])

TRANSMISSIONS = {
    "tcp": TCPTransmission, "ws": WSTransmission, "kcp": KCPTransmission,
    "http": HTTPTransmission, "quic": QuicTransmission, "grpc": GRPCTransmission
} # type: dict[str, _TransmissionsBase]

