"""Platform adapters."""

from .cli import CLIAdapter
from .interface import PlatformAdapter
from .rest import RESTAdapter
from .roll20 import Roll20Adapter

__all__ = ["CLIAdapter", "PlatformAdapter", "RESTAdapter", "Roll20Adapter"]
