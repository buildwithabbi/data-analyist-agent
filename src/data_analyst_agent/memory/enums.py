"""Enumerations for the durable memory subsystem."""

from enum import Enum


class MemoryKind(str, Enum):
    EPISODE = "episode"
    SEMANTIC = "semantic"


class MemoryLifecycle(str, Enum):
    NEW = "new"
    ACTIVE = "active"
    ARCHIVED = "archived"
    EXPIRED = "expired"
