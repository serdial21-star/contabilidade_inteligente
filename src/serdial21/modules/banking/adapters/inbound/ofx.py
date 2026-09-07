'''Parser seguro para OFX 1.x SGML-like e OFX 2.x XML.'''

from datetime import date
from decimal import Decimal, InvalidOperation
from hashlib import sha256
import re
from xml.etree import ElementTree
from xml.parsers import expat

from serdial21.modules.banking.application.ports.parser import OfxParseError
from serdial21.modules.banking.domain.entities import ParsedOfx, ParsedOfxStatement, ParsedOfxTransaction


DEFAULT_MAX_OFX_BYTES = 10 * 1024 * 1024
_TAG = re.compile(r'<(/?)([A-Za-z0-9_.-]+)(?:\s[^>]*)?>')
_HEADER = re.compile(r'^([A-Z0-9_-]+):(.*)$', re.MULTILINE)


class SafeOfxParser:
    parser_name = 'serdial21.ofx'
    parser_version = '1.0.0'

    def __init__(self, *, max_ofx_bytes: int = DEFAULT_MAX_OFX_BYTES) -> None:
        if max_ofx_bytes < 1:
            raise ValueError('limite OFX deve ser positivo')
        self._max_ofx_bytes = max_ofx_bytes

    def parse(self, content: bytes) -> ParsedOfx:
        if not content:
            raise OfxParseError('EMPTY_OFX', 'OFX vazio')
        if len(content) > self._max_ofx_bytes:
            raise OfxParseError('OFX_TOO_LARGE', 'OFX excede o limite permitido')
        if _looks_like_xml(content):
            return self._parse_xml(content)
        return self._parse_sgml(content)

    def _parse_xml(self, content: bytes) -> ParsedOfx:
        _reject_unsafe_xml(content)
        try:
            root = ElementTree.fromstring(content)
        except ElementTree.ParseError as error:
            raise OfxParseError('MALFORMED_OFX', 'OFX XML malformado') from error
        if _local(root.tag).upper() != 'OFX':
            raise OfxParseError('UNSUPPORTED_OFX', 'raiz OFX não reconhecida')
        version = root.attrib.get('VERSION', '2.x')
        statements = tuple(_statement_from_xml(node) for node in _find_all(root, 'STMTRS'))
        if not statements:
            raise OfxParseError('MISSING_STATEMENT', 'OFX não possui extrato bancário')
        return ParsedOfx(schema_version=f'OFX/{version}', statements=statements)

    def _parse_sgml(self, content: bytes) -> ParsedOfx:
        header_end = content.find(b'<OFX')
        if header_end < 0:
            raise OfxParseError('UNSUPPORTED_OFX', 'cabeçalho ou corpo OFX ausente')
        header = content[:header_end].decode('ascii', errors='replace').upper()
        values = dict(_HEADER.findall(header))
        if values.get('OFXHEADER', '').strip() != '100':
            raise OfxParseError('UNSUPPORTED_OFX', 'cabeçalho OFX 1.x inválido')
        encoding = _ofx_encoding(values)
        try:
            text = content[header_end:].decode(encoding)
        except UnicodeDecodeError as error:
            raise OfxParseError('INVALID_ENCODING', 'encoding OFX inválido') from error
        tree = _sgml_tree(text)
        if tree is None or tree.name != 'OFX':
            raise OfxParseError('MALFORMED_OFX', 'corpo OFX 1.x malformado')
        statements = tuple(_statement_from_sgml(node) for node in _descendants(tree, 'STMTRS'))
        if not statements:
            raise OfxParseError('MISSING_STATEMENT', 'OFX não possui extrato bancário')
        version = values.get('VERSION', '1.x').strip()
        return ParsedOfx(schema_version=f'OFX/{version}', statements=statements)


class _Node:
    def __init__(self, name: str) -> None:
        self.name = name.upper()
        self.text = ''
        self.children: list[_Node] = []


def _sgml_tree(text: str) -> _Node | None:
    root: _Node | None = None
    stack: list[_Node] = []
    position = 0
    for match in _TAG.finditer(text):
        value = text[position:match.start()].strip()
        if value and stack:
            stack[-1].text += value
        closing, name = match.group(1), match.group(2).upper()
        if closing:
            matching = next((index for index in range(len(stack) - 1, -1, -1) if stack[index].name == name), None)
            if matching is None:
                raise OfxParseError('MALFORMED_OFX', 'fechamento de tag OFX inválido')
            del stack[matching:]
        else:
            node = _Node(name)
            if stack:
                stack[-1].children.append(node)
            elif root is None:
                root = node
            else:
                raise OfxParseError('MALFORMED_OFX', 'múltiplas raízes OFX')
            stack.append(node)
        position = match.end()
    if root is None:
        return None
    return root


def _statement_from_xml(node: ElementTree.Element) -> ParsedOfxStatement:
    account = _find(node, 'BANKACCTFROM')
    if account is None:
        raise OfxParseError('MISSING_ACCOUNT', 'extrato sem BANKACCTFROM')
    balance = _find(node, 'BALAMT')
    ledger_balance = _find(node, 'LEDGERBAL')
    return _build_statement(
        _value_xml(account, 'BANKID'), _value_xml(account, 'BRANCHID'), _value_xml(account, 'ACCTID'),
        _value_xml(account, 'ACCTTYPE'), _value_xml(node, 'CURDEF'), _value_xml(node, 'DTSTART'),
        _value_xml(node, 'DTEND'), _value_xml(balance if balance is not None else node, 'BALAMT'),
        _value_xml(ledger_balance if ledger_balance is not None else node, 'BALAMT'),
        [_transaction_xml(item) for item in _find_all(node, 'STMTTRN')],
    )


def _statement_from_sgml(node: _Node) -> ParsedOfxStatement:
    account = _child(node, 'BANKACCTFROM')
    if account is None:
        raise OfxParseError('MISSING_ACCOUNT', 'extrato sem BANKACCTFROM')
    return _build_statement(
        _value_node(account, 'BANKID'), _value_node(account, 'BRANCHID'), _value_node(account, 'ACCTID'),
        _value_node(account, 'ACCTTYPE'), _value_node(node, 'CURDEF'), _value_node(node, 'DTSTART'),
        _value_node(node, 'DTEND'), _value_node(node, 'BALAMT'), _value_node(_child(node, 'LEDGERBAL'), 'BALAMT'),
        [_transaction_node(item) for item in _descendants(node, 'STMTTRN')],
    )


def _build_statement(bank: str | None, branch: str | None, account: str | None, account_type: str | None, currency: str | None, start: str | None, end: str | None, opening: str | None, closing: str | None, transactions: list[ParsedOfxTransaction]) -> ParsedOfxStatement:
    if not account:
        raise OfxParseError('MISSING_ACCOUNT', 'número da conta OFX ausente')
    return ParsedOfxStatement(bank_id=bank, branch_id=branch, account_number=account, account_type=account_type, currency_code=currency, start_date=_date(start, 'statement.start_date'), end_date=_date(end, 'statement.end_date'), opening_balance=_decimal(opening, 'opening_balance'), closing_balance=_decimal(closing, 'closing_balance'), transactions=tuple(transactions))


def _transaction_xml(node: ElementTree.Element) -> ParsedOfxTransaction:
    return _transaction(lambda name: _value_xml(node, name))


def _transaction_node(node: _Node) -> ParsedOfxTransaction:
    return _transaction(lambda name: _value_node(node, name))


def _transaction(value: object) -> ParsedOfxTransaction:
    getter = value  # keeps both source adapters identical
    amount = _decimal(getter('TRNAMT'), 'transaction.amount')
    if amount is None:
        raise OfxParseError('MISSING_AMOUNT', 'transação OFX sem TRNAMT')
    fitid = getter('FITID')
    return ParsedOfxTransaction(fitid=fitid or None, external_reference=getter('REFNUM') or None, transaction_date=_date(getter('DTUSER'), 'transaction.date'), posted_date=_date(getter('DTPOSTED'), 'transaction.posted_date'), amount=amount, direction='DEBIT' if amount < 0 else 'CREDIT' if amount > 0 else 'ZERO', description=getter('MEMO') or getter('NAME') or None, document_number=getter('CHECKNUM') or None)


def _decimal(value: str | None, path: str) -> Decimal | None:
    if value is None or not value.strip():
        return None
    try:
        parsed = Decimal(value.strip())
    except InvalidOperation as error:
        raise OfxParseError('INVALID_DECIMAL', f'{path} inválido') from error
    if not parsed.is_finite() or parsed.as_tuple().exponent < -2:
        raise OfxParseError('DECIMAL_OUT_OF_RANGE', f'{path} fora da precisão monetária')
    return parsed


def _date(value: str | None, path: str) -> date | None:
    if value is None or not value.strip():
        return None
    match = re.fullmatch(r'(\d{4})(\d{2})(\d{2})(?:\d{6}(?:\.\d+)?(?:\[[^]]+\])?)?', value.strip())
    if match is None:
        raise OfxParseError('INVALID_DATE', f'{path} inválida')
    try:
        return date(int(match.group(1)), int(match.group(2)), int(match.group(3)))
    except ValueError as error:
        raise OfxParseError('INVALID_DATE', f'{path} inválida') from error


def _reject_unsafe_xml(content: bytes) -> None:
    if content.lstrip().startswith(b'<?xml') and b'<!' not in content:
        return
    if b'<!' in content.upper():
        raise OfxParseError('UNSAFE_XML_DECLARATION', 'DTD ou entidade XML não é permitida')
    parser = expat.ParserCreate()
    parser.SetParamEntityParsing(expat.XML_PARAM_ENTITY_PARSING_NEVER)
    try:
        parser.Parse(content, True)
    except expat.ExpatError as error:
        raise OfxParseError('MALFORMED_OFX', 'OFX XML malformado') from error


def _looks_like_xml(content: bytes) -> bool:
    return content.lstrip().startswith(b'<?xml') or b'<OFX' in content[:256] and b'OFXHEADER:100' not in content[:256].upper()


def _ofx_encoding(header: dict[str, str]) -> str:
    charset = header.get('CHARSET', '').strip().upper()
    if charset in {'1252', 'WINDOWS-1252'}:
        return 'cp1252'
    if charset in {'UTF-8', 'UTF8'}:
        return 'utf-8'
    return 'ascii'


def _local(tag: str) -> str:
    return tag.rsplit('}', 1)[-1]


def _find(element: ElementTree.Element, name: str) -> ElementTree.Element | None:
    return next((item for item in element.iter() if _local(item.tag).upper() == name), None)


def _find_all(element: ElementTree.Element, name: str) -> list[ElementTree.Element]:
    return [item for item in element.iter() if _local(item.tag).upper() == name]


def _value_xml(element: ElementTree.Element | None, name: str) -> str | None:
    if element is None:
        return None
    found = _find(element, name)
    return None if found is None or found.text is None else found.text.strip()


def _child(node: _Node | None, name: str) -> _Node | None:
    if node is None:
        return None
    return next((item for item in node.children if item.name == name), None)


def _descendants(node: _Node, name: str) -> list[_Node]:
    output: list[_Node] = []
    for child in node.children:
        if child.name == name:
            output.append(child)
        output.extend(_descendants(child, name))
    return output


def _value_node(node: _Node | None, name: str) -> str | None:
    found = _child(node, name)
    return None if found is None else found.text.strip() or None
