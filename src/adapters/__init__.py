from ..config import PlatformConfig
from .arango_adapter import ArangoAdapter
from .base import GraphAdapter
from .cypher_bolt_adapter import CypherBoltAdapter
from .neptune_adapter import NeptuneOpenCypherAdapter

_ADAPTER_REGISTRY = {
    "bolt_cypher": CypherBoltAdapter,
    "neptune_opencypher": NeptuneOpenCypherAdapter,
    "arango_aql": ArangoAdapter,
}


def build_adapter(platform: PlatformConfig) -> GraphAdapter:
    cls = _ADAPTER_REGISTRY.get(platform.adapter)
    if cls is None:
        raise ValueError(f"No adapter registered for type '{platform.adapter}'")
    return cls(platform.credentials)
