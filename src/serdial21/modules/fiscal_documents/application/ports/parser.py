'''Contrato de parser fiscal sem dependência de XML no domínio.'''

from typing import Protocol

from serdial21.modules.fiscal_documents.domain.entities import ParsedNFe55


class FiscalXmlParseError(ValueError):
    def __init__(
        self,
        code: str,
        message: str,
        *,
        schema_version: str | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.schema_version = schema_version


class NFe55Parser(Protocol):
    parser_name: str
    parser_version: str

    def parse(self, content: bytes) -> ParsedNFe55: ...
