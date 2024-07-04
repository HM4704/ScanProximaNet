from dataclasses import dataclass

@dataclass
class NodeInfo:
    name: str = ""
    shortId: str = ""
    ip: str = ""
    synced: bool = False
    enabledAPI: bool = False
    version: str = "0.0.1"
    sequencer: bool = False
    apiPort: int = 8000
    