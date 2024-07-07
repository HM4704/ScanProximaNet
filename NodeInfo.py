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
    latestBranchSlot:   int = 0
    ledgerCoverage: int = 0
    sequencerId:    str = "N/A"
    numPeers:       int = 0