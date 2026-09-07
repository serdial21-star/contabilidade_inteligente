from decimal import Decimal
from pathlib import Path

import pytest

from serdial21.modules.fiscal_documents.adapters.inbound.nfe55_xml import (
    SafeNFe55XmlParser,
)
from serdial21.modules.fiscal_documents.application.ports.parser import (
    FiscalXmlParseError,
)


FIXTURES = Path(__file__).resolve().parents[1] / 'fixtures' / 'nfe55'


def fixture(name: str) -> bytes:
    return (FIXTURES / name).read_bytes()


def test_parses_valid_nfe55_without_float() -> None:
    parsed = SafeNFe55XmlParser().parse(fixture('valid_minimal.xml'))

    assert parsed.access_key == '35260912345678000195550010000000011000000011'
    assert parsed.model == '55'
    assert parsed.schema_version == '4.00'
    assert parsed.issuer_tax_id == '12345678000195'
    assert parsed.recipient_tax_id == '98765432000198'
    assert parsed.invoice_total == Decimal('100.00')
    assert parsed.observed_status == 'REPORTED_AUTHORIZED'
    assert len(parsed.items) == 1
    assert parsed.items[0].cfop == '5102'
    assert parsed.items[0].quantity == Decimal('2.000000')
    assert parsed.items[0].unit_value == Decimal('50.0000000000')
    assert all(isinstance(value, Decimal) for value in (
        parsed.products_total,
        parsed.freight_total,
        parsed.insurance_total,
        parsed.discount_total,
        parsed.other_total,
        parsed.tax_total,
        parsed.invoice_total,
        parsed.items[0].quantity,
        parsed.items[0].unit_value,
        parsed.items[0].gross_total,
    ))
    assert [tax.tax_type for tax in parsed.items[0].taxes] == [
        'ICMS', 'PIS', 'COFINS'
    ]
    assert parsed.items[0].taxes[0].tax_status == '00'
    assert parsed.items[0].taxes[0].calculation_base == Decimal('100.00')
    assert parsed.items[0].taxes[0].rate == Decimal('18.000000')
    assert parsed.items[0].taxes[0].amount == Decimal('18.00')


def test_preserves_missing_recipient_as_none_and_reports_issues() -> None:
    parsed = SafeNFe55XmlParser().parse(fixture('missing_recipient.xml'))

    assert parsed.recipient_tax_id is None
    assert parsed.recipient_name is None
    assert {
        issue.field_path
        for issue in parsed.issues
        if issue.code == 'MISSING_FIELD'
    } >= {'recipient.tax_id', 'recipient.name'}


@pytest.mark.parametrize(
    ('content', 'expected_code'),
    [
        (b'<NFe>', 'MALFORMED_XML'),
        (
            b'<!DOCTYPE x [<!ENTITY boom SYSTEM \'file:///etc/passwd\'>]><x>&boom;</x>',
            'UNSAFE_XML_DECLARATION',
        ),
    ],
)
def test_rejects_invalid_or_malicious_xml(
    content: bytes,
    expected_code: str,
) -> None:
    with pytest.raises(FiscalXmlParseError) as failure:
        SafeNFe55XmlParser().parse(content)

    assert failure.value.code == expected_code


def test_rejects_oversized_xml_before_parsing() -> None:
    with pytest.raises(FiscalXmlParseError) as failure:
        SafeNFe55XmlParser(max_xml_bytes=32).parse(b'<' + b'x' * 32)

    assert failure.value.code == 'XML_TOO_LARGE'


def test_rejects_xml_with_too_many_elements_before_tree_construction() -> None:
    content = b'<root><node/><node/><node/></root>'

    with pytest.raises(FiscalXmlParseError) as failure:
        SafeNFe55XmlParser(max_xml_elements=3).parse(content)

    assert failure.value.code == 'XML_STRUCTURE_LIMIT'


def test_rejects_entity_expansion_encoded_as_utf16() -> None:
    content = (
        '<?xml version=\x271.0\x27 encoding=\x27UTF-16\x27?>'
        '<!DOCTYPE NFe [<!ENTITY boom \x27expanded\x27>]>'
        '<NFe>&boom;</NFe>'
    ).encode('utf-16')

    with pytest.raises(FiscalXmlParseError) as failure:
        SafeNFe55XmlParser().parse(content)

    assert failure.value.code == 'UNSAFE_XML_DECLARATION'


@pytest.mark.parametrize('encoding', ['utf-32-le', 'utf-32-be'])
def test_rejects_unsupported_utf32_deterministically(encoding: str) -> None:
    bom = b'\xff\xfe\x00\x00' if encoding.endswith('le') else b'\x00\x00\xfe\xff'
    content = bom + '<NFe/>'.encode(encoding)

    with pytest.raises(FiscalXmlParseError) as failure:
        SafeNFe55XmlParser().parse(content)

    assert failure.value.code == 'UNSUPPORTED_XML_ENCODING'


@pytest.mark.parametrize('raw_value', ['NaN', 'Infinity', '-Infinity', '1E2'])
def test_rejects_non_finite_or_non_decimal_lexical_values(
    raw_value: str,
) -> None:
    content = fixture('valid_minimal.xml').replace(
        b'<vNF>100.00</vNF>',
        f'<vNF>{raw_value}</vNF>'.encode(),
    )

    parsed = SafeNFe55XmlParser().parse(content)

    assert parsed.invoice_total is None
    assert any(
        issue.code == 'INVALID_DECIMAL'
        and issue.field_path == 'totals.invoice'
        and issue.severity == 'ERROR'
        for issue in parsed.issues
    )


@pytest.mark.parametrize('raw_value', ['100.001', '1000000000000000000.00'])
def test_rejects_decimal_that_cannot_be_persisted_exactly(
    raw_value: str,
) -> None:
    content = fixture('valid_minimal.xml').replace(
        b'<vNF>100.00</vNF>',
        f'<vNF>{raw_value}</vNF>'.encode(),
    )

    parsed = SafeNFe55XmlParser().parse(content)

    assert parsed.invoice_total is None
    assert any(
        issue.code == 'DECIMAL_OUT_OF_RANGE'
        and issue.field_path == 'totals.invoice'
        for issue in parsed.issues
    )


def test_invalid_total_indicator_is_not_inferred_as_false() -> None:
    content = fixture('valid_minimal.xml').replace(
        b'<indTot>1</indTot>',
        b'<indTot>invalid</indTot>',
    )

    parsed = SafeNFe55XmlParser().parse(content)

    assert parsed.items[0].included_in_total is None
    assert any(
        issue.code == 'INVALID_BOOLEAN'
        and issue.field_path == 'items[1].included_in_total'
        for issue in parsed.issues
    )


def test_rejects_arbitrary_wrapper_around_nfe() -> None:
    nfe = fixture('valid_minimal.xml').split(b'?>', 1)[1]

    with pytest.raises(FiscalXmlParseError) as failure:
        SafeNFe55XmlParser().parse(b'<wrapper>' + nfe + b'</wrapper>')

    assert failure.value.code == 'UNSUPPORTED_XML_SCHEMA'


def test_rejects_protocol_for_another_access_key() -> None:
    content = fixture('valid_minimal.xml').replace(
        b'<chNFe>35260912345678000195550010000000011000000011</chNFe>',
        b'<chNFe>35260912345678000195550010000000011000000012</chNFe>',
    )

    with pytest.raises(FiscalXmlParseError) as failure:
        SafeNFe55XmlParser().parse(content)

    assert failure.value.code == 'PROTOCOL_ACCESS_KEY_MISMATCH'


def test_rejects_invalid_access_key_check_digit() -> None:
    content = fixture('valid_minimal.xml').replace(
        b'35260912345678000195550010000000011000000011',
        b'35260912345678000195550010000000011000000010',
    )

    with pytest.raises(FiscalXmlParseError) as failure:
        SafeNFe55XmlParser().parse(content)

    assert failure.value.code == 'INVALID_ACCESS_KEY'


def test_duplicate_scalar_field_is_rejected_instead_of_choosing_first() -> None:
    content = fixture('valid_minimal.xml').replace(
        b'<mod>55</mod>',
        b'<mod>55</mod><mod>55</mod>',
    )

    with pytest.raises(FiscalXmlParseError) as failure:
        SafeNFe55XmlParser().parse(content)

    assert failure.value.code == 'DUPLICATE_XML_FIELD'


def test_duplicate_item_sequence_becomes_blocking_issue() -> None:
    second_item = b'''
      <det nItem='1'>
        <prod>
          <cProd>PROD-002</cProd>
          <xProd>OUTRO PRODUTO SINTETICO</xProd>
          <CFOP>5102</CFOP>
          <uCom>UN</uCom>
          <qCom>1.000000</qCom>
          <vUnCom>1.0000000000</vUnCom>
          <vProd>1.00</vProd>
        </prod>
      </det>'''
    content = fixture('valid_minimal.xml').replace(
        b'</det>',
        b'</det>' + second_item,
        1,
    )

    parsed = SafeNFe55XmlParser().parse(content)

    assert any(
        issue.code == 'DUPLICATE_ITEM_SEQUENCE'
        and issue.severity == 'ERROR'
        for issue in parsed.issues
    )


def test_tax_group_in_foreign_namespace_is_not_extracted() -> None:
    content = (
        fixture('valid_minimal.xml')
        .replace(b'<ICMS>', b'<evil:ICMS xmlns:evil=\x27urn:evil\x27>')
        .replace(b'</ICMS>', b'</evil:ICMS>')
    )

    parsed = SafeNFe55XmlParser().parse(content)

    assert [tax.tax_type for tax in parsed.items[0].taxes] == ['PIS', 'COFINS']
    assert any(
        issue.code == 'UNSUPPORTED_TAX_NAMESPACE'
        and issue.severity == 'ERROR'
        for issue in parsed.issues
    )


def test_rejects_fiscal_model_other_than_55() -> None:
    content = fixture('valid_minimal.xml').replace(b'<mod>55</mod>', b'<mod>65</mod>')

    with pytest.raises(FiscalXmlParseError) as failure:
        SafeNFe55XmlParser().parse(content)

    assert failure.value.code == 'UNSUPPORTED_DOCUMENT_MODEL'
