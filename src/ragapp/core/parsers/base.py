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

    @staticmethod
    def _make_id() -> str:
        return str(uuid.uuid4())

    @staticmethod
    def _clean(text: str) -> str:
        return text.strip() if text else ""
