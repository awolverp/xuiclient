import dataclasses
import typing

class _StatusStat(typing.TypedDict):
    current: int
    total: int

class _StatusXRayState(typing.TypedDict):
    state: str
    errorMsg: str
    version: str

class _StatusNetIO(typing.TypedDict):
    up: int
    down: int

class _StatusNetTraffic(typing.TypedDict):
    sent: int
    recv: int

class _PublicIP(typing.TypedDict):
    ipv4: str
    ipv6: str

@dataclasses.dataclass()
class ServerStatusResponse:
    cpu: float
    mem: _StatusStat
    swap: _StatusStat
    disk: _StatusStat
    xray: _StatusXRayState
    uptime: int
    loads: typing.List[float]
    tcpCount: int
    udpCount: int
    netIO: _StatusNetIO
    netTraffic: _StatusNetTraffic

    cpuCores: int = 0
    """ Vaxilu and NidukaAkalanka not supported """

    cpuSpeedMhz: int = 0
    """ Vaxilu and NidukaAkalanka not supported """

    publicIP: _PublicIP = dataclasses.field(default_factory=lambda: _PublicIP(ipv4="", ipv6=""))
    """ Vaxilu and NidukaAkalanka not supported """

@dataclasses.dataclass()
class SettingsResponse:
    webPort: int
    xrayTemplateConfig: str
    timeLocation: str
    webListen: str = ""
    webCertFile: str = ""
    webKeyFile: str = ""
    webBasePath: str = "/"

    tgBotEnable: bool = False
    """ Vaxilu not supported """

    tgBotToken: str = ""
    """ Vaxilu not supported """

    tgBotChatId: int = 0
    """ Vaxilu not supported """

    tgRunTime: typing.Union[int, str] = 0
    """
    Vaxilu not supported.

    - Is int for NidukaAkalanka
    - Is str for Sanaei
    """

    webDomain: str = ""
    """ Vaxilu and NidukaAkalanka not supported """

    sessionMaxAge: int = 0
    """ Vaxilu and NidukaAkalanka not supported """

    expireDiff: int = 0
    """ Vaxilu and NidukaAkalanka not supported """

    trafficDiff: int = 0
    """ Vaxilu and NidukaAkalanka not supported """

    tgBotBackup: bool = False
    """ Vaxilu and NidukaAkalanka not supported """

    tgBotLoginNotify: bool = False
    """ Vaxilu and NidukaAkalanka not supported """

    tgCpu: int = 0
    """ Vaxilu and NidukaAkalanka not supported """

    tgLang: str = "en-US"
    """ Vaxilu and NidukaAkalanka not supported """

    secretEnable: bool = False
    """ Vaxilu and NidukaAkalanka not supported """

    subEnable: bool = False
    """ Vaxilu and NidukaAkalanka not supported """

    subListen: str = ""
    """ Vaxilu and NidukaAkalanka not supported """

    subPort: int = 0
    """ Vaxilu and NidukaAkalanka not supported """

    subPath: str = "/sub/"
    """ Vaxilu and NidukaAkalanka not supported """

    subDomain: str = ""
    """ Vaxilu and NidukaAkalanka not supported """

    subCertFile: str = ""
    """ Vaxilu and NidukaAkalanka not supported """

    subKeyFile: str = ""
    """ Vaxilu and NidukaAkalanka not supported """

    subUpdates: int = 12
    """ Vaxilu and NidukaAkalanka not supported """

    def __post_init__(self):
        if isinstance(self.tgBotChatId, str):
            self.tgBotChatId = int(self.tgBotChatId or '0')
        
        if isinstance(self.tgRunTime, str) and self.tgRunTime.isdigit():
            self.tgRunTime = int(self.tgRunTime or '0')
