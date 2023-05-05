import typing

class StatusInfo:
    def __init__(self, current: int, total: int) -> None:
        self.current = current
        self.total = total
    
    @property
    def percentage(self) -> float:
        if self.total == 0:
            return 0.0
        
        return (self.current/self.total)*100.0

    def __repr__(self) -> str:
        return f"StatusInfo(current={self.current}, total={self.total})"

class XRayStatus:
    def __init__(self, state: int, errorMsg: str, version: str) -> None:
        self.state = state
        self.errorMsg = errorMsg
        self.version = version
    
    def __repr__(self) -> str:
        return f"XRayStatus(state={self.state}, version={self.version}, errorMsg={self.errorMsg})"

class NetIO:
    def __init__(self, up: int, down: int) -> None:
        self.up = up
        self.down = down
    
    def __repr__(self) -> str:
        return f"NetIO(up={self.up}, down={self.down})"

class NetTraffic:
    def __init__(self, sent: int, recv: int) -> None:
        self.sent = sent
        self.recv = recv
    
    def __repr__(self) -> str:
        return f"NetTraffic(sent={self.sent}, recv={self.recv})"

_StatusInfo = typing.Union[dict, StatusInfo]

class Status:
    def __init__(
        self, cpu: float, mem: _StatusInfo, swap: _StatusInfo, disk: _StatusInfo,
        xray: typing.Union[dict, XRayStatus], uptime: int, loads: typing.List[float],
        tcpCount: int, udpCount: int, netIO: typing.Union[dict, NetIO],
        netTraffic: typing.Union[dict, NetTraffic]
    ) -> None:
        self.cpu = cpu
        self.mem = StatusInfo(**mem) if isinstance(mem, dict) else mem
        self.swap = StatusInfo(**swap) if isinstance(swap, dict) else swap
        self.disk = StatusInfo(**disk) if isinstance(disk, dict) else disk
        self.xray = XRayStatus(**xray) if isinstance(xray, dict) else xray
        self.uptime = uptime
        self.loads = loads
        self.tcpCount = tcpCount
        self.udpCount = udpCount
        self.netIO = NetIO(**netIO) if isinstance(netIO, dict) else netIO
        self.netTraffic = NetTraffic(**netTraffic) if isinstance(netTraffic, dict) else netTraffic
    
    def __repr__(self) -> str:
        return f"Status(cpu={self.cpu}, mem={self.mem}, swap={self.swap}, " \
               f"disk={self.disk}, xray={self.xray}, uptime={self.uptime}, " \
               f"loads={self.loads}, tcpCount={self.tcpCount}, udpCount={self.udpCount}, " \
               f"netIO={self.netIO}, netTraffic={self.netTraffic})"

class Settings:
    def __init__(
        self, webListen: str, webPort: int, webCertFile: str, webKeyFile: str,
        webBasePath: str, tgBotEnable: bool, tgBotToken: str, tgBotChatId: str, tgRunTime: str,
        xrayTemplateConfig: str, timeLocation: str
    ) -> None:
        self.webListen = webListen
        self.webPort = webPort
        self.webCertFile = webCertFile
        self.webKeyFile = webKeyFile
        self.webBasePath = webBasePath
        self.tgBotEnable = tgBotEnable
        self.tgBotToken = tgBotToken
        self.tgBotChatId = tgBotChatId
        self.tgRunTime = tgRunTime
        self.xrayTemplateConfig = xrayTemplateConfig
        self.timeLocation = timeLocation

BYTE     = 1
KILOBYTE = 1024
MEGABYTE = 1024 * 1024
GIGABYTE = 1024 * 1024 * 1024
