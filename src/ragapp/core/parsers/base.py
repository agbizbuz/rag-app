"""Chunk dataclass, ParserProtocol, and extension registry."""

from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Protocol, runtime_checkable


@dataclass(frozen=True)
class Chunk:
    text: str
    metadata: dict  # e.g. {"source": "file.pdf", "page": 1, "paragraph": 0}


@runtime_checkable
class Parser(Protocol):
    @property
    def supported_extensions(self) -> tuple[str, ...]: ...

    @abstractmethod
    def parse(self, file) -> list[Chunk]: ...


class BaseParser(ABC):
    """Base class with shared utilities."""

    def __init__(self, chunk_size: int | None = None) -> None:
        self._chunk_size = chunk_size

    @property
    def chunk_size(self) -> int:
        if self._chunk_size is not None:
            return self._chunk_size
        from config_provider import get_config

        return get_config().chunk_size

    @abstractmethod
    def parse(self, file) -> list[Chunk]:
        """Parse file into chunks."""

    @staticmethod
    def _make_id() -> str:
        return str(uuid.uuid4())

    @staticmethod
    def _clean(text: str) -> str:
        return text.strip() if text else ""
