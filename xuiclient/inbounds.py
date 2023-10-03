from urllib.parse import urlencode, quote
import dataclasses
import typing
import json
import copy
import uuid
import base64

MISSING = type("MISSING", (object,), {})

_SupportedProtocols = typing.Literal[
    "vmess", "vless", "trojan", "shadowsocks", "dokodemo-door", "http", "socks"
]

# VMess Protocol
@dataclasses.dataclass()
class VMessClient:
    id: str = dataclasses.field(default_factory=lambda: str(uuid.uuid4()))
    """ VMess protocol client ID (UUID) """

    alterId: int = 0
    """ I don't know what it is """

    email: str = dataclasses.field(default=MISSING, compare=False)
    """ Vaxilu not supported """

    limitIp: int = dataclasses.field(default=MISSING, compare=False)
    """ Vaxilu not supported """

    totalGB: int = dataclasses.field(default=MISSING, compare=False)
    """ Vaxilu not supported """

    expiryTime: int = dataclasses.field(default=MISSING, compare=False)
    """ Vaxilu not supported - *in milliseconds*"""

    enable: bool = dataclasses.field(default=MISSING, compare=False)
    """ Vaxilu and NidukaAkalanka not supported """

    tgId: str = dataclasses.field(default=MISSING, compare=False)
    """ Vaxilu and NidukaAkalanka not supported """

    subId: str = dataclasses.field(default=MISSING, compare=False)
    """ Vaxilu and NidukaAkalanka not supported """

    def __post_init__(self):
        if isinstance(self.expiryTime, str):
            self.expiryTime = int(self.expiryTime or '0')

@dataclasses.dataclass()
class VMessSettings:
    clients: typing.List[VMessClient]
    """ VMess clients """

    disableInsecureEncryption: bool = False
    """ disable insecure encryption """

    def __post_init__(self):
        if self.clients and isinstance(self.clients[0], dict):
            self.clients = [VMessClient(**i) for i in self.clients] # type: ignore

# VLess Protocol
class VLessFallback(typing.TypedDict):
    name: str
    """ fallback name """

    alpn: str
    """ fallback alpn """
    
    path: str
    """ fallback url path """

    dest: str
    """ fallback destination """
    
    xver: int
    """ fallback xversion """

@dataclasses.dataclass()
class VLessClient:
    id: str = dataclasses.field(default_factory=lambda: str(uuid.uuid4()))
    """ VLess protocol client ID (UUID) """

    flow: typing.Literal["xtls-rprx-direct", "xtls-rprx-origin", ""] = ""
    """ can be `xtls-rprx-direct` or `xtls-rprx-origin`. """

    email: str = dataclasses.field(default=MISSING, compare=False)
    """ Vaxilu not supported """

    limitIp: int = dataclasses.field(default=MISSING, compare=False)
    """ Vaxilu not supported """

    totalGB: int = dataclasses.field(default=MISSING, compare=False)
    """ Vaxilu not supported """

    expiryTime: int = dataclasses.field(default=MISSING, compare=False)
    """ Vaxilu not supported - *in milliseconds*"""

    enable: bool = dataclasses.field(default=MISSING, compare=False)
    """ Vaxilu and NidukaAkalanka not supported """

    tgId: str = dataclasses.field(default=MISSING, compare=False)
    """ Vaxilu and NidukaAkalanka not supported """

    subId: str = dataclasses.field(default=MISSING, compare=False)
    """ Vaxilu and NidukaAkalanka not supported """

    def __post_init__(self):
        if isinstance(self.expiryTime, str):
            self.expiryTime = int(self.expiryTime or '0')

@dataclasses.dataclass()
class VLessSettings:
    clients: typing.List[VLessClient]
    """ VLess clients """

    decryption: str = "none"
    """ usuall is `none` """
    
    fallbacks: typing.List[VLessFallback] = dataclasses.field(default_factory=list)
    """ VLess fallbacks """

    def __post_init__(self):
        if self.clients and isinstance(self.clients[0], dict):
            self.clients = [VLessClient(**i) for i in self.clients] # type: ignore

# Trojan Protocol
class TrojanFallback(VLessFallback): pass

@dataclasses.dataclass()
class TrojanClient:
    password: str
    """ client password for connecting """

    flow: typing.Literal["xtls-rprx-direct", "xtls-rprx-origin", ""] = ""
    """ can be `xtls-rprx-direct` or `xtls-rprx-origin`. """

    email: str = dataclasses.field(default=MISSING, compare=False)
    """ Vaxilu not supported """

    limitIp: int = dataclasses.field(default=MISSING, compare=False)
    """ Vaxilu not supported """

    totalGB: int = dataclasses.field(default=MISSING, compare=False)
    """ Vaxilu not supported """

    expiryTime: int = dataclasses.field(default=MISSING, compare=False)
    """ Vaxilu not supported - *in milliseconds*"""

    enable: bool = dataclasses.field(default=MISSING, compare=False)
    """ Vaxilu and NidukaAkalanka not supported """

    tgId: str = dataclasses.field(default=MISSING, compare=False)
    """ Vaxilu and NidukaAkalanka not supported """

    subId: str = dataclasses.field(default=MISSING, compare=False)
    """ Vaxilu and NidukaAkalanka not supported """

@dataclasses.dataclass()
class TrojanSettings:
    clients: typing.List[TrojanClient]
    """ Trojan clients """

    fallbacks: typing.List[TrojanFallback] = dataclasses.field(default_factory=list)
    """ Trojan fallbacks """

    def __post_init__(self):
        if self.clients and isinstance(self.clients[0], dict):
            self.clients = [TrojanClient(**i) for i in self.clients] # type: ignore

# Shadowsocks Protocol
@dataclasses.dataclass()
class ShadowsocksClient:
    password: str
    """ It is same with default inbound password """

    email: str
    limitIp: int
    totalGB: int
    expiryTime: int
    enable: bool
    tgId: str
    subId: str

@dataclasses.dataclass()
class ShadowsocksSettings:
    password: str
    """ Password """

    method: typing.Literal["aes-128-gcm", "aes-256-gcm", "chacha20-poly1305"] = "aes-256-gcm"
    """ it can be `aes-128-gcm`, `aes-256-gcm`, and `chacha20-poly1305` """

    network: typing.Literal["tcp", "udp", "tcp,udp"] = "tcp,udp"
    """ Usable networks. can be `tcp`, `udp`, and `tcp,udp` """

    clients: typing.List[ShadowsocksClient] = dataclasses.field(default=MISSING, compare=False)
    """ Vaxilu not supported """

    def __post_init__(self):
        if self.clients and self.clients is not MISSING and isinstance(self.clients[0], dict):
            self.clients = [ShadowsocksClient(**i) for i in self.clients] # type: ignore

# Dokodemo-door Protocol
@dataclasses.dataclass()
class DokodemoDoorSettings:
    address: typing.Union[str, typing.Type[MISSING]] = MISSING
    """ Destination address - you can ignore this parameter. """

    port: typing.Union[str, typing.Type[MISSING]] = MISSING
    """ Destination port - you can ignore this parameter. """

    network: typing.Literal["tcp", "udp", "tcp,udp"] = "tcp,udp"
    """ Usable networks. can be `tcp`, `udp`, and `tcp,udp` """

    followRedirect: bool = dataclasses.field(default=MISSING, compare=False)
    """ Vaxilu and NidukaAkalanka not supported """

# Socks Protocol
_PAccount = typing.TypedDict("_PAccount", {"user": str, "pass": str})

@dataclasses.dataclass()
class SocksSettings:
    auth: typing.Literal["password", "noauth"]
    """ set `password` if there is any password, otherwise `noauth` """

    accounts: typing.List[_PAccount]
    """ Accounts """
    
    udp: bool = False
    """ UDP enabled or not. """
    
    ip: str = ""
    """ if UDP enabled, the UDP address is where? """

# HTTP Protocol
@dataclasses.dataclass()
class HTTPSettings:
    accounts: typing.List[_PAccount]
    """ Accounts """

_ProtocolSettings = typing.Union[
    VMessSettings, VLessSettings, ShadowsocksSettings,
    DokodemoDoorSettings, SocksSettings, HTTPSettings,
    TrojanSettings
]
_PROTOCOLS = {
    "vmess": VMessSettings, "vless": VLessSettings, "shadowsocks": ShadowsocksSettings,
    "dokodemo-door": DokodemoDoorSettings, "socks": SocksSettings,
    "http": HTTPSettings, "trojan": TrojanSettings
}

@dataclasses.dataclass()
class SniffingSettings:
    enabled: bool = True
    """ sniffing is enabled or not """

    destOverride: typing.List[str] = dataclasses.field(default_factory=lambda: ["http", "tls"])
    """ always is `['http', 'tls']` """


class TlsCertificate(typing.TypedDict):
    certificateFile: str
    keyFile: str

@dataclasses.dataclass()
class TlsStreamSettingsInfo:
    allowInsecure: bool = False
    fingerprint: str = ""
    serverName: str = ""
    domains: typing.List[str] = dataclasses.field(default_factory=list)

@dataclasses.dataclass()
class TlsStreamSettings:
    serverName: str
    """ tls server name """

    certificates: typing.List[TlsCertificate]
    """ certificate files """

    alpn: typing.List[str] = dataclasses.field(default=MISSING, compare=False)
    """ Vaxula not supported """

    minVersion: str = dataclasses.field(default=MISSING, compare=False)
    """ Vaxilu and NidukaAkalanka not supported """

    maxVersion: str = dataclasses.field(default=MISSING, compare=False)
    """ Vaxilu and NidukaAkalanka not supported """

    cipherSuites: str = dataclasses.field(default=MISSING, compare=False)
    """ Vaxilu and NidukaAkalanka not supported """

    rejectUnknownSni: bool = dataclasses.field(default=MISSING, compare=False)
    """ Vaxilu and NidukaAkalanka not supported """

    settings: TlsStreamSettingsInfo = dataclasses.field(default=MISSING, compare=False)
    """ Vaxilu and NidukaAkalanka not supported """

    def __post_init__(self):
        # settings
        if isinstance(self.settings, dict):
            self.settings = TlsStreamSettingsInfo(**self.settings)

class TcpHTTPRequest(typing.TypedDict):
    method: str
    path: typing.List[str]
    headers: typing.Dict[str, typing.List[str]]

class TcpHTTPResponse(typing.TypedDict):
    version: str
    status: str
    reason: str
    headers: typing.Dict[str, typing.List[str]]

@dataclasses.dataclass()
class TcpHeader:
    type: typing.Literal["none", "http"] = "none"
    """ set `http` if you want, else `none` """
    
    request: typing.Optional[TcpHTTPRequest] = dataclasses.field(default=MISSING, repr=False)
    """ if you set type to `http`, you can specify the request info """

    response: typing.Optional[TcpHTTPResponse] = dataclasses.field(default=MISSING, repr=False)
    """ if you set type to `http`, you can specify the response info """

    def __post_init__(self):
        if self.type == "http":
            if self.request is MISSING:
                self.request = TcpHTTPRequest(method="GET", path=["/"], headers={})
            
            if self.response is MISSING:
                self.response = TcpHTTPResponse(version="1.1", status="200", reason="OK", headers={})

@dataclasses.dataclass()
class TcpStreamSettings:
    header: TcpHeader = dataclasses.field(default_factory=TcpHeader)
    """ tcp header """

    acceptProxyProtocol: bool = dataclasses.field(default=MISSING, compare=False)
    """ Vaxilu not supported """

    def __post_init__(self):
        if isinstance(self.header, dict):
            self.header = TcpHeader(**self.header)

@dataclasses.dataclass()
class WsStreamSettings:
    path: str = "/"
    headers: typing.Dict[str, str] = dataclasses.field(default_factory=dict)
    
    acceptProxyProtocol: bool = dataclasses.field(default=MISSING, compare=False)
    """ Vaxilu not supported """

class KcpHeader(typing.TypedDict):
    type: typing.Literal["none", "srtp", "utp", "wechat-video", "dtls", "wireguard"]
    """ can be `none`, `srtp`, `utp`, `wechat-video`, `dtls`, and `wireguard` """

@dataclasses.dataclass()
class KcpStreamSettings:
    header: KcpHeader
    seed: str
    mtu: int = 1350
    tti: int = 20
    uplinkCapacity: int = 5
    downlinkCapacity: int = 20
    congestion: bool = False
    readBufferSize: int = 2
    writeBufferSize: int = 2

class SockoptHeader(typing.TypedDict):
    acceptProxyProtocol: bool

@dataclasses.dataclass()
class HTTPStreamSettings:
    path: str = "/"
    host: typing.List[str] = dataclasses.field(default_factory=list)
    sockopt: SockoptHeader = dataclasses.field(default=MISSING, compare=False)
    """ Vaxilu and NidukaAkalanka not supported """

class QuicHeader(typing.TypedDict):
    type: typing.Literal["none", "srtp", "utp", "wechat-video", "dtls", "wireguard"]
    """ can be `none`, `srtp`, `utp`, `wechat-video`, `dtls`, and `wireguard` """

@dataclasses.dataclass()
class QuicStreamSettings:
    header: QuicHeader
    security: typing.Literal["none", "aes-128-gcm", "chacha20-poly1305"] = "none"
    key: str = ""

@dataclasses.dataclass()
class GrpcStreamSettings:
    serviceName: str

    multiMode: bool = dataclasses.field(default=MISSING, compare=False)
    """ Vaxilu and NidukaAkalanka not supported """
    
    sockopt: SockoptHeader = dataclasses.field(default=MISSING, compare=False)
    """ Vaxilu and NidukaAkalanka not supported """

@dataclasses.dataclass()
class StreamSettings:
    network: typing.Literal["tcp", "kcp", "ws", "http", "quic", "grpc"]
    """ stream network - `tcp`, `kcp`, `ws`, `http`, `quic`, `grpc` """

    security: typing.Literal["none", "tls", "xtls"] = "none"
    """ stream network security - `none`, `tls`, and `xtls` (for some protocols) """

    tlsSettings: typing.Optional[TlsStreamSettings] = dataclasses.field(default=MISSING, repr=False)
    """ tls settings is needed if used """

    xtlsSettings: typing.Optional[TlsStreamSettings] = dataclasses.field(default=MISSING, repr=False)
    """ xtls settings is needed if used """

    tcpSettings: typing.Optional[TcpStreamSettings] = dataclasses.field(default=MISSING, repr=False)
    """ tcp settings is needed if used """

    wsSettings: typing.Optional[WsStreamSettings] = dataclasses.field(default=MISSING, repr=False)
    """ ws settings is needed if used """

    kcpSettings: typing.Optional[KcpStreamSettings] = dataclasses.field(default=MISSING, repr=False)
    """ kcp settings is needed if used """

    httpSettings: typing.Optional[HTTPStreamSettings] = dataclasses.field(default=MISSING, repr=False)
    """ http settings is needed if used """

    quicSettings: typing.Optional[QuicStreamSettings] = dataclasses.field(default=MISSING, repr=False)
    """ quic settings is needed if used """

    grpcSettings: typing.Optional[GrpcStreamSettings] = dataclasses.field(default=MISSING, repr=False)
    """ grpc settings is needed if used """

    def __post_init__(self):
        if self.network == "tcp":
            if isinstance(self.tcpSettings, dict):
                self.tcpSettings = TcpStreamSettings(**self.tcpSettings)
        
        elif self.network == "kcp":
            if isinstance(self.kcpSettings, dict):
                self.kcpSettings = KcpStreamSettings(**self.kcpSettings)
        
        elif self.network == "ws":
            if isinstance(self.wsSettings, dict):
                self.wsSettings = WsStreamSettings(**self.wsSettings)
        
        elif self.network == "http":
            if isinstance(self.httpSettings, dict):
                self.httpSettings = HTTPStreamSettings(**self.httpSettings)
        
        elif self.network == "quic":
            if isinstance(self.quicSettings, dict):
                self.quicSettings = QuicStreamSettings(**self.quicSettings)

        elif self.network == "grpc":
            if isinstance(self.grpcSettings, dict):
                self.grpcSettings = GrpcStreamSettings(**self.grpcSettings)
        
        if self.security == "tls":
            if isinstance(self.tlsSettings, dict):
                self.tlsSettings = TlsStreamSettings(**self.tlsSettings)
        
        if self.security == "xtls":
            if isinstance(self.xtlsSettings, dict):
                self.xtlsSettings = TlsStreamSettings(**self.xtlsSettings)

@dataclasses.dataclass()
class ClientStat:
    id: int
    inboundId: int
    enable: bool
    email: str
    up: int
    down: int
    expiryTime: int
    total: int

@dataclasses.dataclass()
class Inbound:
    remark: str
    """ inbound remark """

    port: int
    """ inbound port """

    protocol: _SupportedProtocols
    """ inbound protocol """

    settings: _ProtocolSettings
    """ inbound settings """

    streamSettings: typing.Union[StreamSettings, str]
    """
    inbound stream settings
    
    - can be empty string (ONLY for some protocols and ONLY for MHSanaei)
    """

    sniffing: typing.Union[SniffingSettings, str]
    """
    inbound sniffing settings
    
    - can be empty string (ONLY for some protocols and ONLY for MHSanaei)
    """

    clientStats: typing.List[ClientStat] = dataclasses.field(default=MISSING, compare=False)
    """ Vaxilu not supported """

    id: int = dataclasses.field(default=MISSING, compare=False)
    """ inbound ID - you don't need to set it """

    up: int = 0
    """ upload (in Bytes) """

    down: int = 0
    """ download (in Bytes) """

    total: int = 0
    """ total traffic in bytes, zero means infinite """

    enable: bool = True
    """ inbound enabled or not """

    expiryTime: int = 0
    """ expiry time *in milliseconds* """

    listen: str = ""
    """ listening IP """

    tag: str = dataclasses.field(default=MISSING, repr=False)
    """ inbound tag, always like 'inbound-PORT' - you don't need to set it """

    def __post_init__(self):
        # settings
        if isinstance(self.settings, str):
            self.settings = json.loads(self.settings)
        
        if isinstance(self.settings, dict):
            self.settings = _PROTOCOLS[self.protocol](**self.settings)
        
        # stream settings
        if isinstance(self.streamSettings, str):
            if self.streamSettings:
                self.streamSettings = json.loads(self.streamSettings)
        
        if isinstance(self.streamSettings, dict):
            self.streamSettings = StreamSettings(**self.streamSettings)
        
        # sniffing
        if isinstance(self.sniffing, str):
            if self.sniffing:
                self.sniffing = json.loads(self.sniffing)
        
        if isinstance(self.sniffing, dict):
            self.sniffing = SniffingSettings(**self.sniffing)

        # client stats
        if self.clientStats and self.clientStats is not MISSING and isinstance(self.clientStats[0], dict):
            self.clientStats = list(ClientStat(**i) for i in self.clientStats) # type: ignore

    def _vmess_access_link(self, address: str, remark: str = "", client_index: int = 0) -> str:
        if self.protocol != "vmess":
            raise ValueError(
                f"cannot create vmess access link: invalid protocol error {self.protocol!r}"
            )
        
        remark = (remark) or (self.settings.clients[client_index].email or self.remark)

        obj = dict(
            v="2", ps=remark, add=address, port=self.port,
            id=self.settings.clients[client_index].id, # type: ignore
            net=self.streamSettings.network, # type: ignore
            type="none", tls=self.streamSettings.security # type: ignore
        )

        # stream settings
        network = self.streamSettings.network # type: ignore
        if network == "tcp":
            obj["type"] = self.streamSettings.tcpSettings.header.type

            if (self.streamSettings.tcpSettings.header.type == "http"):
                obj["path"] = ",".join(self.streamSettings.tcpSettings.header.request["path"])
                host = self.streamSettings.tcpSettings.header.request["headers"].get("host", None)
                if host:
                    obj["host"] = ",".join(host)
        
        elif network == "kcp":
            obj["type"] = self.streamSettings.kcpSettings.header["type"]
            obj["seed"] = self.streamSettings.kcpSettings.seed
        
        elif network == "ws":
            obj["path"] = self.streamSettings.wsSettings.path
            host = self.streamSettings.wsSettings.headers.get("host", None)
            if host:
                obj["host"] = host
        
        elif network == "http":
            obj["net"] = "h2"
            obj["path"] = self.streamSettings.httpSettings.path
            obj["host"] = ",".join(self.streamSettings.httpSettings.host)
        
        elif network == "quic":
            obj["type"] = self.streamSettings.quicSettings.header["type"]
            obj["host"] = self.streamSettings.quicSettings.security
            obj["path"] = self.streamSettings.quicSettings.key
        
        elif network == "grpc":
            obj["path"] = self.streamSettings.grpcSettings.serviceName
            if self.streamSettings.grpcSettings.multiMode is True:
                obj["type"] = "multi"
        
        # tls settings
        if self.streamSettings.security == "tls":
            if self.streamSettings.tlsSettings.serverName:
                obj["add"] = self.streamSettings.tlsSettings.serverName
            
            if isinstance(self.streamSettings.tlsSettings.settings, TlsStreamSettingsInfo):
                if self.streamSettings.tlsSettings.settings.serverName:
                    obj["sni"] = self.streamSettings.tlsSettings.settings.serverName
                
                if self.streamSettings.tlsSettings.settings.fingerprint:
                    obj["fp"] = self.streamSettings.tlsSettings.settings.fingerprint
            
                if self.streamSettings.tlsSettings.settings.allowInsecure:
                    obj["allowInsecure"] = self.streamSettings.tlsSettings.settings.allowInsecure

            if isinstance(self.streamSettings.tlsSettings.alpn, list) and self.streamSettings.tlsSettings.alpn:
                obj["alpn"] = ",".join(self.streamSettings.tlsSettings.alpn)
        
        return (b"vmess://" + base64.b64encode(json.dumps(obj, indent=4).encode())).decode()

    def _vless_access_link(self, address: str, remark: str = "", client_index: int = 0) -> str:
        if self.protocol != "vless":
            raise ValueError(
                f"cannot create vless access link: invalid protocol error {self.protocol!r}"
            )
        
        remark = (remark) or (self.settings.clients[client_index].email or self.remark)
        
        params = {"type": self.streamSettings.network}
        
        # stream
        if self.streamSettings.network == "tcp":
            if self.streamSettings.tcpSettings.header.type == "http":
                params["path"] = ",".join(self.streamSettings.tcpSettings.header.request["path"])
                host = self.streamSettings.tcpSettings.header.request["headers"].get("host", None)
                if host:
                    params["host"] = ",".join(host)

                params["headerType"] = "http"
        
        elif self.streamSettings.network == "kcp":
            params["headerType"] = self.streamSettings.kcpSettings.header["type"]
            params["seed"] = self.streamSettings.kcpSettings.seed
        
        elif self.streamSettings.network == "ws":
            params["path"] = self.streamSettings.wsSettings.path
            host = self.streamSettings.wsSettings.headers.get("host", None)
            if host:
                params["host"] = host
        
        elif self.streamSettings.network == "http":
            params["path"] = self.streamSettings.httpSettings.path
            params["host"] = ",".join(self.streamSettings.httpSettings.host)
        
        elif self.streamSettings.network == "quic":
            params["headerType"] = self.streamSettings.quicSettings.header["type"]
            params["quicSecurity"] = self.streamSettings.quicSettings.security
            params["key"] = self.streamSettings.quicSettings.key
        
        elif self.streamSettings.network == "grpc":
            params["serviceName"] = self.streamSettings.grpcSettings.serviceName
            if self.streamSettings.grpcSettings.multiMode is True:
                params["mode"] = "multi"
        
        # tls
        if self.streamSettings.security == "tls":
            params["security"] = "tls"

            if isinstance(self.streamSettings.tlsSettings.settings, TlsStreamSettingsInfo):
                params["fp"] = self.streamSettings.tlsSettings.settings.fingerprint

                if self.streamSettings.tlsSettings.settings.allowInsecure:
                    params["allowInsecure"] = "1"
                
                if self.streamSettings.tlsSettings.settings.serverName:
                    params["sni"] = self.streamSettings.tlsSettings.settings.serverName
            
            if self.streamSettings.tlsSettings.alpn is not MISSING:
                params["alpn"] = ",".join(self.streamSettings.tlsSettings.alpn)
            
            if self.streamSettings.tlsSettings.serverName:
                address = self.streamSettings.tlsSettings.serverName
            
            # client flow
            if (self.streamSettings.network == "tcp") and (self.settings.clients[client_index].flow):
                params["flow"] = self.settings.clients[client_index].flow
        
        elif self.streamSettings.security == "xtls":
            params["security"] = "xtls"

            if isinstance(self.streamSettings.xtlsSettings.settings, TlsStreamSettingsInfo):
                if self.streamSettings.xtlsSettings.settings.allowInsecure:
                    params["allowInsecure"] = "1"
                
                if self.streamSettings.xtlsSettings.settings.serverName:
                    params["sni"] = self.streamSettings.xtlsSettings.settings.serverName
            
            if self.streamSettings.xtlsSettings.alpn is not MISSING:
                params["alpn"] = ",".join(self.streamSettings.xtlsSettings.alpn)
            
            if self.streamSettings.xtlsSettings.serverName:
                address = self.streamSettings.xtlsSettings.serverName
            
            # client flow
            if (self.streamSettings.network == "tcp") and (self.settings.clients[client_index].flow):
                params["flow"] = self.settings.clients[client_index].flow

        else:
            params["security"] = "none"
        
        return "vless://" + self.settings.clients[client_index].id + "@" + address + ":" + str(self.port) \
                + "?" + urlencode(params) + "#" + quote(remark)
    
    def _trojan_access_link(self, address: str, remark: str = "", client_index: int = 0) -> str:
        if self.protocol != "trojan":
            raise ValueError(
                f"cannot create trojan access link: invalid protocol error {self.protocol!r}"
            )
        
        remark = (remark) or (self.settings.clients[client_index].email or self.remark)
        
        params = {"type": self.streamSettings.network}

        # stream
        if self.streamSettings.network == "tcp":
            if self.streamSettings.tcpSettings.header.type == "http":
                params["path"] = ",".join(self.streamSettings.tcpSettings.header.request["path"])
                host = self.streamSettings.tcpSettings.header.request["headers"].get("host", None)
                if host:
                    params["host"] = ",".join(host)

                params["headerType"] = "http"
        
        elif self.streamSettings.network == "kcp":
            params["headerType"] = self.streamSettings.kcpSettings.header["type"]
            params["seed"] = self.streamSettings.kcpSettings.seed
        
        elif self.streamSettings.network == "ws":
            params["path"] = self.streamSettings.wsSettings.path
            host = self.streamSettings.wsSettings.headers.get("host", None)
            if host:
                params["host"] = host
        
        elif self.streamSettings.network == "http":
            params["path"] = self.streamSettings.httpSettings.path
            params["host"] = ",".join(self.streamSettings.httpSettings.host)
        
        elif self.streamSettings.network == "quic":
            params["headerType"] = self.streamSettings.quicSettings.header["type"]
            params["quicSecurity"] = self.streamSettings.quicSettings.security
            params["key"] = self.streamSettings.quicSettings.key
        
        elif self.streamSettings.network == "grpc":
            params["serviceName"] = self.streamSettings.grpcSettings.serviceName
            if self.streamSettings.grpcSettings.multiMode is True:
                params["mode"] = "multi"
        
        # tls
        if self.streamSettings.security == "tls":
            params["security"] = "tls"

            if isinstance(self.streamSettings.tlsSettings.settings, TlsStreamSettingsInfo):
                params["fp"] = self.streamSettings.tlsSettings.settings.fingerprint

                if self.streamSettings.tlsSettings.settings.allowInsecure:
                    params["allowInsecure"] = "1"
                
                if self.streamSettings.tlsSettings.settings.serverName:
                    params["sni"] = self.streamSettings.tlsSettings.settings.serverName
            
            if self.streamSettings.tlsSettings.alpn is not MISSING:
                params["alpn"] = ",".join(self.streamSettings.tlsSettings.alpn)
            
            if self.streamSettings.tlsSettings.serverName:
                address = self.streamSettings.tlsSettings.serverName
        
        elif self.streamSettings.security == "xtls":
            params["security"] = "xtls"

            if isinstance(self.streamSettings.xtlsSettings.settings, TlsStreamSettingsInfo):
                if self.streamSettings.xtlsSettings.settings.allowInsecure:
                    params["allowInsecure"] = "1"
                
                if self.streamSettings.xtlsSettings.settings.serverName:
                    params["sni"] = self.streamSettings.xtlsSettings.settings.serverName
            
            if self.streamSettings.xtlsSettings.alpn is not MISSING:
                params["alpn"] = ",".join(self.streamSettings.xtlsSettings.alpn)
            
            if self.streamSettings.xtlsSettings.serverName:
                address = self.streamSettings.xtlsSettings.serverName
            
            # client flow
            if (self.streamSettings.network == "tcp") and (self.settings.clients[client_index].flow):
                params["flow"] = self.settings.clients[client_index].flow

        else:
            params["security"] = "none"

        return "trojan://" + self.settings.clients[client_index].password + "@" + address + ":" + str(self.port) \
                + "?" + urlencode(params) + "#" + quote(remark)

    def generate_access_link(self, address: str, remark: str = "", client_index: int = 0) -> str:
        if self.protocol == "vmess":
            return self._vmess_access_link(address, remark, client_index)

        if self.protocol == "vless":
            return self._vless_access_link(address, remark, client_index)

        if self.protocol == "trojan":
            return self._trojan_access_link(address, remark, client_index)

        return ""

def _asdict_inner(obj, dict_factory, fill_fields: bool = False) -> dict:
    if hasattr(type(obj), '__dataclass_fields__'):
        result = []
        for f in dataclasses.fields(obj):
            value = _asdict_inner(getattr(obj, f.name), dict_factory, fill_fields)
            if value is not MISSING:
                result.append((f.name, value))
            elif fill_fields:
                result.append((f.name, f.type()))

        return dict_factory(result)
    
    elif isinstance(obj, tuple) and hasattr(obj, '_fields'):
        return type(obj)(*[_asdict_inner(v, dict_factory, fill_fields) for v in obj]) # type: ignore
    
    elif isinstance(obj, (list, tuple)):
        return type(obj)(_asdict_inner(v, dict_factory, fill_fields) for v in obj) # type: ignore
    
    elif isinstance(obj, dict):
        return type(obj)((_asdict_inner(k, dict_factory, fill_fields),
                          _asdict_inner(v, dict_factory, fill_fields))
                         for k, v in obj.items())
    else:
        return copy.deepcopy(obj)

def _cast_to_dict(obj, fill_fields: bool = False) -> dict:
    data = _asdict_inner(obj, dict, fill_fields)
    data["settings"] = json.dumps(data["settings"])
    data["streamSettings"] = json.dumps(data["streamSettings"])
    data["sniffing"] = json.dumps(data["sniffing"])
    return data
