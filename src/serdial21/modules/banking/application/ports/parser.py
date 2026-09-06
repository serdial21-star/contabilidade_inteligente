from typing import Protocol

from serdial21.modules.banking.domain.entities import ParsedOfx


class OfxParseError(ValueError):
    def __init__(self, code: str, message: str, *, schema_version: str | None = None) -> None:
        super().__init__(message)
        self.code = code
        self.schema_version = schema_version


class OfxParser(Protocol):
    parser_name: str
    parser_version: str

    def parse(self, content: bytes) -> ParsedOfx: ...
