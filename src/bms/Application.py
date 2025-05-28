from dataclasses import dataclass, field

@dataclass
class Application:
    appname: str
    apptype: str
    iid: str
    name: str = field(default="", repr=False)
    appstatus: str = field(default="", repr=False)
    category: str = field(default="", repr=False)
    categorydef: str = field(default="", repr=False)
    categoryname: str = field(default="", repr=False)
    commissionable: int = field(default=0, repr=False)
    device: bool = field(default=False, repr=False)
    devicetype: str = field(default="", repr=False)
    properties: list[str] = field(default_factory=list, repr=False)
    DevAddr: str = field(default="", repr=False)
    Route: str = field(default="", repr=False)
