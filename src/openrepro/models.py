"""Versioned manifest models and portable path rules."""

import re
import unicodedata
from datetime import UTC, date, datetime
from enum import StrEnum
from pathlib import PurePosixPath
from typing import Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator

from . import __version__


class OpenReproError(ValueError):
    """Actionable input or package error."""


def safe_path(value: str) -> str:
    """Accept canonical relative POSIX paths portable to Windows and Unix."""
    if not value or "\\" in value or unicodedata.normalize("NFC", value) != value:
        raise OpenReproError("Use a nonempty NFC-normalized relative POSIX path")
    parts = value.split("/")
    reserved = {"CON", "PRN", "AUX", "NUL"} | {
        f"{prefix}{i}" for prefix in ("COM", "LPT") for i in range(1, 10)
    }
    for part in parts:
        if (
            part in ("", ".", "..")
            or part.endswith((".", " "))
            or re.search(r'[<>:"|?*\x00-\x1f\x7f]', part)
            or part.split(".")[0].upper() in reserved
        ):
            raise OpenReproError("Unsafe or nonportable file path")
    if PurePosixPath(value).is_absolute():
        raise OpenReproError("Absolute paths are forbidden")
    return value


class Role(StrEnum):
    raw = "raw"
    processed = "processed"
    protocol = "protocol"
    script = "script"
    figure = "figure"
    table = "table"
    supplementary = "supplementary"


ROLE_DIR = {
    Role.raw: "data/raw",
    Role.processed: "data/processed",
    Role.protocol: "protocol",
    Role.script: "analysis/scripts",
    Role.figure: "results/figures",
    Role.table: "results/tables",
    Role.supplementary: "supplementary",
}


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class FileEntry(StrictModel):
    path: str
    sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    size: int = Field(ge=0)
    role: Role
    description: str = ""
    derived_from: list[str] = Field(default_factory=list)

    _path = field_validator("path")(safe_path)

    @field_validator("derived_from")
    @classmethod
    def check_relations(cls, values: list[str]) -> list[str]:
        return [safe_path(v) for v in values]


class Manifest(StrictModel):
    schema_version: Literal["0.1"] = "0.1"
    software_version: str = __version__
    identifier: UUID = Field(default_factory=uuid4)
    title: str = Field(min_length=1)
    description: str = Field(min_length=1)
    authors: list[str] = Field(min_length=1)
    created: datetime = Field(default_factory=lambda: datetime.now(UTC))
    license: str = Field(default="CC-BY-4.0", min_length=1)
    domain: str | None = None
    keywords: list[str] = Field(default_factory=list)
    doi: str | None = None
    institution: str | None = None
    experimental_date: date | None = None
    reproduction: str = ""
    files: list[FileEntry] = Field(default_factory=list)

    @field_validator("schema_version")
    @classmethod
    def supported(cls, value: str) -> str:
        if value != "0.1":
            raise ValueError("Unsupported schema version; supported: 0.1")
        return value

    @field_validator("authors")
    @classmethod
    def authors_not_empty(cls, values: list[str]) -> list[str]:
        if any(not a.strip() for a in values):
            raise ValueError("Authors must be nonempty")
        return [a.strip() for a in values]

    @field_validator("created")
    @classmethod
    def aware(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            raise ValueError("Creation date must have a timezone")
        return value
