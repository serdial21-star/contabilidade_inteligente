'''Regras canônicas para CPF e CNPJ numérico ou alfanumérico.'''

import pytest

from serdial21.modules.access_control.domain.tax_identifiers import (
    canonicalize_tax_identifier,
    is_valid_cnpj,
    is_valid_cpf,
    tax_identifier_kind,
    validate_tax_identifier,
)


@pytest.mark.parametrize(
    ('raw', 'canonical'),
    [
        ('529.982.247-25', '52998224725'),
        ('12.abc.345/01de-35', '12ABC34501DE35'),
        (' 00.000.000/E08G-12 ', '00000000E08G12'),
    ],
)
def test_canonicalize_accepts_only_display_separators(raw: str, canonical: str) -> None:
    assert canonicalize_tax_identifier(raw) == canonical


@pytest.mark.parametrize('raw', ['12_ABC_345_01DE_35', '12@ABC34501DE35', '１２３'])
def test_canonicalize_rejects_unapproved_or_non_ascii_characters(raw: str) -> None:
    assert canonicalize_tax_identifier(raw) is None


@pytest.mark.parametrize('value', ['52998224725', '11144477735'])
def test_valid_cpf(value: str) -> None:
    assert tax_identifier_kind(value) == 'CPF'
    assert is_valid_cpf(value)


@pytest.mark.parametrize('value', ['52998224724', '00000000000', '5299822472A'])
def test_invalid_cpf(value: str) -> None:
    assert not is_valid_cpf(value)


@pytest.mark.parametrize(
    'value',
    ['12345678000195', '12ABC34501DE35', '00000000E08G12'],
)
def test_valid_numeric_and_alphanumeric_cnpj(value: str) -> None:
    assert tax_identifier_kind(value) == 'CNPJ'
    assert is_valid_cnpj(value)


@pytest.mark.parametrize(
    'value',
    ['12345678000194', '12ABC34501DE34', '00000000000000', '12ABC34501DEAA'],
)
def test_invalid_cnpj(value: str) -> None:
    assert not is_valid_cnpj(value)


def test_validate_returns_canonical_value_and_kind() -> None:
    assert validate_tax_identifier('12.abc.345/01de-35') == ('12ABC34501DE35', 'CNPJ')
    assert validate_tax_identifier('529.982.247-24') is None
