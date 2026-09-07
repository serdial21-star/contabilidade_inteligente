'''Parser estrutural seguro e mínimo para NF-e modelo 55.'''

from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
import re
from xml.etree import ElementTree
from xml.parsers import expat

from serdial21.modules.fiscal_documents.application.ports.parser import (
    FiscalXmlParseError,
)
from serdial21.modules.fiscal_documents.domain.entities import (
    ParsedFiscalItem,
    ParsedNFe55,
    ParsedTaxDetail,
    ParsedValidationIssue,
)


NFE_NAMESPACE = 'http://www.portalfiscal.inf.br/nfe'
DEFAULT_MAX_XML_BYTES = 5 * 1024 * 1024
DEFAULT_MAX_XML_ELEMENTS = 100_000
ACCESS_KEY_PATTERN = re.compile(r'^\d{44}$')
XML_DECIMAL_PATTERN = re.compile(r'^[+-]?\d+(?:\.\d+)?$')
NFE_TAG_PREFIX = f'{{{NFE_NAMESPACE}}}'
MAX_BIGINT = 2**63 - 1


class SafeNFe55XmlParser:
    parser_name = 'serdial21.nfe55.xml'
    parser_version = '1.2.0'

    def __init__(
        self,
        *,
        max_xml_bytes: int = DEFAULT_MAX_XML_BYTES,
        max_xml_elements: int = DEFAULT_MAX_XML_ELEMENTS,
    ) -> None:
        if max_xml_bytes < 1:
            raise ValueError('limite XML deve ser positivo')
        if max_xml_elements < 1:
            raise ValueError('limite de elementos XML deve ser positivo')
        self._max_xml_bytes = max_xml_bytes
        self._max_xml_elements = max_xml_elements

    def parse(self, content: bytes) -> ParsedNFe55:
        self._preflight(content)
        try:
            root = ElementTree.fromstring(content)
        except ElementTree.ParseError as error:
            raise FiscalXmlParseError(
                'MALFORMED_XML',
                'XML malformado',
            ) from error

        namespace = {'nfe': NFE_NAMESPACE}
        if root.tag == f'{NFE_TAG_PREFIX}NFe':
            nfe = root
            protocol = None
        elif root.tag == f'{NFE_TAG_PREFIX}nfeProc':
            nfe_nodes = root.findall('nfe:NFe', namespace)
            protocol_nodes = root.findall('nfe:protNFe', namespace)
            if len(nfe_nodes) != 1 or len(protocol_nodes) != 1:
                raise FiscalXmlParseError(
                    'UNSUPPORTED_XML_SCHEMA',
                    'nfeProc deve conter exatamente uma NFe e um protNFe',
                )
            nfe = nfe_nodes[0]
            protocol = protocol_nodes[0]
        else:
            raise FiscalXmlParseError(
                'UNSUPPORTED_XML_SCHEMA',
                'raiz ou namespace de NF-e não reconhecido',
            )

        inf_nfe_nodes = nfe.findall('nfe:infNFe', namespace)
        if len(inf_nfe_nodes) != 1:
            raise FiscalXmlParseError(
                'UNSUPPORTED_XML_SCHEMA',
                'NFe deve conter exatamente um infNFe direto',
            )
        inf_nfe = inf_nfe_nodes[0]
        schema_version = (inf_nfe.get('versao') or '').strip()
        if not schema_version:
            raise FiscalXmlParseError(
                'MISSING_SCHEMA_VERSION',
                'versão do schema NF-e ausente',
            )
        if len(schema_version) > 20:
            raise FiscalXmlParseError(
                'INVALID_SCHEMA_VERSION',
                'versão do schema NF-e excede o limite suportado',
            )
        for envelope in (root, protocol):
            if envelope is None:
                continue
            envelope_version = (envelope.get('versao') or '').strip()
            if envelope_version and envelope_version != schema_version:
                raise FiscalXmlParseError(
                    'SCHEMA_VERSION_MISMATCH',
                    'versões declaradas no XML de NF-e divergem',
                    schema_version=schema_version,
                )
        access_key = (inf_nfe.get('Id') or '').strip()
        if access_key.startswith('NFe'):
            access_key = access_key[3:]
        if (
            not ACCESS_KEY_PATTERN.fullmatch(access_key)
            or not _has_valid_access_key_digit(access_key)
        ):
            raise FiscalXmlParseError(
                'INVALID_ACCESS_KEY',
                'chave NF-e ausente ou inválida',
                schema_version=schema_version,
            )

        issues: list[ParsedValidationIssue] = []
        model = _text(inf_nfe, 'nfe:ide/nfe:mod', namespace)
        if model is None:
            raise FiscalXmlParseError(
                'MISSING_DOCUMENT_MODEL',
                'modelo fiscal ausente',
                schema_version=schema_version,
            )
        if model != '55':
            raise FiscalXmlParseError(
                'UNSUPPORTED_DOCUMENT_MODEL',
                'somente NF-e modelo 55 é aceita',
                schema_version=schema_version,
            )
        if access_key[20:22] != model:
            raise FiscalXmlParseError(
                'ACCESS_KEY_MODEL_MISMATCH',
                'modelo do XML diverge do modelo codificado na chave NF-e',
                schema_version=schema_version,
            )

        issuer = _single_element(inf_nfe, 'nfe:emit', namespace)
        recipient = _single_element(inf_nfe, 'nfe:dest', namespace)
        issuer_tax_id = _bounded(
            _party_identifier(issuer, namespace),
            32,
            'issuer.tax_id',
            issues,
        )
        issuer_name = _bounded(
            _text(issuer, 'nfe:xNome', namespace),
            255,
            'issuer.name',
            issues,
        )
        recipient_tax_id = _bounded(
            _party_identifier(recipient, namespace),
            32,
            'recipient.tax_id',
            issues,
        )
        recipient_name = _bounded(
            _text(recipient, 'nfe:xNome', namespace),
            255,
            'recipient.name',
            issues,
        )
        _missing(issues, issuer_tax_id, 'issuer.tax_id')
        _missing(issues, issuer_name, 'issuer.name')
        _missing(issues, recipient_tax_id, 'recipient.tax_id')
        _missing(issues, recipient_name, 'recipient.name')

        issued_at = _datetime_value(
            _text(inf_nfe, 'nfe:ide/nfe:dhEmi', namespace),
            'issued_at',
            issues,
        )
        movement_at = _datetime_value(
            _text(inf_nfe, 'nfe:ide/nfe:dhSaiEnt', namespace),
            'movement_at',
            issues,
            required=False,
        )
        total = _single_element(
            inf_nfe,
            'nfe:total/nfe:ICMSTot',
            namespace,
        )
        items = tuple(
            _parse_item(node, namespace, issues, schema_version)
            for node in inf_nfe.findall('nfe:det', namespace)
        )
        if not items:
            issues.append(ParsedValidationIssue(
                code='MISSING_FIELD',
                severity='ERROR',
                field_path='items',
                message='NF-e sem itens',
            ))
        seen_sequences: set[int] = set()
        for item in items:
            if item.sequence in seen_sequences:
                issues.append(ParsedValidationIssue(
                    code='DUPLICATE_ITEM_SEQUENCE',
                    severity='ERROR',
                    field_path=f'items[{item.sequence}].sequence',
                    message='sequência de item duplicada',
                ))
            seen_sequences.add(item.sequence)

        inf_protocol = None
        if protocol is not None:
            inf_protocol_nodes = protocol.findall('nfe:infProt', namespace)
            if len(inf_protocol_nodes) != 1:
                raise FiscalXmlParseError(
                    'UNSUPPORTED_XML_SCHEMA',
                    'protNFe deve conter exatamente um infProt',
                    schema_version=schema_version,
                )
            inf_protocol = inf_protocol_nodes[0]
            protocol_access_key = _text(inf_protocol, 'nfe:chNFe', namespace)
            if protocol_access_key != access_key:
                raise FiscalXmlParseError(
                    'PROTOCOL_ACCESS_KEY_MISMATCH',
                    'protocolo não corresponde à chave da NF-e',
                    schema_version=schema_version,
                )
        status_code = _bounded(
            _text(inf_protocol, 'nfe:cStat', namespace),
            10,
            'protocol.status_code',
            issues,
        )
        status_reason = _bounded(
            _text(inf_protocol, 'nfe:xMotivo', namespace),
            255,
            'protocol.status_reason',
            issues,
        )
        observed_status = (
            'REPORTED_AUTHORIZED'
            if status_code == '100'
            else f'PROTOCOL_{status_code}' if status_code else 'UNVERIFIED'
        )
        return ParsedNFe55(
            access_key=access_key,
            model=model,
            schema_version=schema_version,
            series=_bounded(
                _text(inf_nfe, 'nfe:ide/nfe:serie', namespace),
                10,
                'series',
                issues,
            ),
            document_number=_bounded(
                _text(inf_nfe, 'nfe:ide/nfe:nNF', namespace),
                20,
                'document_number',
                issues,
            ),
            operation_nature=_bounded(
                _text(inf_nfe, 'nfe:ide/nfe:natOp', namespace),
                255,
                'operation_nature',
                issues,
            ),
            issuer_tax_id=issuer_tax_id,
            issuer_name=issuer_name,
            recipient_tax_id=recipient_tax_id,
            recipient_name=recipient_name,
            issued_at=issued_at,
            movement_at=movement_at,
            products_total=_decimal_field(
                total, 'nfe:vProd', namespace, 'totals.products', issues,
                precision=20, scale=2,
            ),
            freight_total=_decimal_field(
                total, 'nfe:vFrete', namespace, 'totals.freight', issues,
                precision=20, scale=2,
            ),
            insurance_total=_decimal_field(
                total, 'nfe:vSeg', namespace, 'totals.insurance', issues,
                precision=20, scale=2,
            ),
            discount_total=_decimal_field(
                total, 'nfe:vDesc', namespace, 'totals.discount', issues,
                precision=20, scale=2,
            ),
            other_total=_decimal_field(
                total, 'nfe:vOutro', namespace, 'totals.other', issues,
                precision=20, scale=2,
            ),
            tax_total=_decimal_field(
                total, 'nfe:vTotTrib', namespace, 'totals.tax', issues,
                precision=20, scale=2,
            ),
            invoice_total=_decimal_field(
                total, 'nfe:vNF', namespace, 'totals.invoice', issues,
                precision=20, scale=2,
            ),
            observed_status=observed_status,
            protocol_status_code=status_code,
            protocol_status_reason=status_reason,
            items=items,
            issues=tuple(issues),
        )

    def _preflight(self, content: bytes) -> None:
        if len(content) > self._max_xml_bytes:
            raise FiscalXmlParseError('XML_TOO_LARGE', 'XML excede o limite permitido')
        if content.startswith((
            b'\x00\x00\xfe\xff',
            b'\xff\xfe\x00\x00',
            b'\x00\x00\x00<',
            b'<\x00\x00\x00',
        )):
            raise FiscalXmlParseError(
                'UNSUPPORTED_XML_ENCODING',
                'codificação UTF-32 não é suportada',
            )

        parser = expat.ParserCreate()
        parser.StartDoctypeDeclHandler = _reject_unsafe_declaration
        parser.EntityDeclHandler = _reject_unsafe_declaration
        parser.UnparsedEntityDeclHandler = _reject_unsafe_declaration
        parser.NotationDeclHandler = _reject_unsafe_declaration
        parser.ExternalEntityRefHandler = _reject_external_entity
        parser.SkippedEntityHandler = _reject_unsafe_declaration
        parser.SetParamEntityParsing(expat.XML_PARAM_ENTITY_PARSING_NEVER)
        element_count = 0

        def count_element(_: str, __: dict[str, str]) -> None:
            nonlocal element_count
            element_count += 1
            if element_count > self._max_xml_elements:
                raise _XmlStructureLimit

        parser.StartElementHandler = count_element
        try:
            parser.Parse(content, True)
        except _UnsafeXmlDeclaration as error:
            raise FiscalXmlParseError(
                'UNSAFE_XML_DECLARATION',
                'DTD e entidades XML não são permitidas',
            ) from error
        except _XmlStructureLimit as error:
            raise FiscalXmlParseError(
                'XML_STRUCTURE_LIMIT',
                'XML excede o limite de elementos permitido',
            ) from error
        except expat.ExpatError as error:
            raise FiscalXmlParseError('MALFORMED_XML', 'XML malformado') from error


def _parse_item(
    node: ElementTree.Element,
    namespace: dict[str, str],
    issues: list[ParsedValidationIssue],
    schema_version: str,
) -> ParsedFiscalItem:
    raw_sequence = (node.get('nItem') or '').strip()
    try:
        sequence = int(raw_sequence)
    except ValueError as error:
        raise FiscalXmlParseError(
            'INVALID_ITEM_SEQUENCE',
            'sequência de item ausente ou inválida',
            schema_version=schema_version,
        ) from error
    if not 1 <= sequence <= MAX_BIGINT:
        raise FiscalXmlParseError(
            'INVALID_ITEM_SEQUENCE',
            'sequência de item fora do intervalo suportado',
            schema_version=schema_version,
        )
    product = _single_element(node, 'nfe:prod', namespace)
    item_path = f'items[{sequence}]'
    product_code = _bounded(
        _text(product, 'nfe:cProd', namespace),
        100,
        f'{item_path}.product_code',
        issues,
    )
    description = _bounded(
        _text(product, 'nfe:xProd', namespace),
        255,
        f'{item_path}.description',
        issues,
    )
    cfop = _bounded(
        _text(product, 'nfe:CFOP', namespace),
        8,
        f'{item_path}.cfop',
        issues,
    )
    _missing(issues, product_code, f'{item_path}.product_code')
    _missing(issues, description, f'{item_path}.description')
    _missing(issues, cfop, f'{item_path}.cfop')
    included_text = _text(product, 'nfe:indTot', namespace)
    included = _boolean_text(included_text, f'{item_path}.included_in_total', issues)
    return ParsedFiscalItem(
        sequence=sequence,
        product_code=product_code,
        description=description,
        ncm=_bounded(
            _text(product, 'nfe:NCM', namespace),
            16,
            f'{item_path}.ncm',
            issues,
        ),
        cfop=cfop,
        commercial_unit=_bounded(
            _text(product, 'nfe:uCom', namespace),
            10,
            f'{item_path}.commercial_unit',
            issues,
        ),
        quantity=_decimal_field(
            product, 'nfe:qCom', namespace, f'{item_path}.quantity', issues,
            precision=20, scale=6,
        ),
        unit_value=_decimal_field(
            product, 'nfe:vUnCom', namespace, f'{item_path}.unit_value', issues,
            precision=20, scale=10,
        ),
        gross_total=_decimal_field(
            product, 'nfe:vProd', namespace, f'{item_path}.gross_total', issues,
            precision=20, scale=2,
        ),
        discount_total=_decimal_field(
            product, 'nfe:vDesc', namespace, f'{item_path}.discount', issues,
            precision=20, scale=2, required=False,
        ),
        other_total=_decimal_field(
            product, 'nfe:vOutro', namespace, f'{item_path}.other', issues,
            precision=20, scale=2, required=False,
        ),
        included_in_total=included,
        taxes=_parse_taxes(node, namespace, issues, item_path),
    )


def _parse_taxes(
    item: ElementTree.Element,
    namespace: dict[str, str],
    issues: list[ParsedValidationIssue],
    item_path: str,
) -> tuple[ParsedTaxDetail, ...]:
    tax_root = _single_element(item, 'nfe:imposto', namespace)
    if tax_root is None:
        return ()
    field_map = {
        'ICMS': ('vBC', 'pICMS', 'vICMS'),
        'ICMSUFDest': ('vBCUFDest', 'pICMSUFDest', 'vICMSUFDest'),
        'IPI': ('vBC', 'pIPI', 'vIPI'),
        'II': ('vBC', '', 'vII'),
        'PIS': ('vBC', 'pPIS', 'vPIS'),
        'PISST': ('vBC', 'pPIS', 'vPIS'),
        'COFINS': ('vBC', 'pCOFINS', 'vCOFINS'),
        'COFINSST': ('vBC', 'pCOFINS', 'vCOFINS'),
        'ISSQN': ('vBC', 'vAliq', 'vISSQN'),
    }
    details: list[ParsedTaxDetail] = []
    seen_types: set[str] = set()
    for container in list(tax_root):
        tax_type = _nfe_local_name(container.tag)
        if tax_type is None:
            issues.append(ParsedValidationIssue(
                code='UNSUPPORTED_TAX_NAMESPACE',
                severity='ERROR',
                field_path=f'{item_path}.taxes',
                message='grupo tributário fora do namespace NF-e',
            ))
            continue
        if len(tax_type) > 64:
            issues.append(ParsedValidationIssue(
                code='XML_NAME_TOO_LONG',
                severity='ERROR',
                field_path=f'{item_path}.taxes',
                message='nome de grupo tributário excede o limite seguro',
            ))
            continue
        if tax_type not in field_map:
            issues.append(ParsedValidationIssue(
                code='UNSUPPORTED_TAX_GROUP',
                severity='WARNING',
                field_path=f'{item_path}.taxes.{tax_type}',
                message='grupo tributário presente ainda não normalizado',
            ))
            continue
        if tax_type in seen_types:
            issues.append(ParsedValidationIssue(
                code='DUPLICATE_TAX_GROUP',
                severity='ERROR',
                field_path=f'{item_path}.taxes.{tax_type}',
                message='grupo tributário aparece mais de uma vez',
            ))
            continue
        seen_types.add(tax_type)
        group = _tax_group(container, tax_type)
        base_name, rate_name, amount_name = field_map[tax_type]
        prefix = f'{item_path}.taxes.{tax_type}'
        details.append(ParsedTaxDetail(
            tax_type=tax_type,
            tax_status=_bounded(
                _child_text(group, 'CST') or _child_text(group, 'CSOSN'),
                10,
                f'{prefix}.status',
                issues,
            ),
            calculation_base=_decimal_text(
                _child_text(group, base_name),
                f'{prefix}.base',
                issues,
                precision=20,
                scale=2,
            ),
            rate=_decimal_text(
                _child_text(group, rate_name) if rate_name else None,
                f'{prefix}.rate',
                issues,
                precision=12,
                scale=6,
            ),
            amount=_decimal_text(
                _child_text(group, amount_name),
                f'{prefix}.amount',
                issues,
                precision=20,
                scale=2,
            ),
        ))
    return tuple(details)


def _tax_group(
    container: ElementTree.Element,
    tax_type: str,
) -> ElementTree.Element:
    matches = tuple(
        child
        for child in list(container)
        if (
            (local_name := _nfe_local_name(child.tag)) is not None
            and local_name.startswith(tax_type)
        )
    )
    if len(matches) > 1:
        raise FiscalXmlParseError(
            'DUPLICATE_XML_FIELD',
            'grupo tributário contém mais de um enquadramento',
        )
    if matches:
        return matches[0]
    return container


def _text(
    parent: ElementTree.Element | None,
    path: str,
    namespace: dict[str, str],
) -> str | None:
    if parent is None:
        return None
    node = _single_element(parent, path, namespace)
    if node is None or node.text is None:
        return None
    value = node.text.strip()
    return value or None


def _child_text(parent: ElementTree.Element, local_name: str) -> str | None:
    matches = tuple(
        child
        for child in list(parent)
        if child.tag == f'{NFE_TAG_PREFIX}{local_name}'
    )
    if len(matches) > 1:
        raise FiscalXmlParseError(
            'DUPLICATE_XML_FIELD',
            'campo tributário aparece mais de uma vez',
        )
    if not matches or matches[0].text is None:
        return None
    value = matches[0].text.strip()
    return value or None


def _party_identifier(
    parent: ElementTree.Element | None,
    namespace: dict[str, str],
) -> str | None:
    identifiers = tuple(
        value
        for value in (
            _text(parent, 'nfe:CNPJ', namespace),
            _text(parent, 'nfe:CPF', namespace),
            _text(parent, 'nfe:idEstrangeiro', namespace),
        )
        if value is not None
    )
    if len(identifiers) > 1:
        raise FiscalXmlParseError(
            'DUPLICATE_XML_FIELD',
            'parte da NF-e possui mais de um identificador',
        )
    return identifiers[0] if identifiers else None


def _single_element(
    parent: ElementTree.Element,
    path: str,
    namespace: dict[str, str],
) -> ElementTree.Element | None:
    current = parent
    for segment in path.split('/'):
        matches = current.findall(segment, namespace)
        if len(matches) > 1:
            raise FiscalXmlParseError(
                'DUPLICATE_XML_FIELD',
                'campo ou grupo XML aparece mais de uma vez',
            )
        if not matches:
            return None
        current = matches[0]
    return current


def _decimal_field(
    parent: ElementTree.Element | None,
    path: str,
    namespace: dict[str, str],
    field_path: str,
    issues: list[ParsedValidationIssue],
    *,
    precision: int,
    scale: int,
    required: bool = True,
) -> Decimal | None:
    value = _text(parent, path, namespace)
    if value is None and required:
        _missing(issues, value, field_path)
    return _decimal_text(
        value,
        field_path,
        issues,
        precision=precision,
        scale=scale,
    )


def _decimal_text(
    value: str | None,
    field_path: str,
    issues: list[ParsedValidationIssue],
    *,
    precision: int,
    scale: int,
) -> Decimal | None:
    if value is None:
        return None
    if not XML_DECIMAL_PATTERN.fullmatch(value):
        issues.append(ParsedValidationIssue(
            code='INVALID_DECIMAL',
            severity='ERROR',
            field_path=field_path,
            message='valor decimal inválido',
        ))
        return None
    if len(value) > 256:
        issues.append(ParsedValidationIssue(
            code='DECIMAL_OUT_OF_RANGE',
            severity='ERROR',
            field_path=field_path,
            message='valor decimal excede o limite seguro',
        ))
        return None
    try:
        parsed = Decimal(value)
    except InvalidOperation:
        issues.append(ParsedValidationIssue(
            code='INVALID_DECIMAL',
            severity='ERROR',
            field_path=field_path,
            message='valor decimal inválido',
        ))
        return None
    if not parsed.is_finite():
        issues.append(ParsedValidationIssue(
            code='INVALID_DECIMAL',
            severity='ERROR',
            field_path=field_path,
            message='valor decimal deve ser finito',
        ))
        return None
    if not _fits_decimal(parsed, precision=precision, scale=scale):
        issues.append(ParsedValidationIssue(
            code='DECIMAL_OUT_OF_RANGE',
            severity='ERROR',
            field_path=field_path,
            message='valor decimal excede a precisão ou escala suportada',
        ))
        return None
    return parsed


def _fits_decimal(value: Decimal, *, precision: int, scale: int) -> bool:
    _, raw_digits, exponent = value.as_tuple()
    digits = tuple(raw_digits)
    if exponent < -scale:
        excess = -scale - exponent
        if any(digits[-excess:]):
            return False
        digits = digits[:-excess] or (0,)
        exponent += excess
    integer_digits = max(len(digits) + exponent, 0)
    return integer_digits <= precision - scale


def _datetime_value(
    value: str | None,
    field_path: str,
    issues: list[ParsedValidationIssue],
    *,
    required: bool = True,
) -> datetime | None:
    if value is None:
        if required:
            _missing(issues, value, field_path)
        return None
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        issues.append(ParsedValidationIssue(
            code='INVALID_DATETIME',
            severity='ERROR',
            field_path=field_path,
            message='data/hora inválida',
        ))
        return None
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        issues.append(ParsedValidationIssue(
            code='DATETIME_WITHOUT_TIMEZONE',
            severity='ERROR',
            field_path=field_path,
            message='data/hora sem timezone',
        ))
        return None
    try:
        utc_value = parsed.astimezone(UTC)
    except (OverflowError, ValueError):
        utc_value = None
    if utc_value is None or utc_value.year < 1000:
        issues.append(ParsedValidationIssue(
            code='DATETIME_OUT_OF_RANGE',
            severity='ERROR',
            field_path=field_path,
            message='data/hora fora do intervalo persistível',
        ))
        return None
    return parsed


def _boolean_text(
    value: str | None,
    field_path: str,
    issues: list[ParsedValidationIssue],
) -> bool | None:
    if value is None:
        return None
    if value == '1':
        return True
    if value == '0':
        return False
    issues.append(ParsedValidationIssue(
        code='INVALID_BOOLEAN',
        severity='ERROR',
        field_path=field_path,
        message='indicador booleano inválido',
    ))
    return None


def _bounded(
    value: str | None,
    max_length: int,
    field_path: str,
    issues: list[ParsedValidationIssue],
) -> str | None:
    if value is not None and len(value) > max_length:
        issues.append(ParsedValidationIssue(
            code='FIELD_TOO_LONG',
            severity='ERROR',
            field_path=field_path,
            message='campo excede o limite persistível',
        ))
    return value


def _missing(
    issues: list[ParsedValidationIssue],
    value: object | None,
    field_path: str,
) -> None:
    if value is None:
        issues.append(ParsedValidationIssue(
            code='MISSING_FIELD',
            severity='WARNING',
            field_path=field_path,
            message='campo ausente no XML; nenhum valor foi inferido',
        ))


def _nfe_local_name(tag: str) -> str | None:
    if not tag.startswith(NFE_TAG_PREFIX):
        return None
    return tag[len(NFE_TAG_PREFIX):]


def _has_valid_access_key_digit(access_key: str) -> bool:
    weighted_sum = 0
    weight = 2
    for digit in reversed(access_key[:-1]):
        weighted_sum += int(digit) * weight
        weight = 2 if weight == 9 else weight + 1
    remainder = weighted_sum % 11
    expected = 0 if remainder in {0, 1} else 11 - remainder
    return int(access_key[-1]) == expected


class _UnsafeXmlDeclaration(Exception):
    '''Sinal interno levantado antes que qualquer entidade seja expandida.'''


class _XmlStructureLimit(Exception):
    '''Sinal interno para interromper XML excessivamente estruturado.'''


def _reject_unsafe_declaration(*_: object) -> None:
    raise _UnsafeXmlDeclaration


def _reject_external_entity(*_: object) -> int:
    raise _UnsafeXmlDeclaration
