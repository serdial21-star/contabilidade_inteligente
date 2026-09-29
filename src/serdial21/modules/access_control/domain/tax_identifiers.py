'''Normaliza e valida CPF e CNPJ, inclusive o CNPJ alfanumérico.'''

from __future__ import annotations

from typing import Literal


TaxIdentifierKind = Literal['CPF', 'CNPJ']

_DISPLAY_SEPARATORS = frozenset('.-/ ')
_CNPJ_FIRST_WEIGHTS = (5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2)
_CNPJ_SECOND_WEIGHTS = (6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2)


def canonicalize_tax_identifier(value: str | None) -> str | None:
    '''Remove somente separadores de exibição e converte letras para maiúsculas.'''

    stripped = (value or '').strip().upper()
    if not stripped:
        return None
    if any(
        not ('0' <= character <= '9' or 'A' <= character <= 'Z')
        and character not in _DISPLAY_SEPARATORS
        for character in stripped
    ):
        return None
    canonical = ''.join(
        character for character in stripped if character not in _DISPLAY_SEPARATORS
    )
    return canonical or None


def tax_identifier_kind(value: str) -> TaxIdentifierKind | None:
    if len(value) == 11 and value.isascii() and value.isdigit():
        return 'CPF'
    if (
        len(value) == 14
        and value.isascii()
        and all(character.isdigit() or 'A' <= character <= 'Z' for character in value[:12])
        and value[12:].isdigit()
    ):
        return 'CNPJ'
    return None


def is_valid_cpf(value: str) -> bool:
    if len(value) != 11 or not value.isascii() or not value.isdigit():
        return False
    if len(set(value)) == 1:
        return False
    digits = tuple(int(character) for character in value)
    first = _cpf_digit(digits[:9], 10)
    second = _cpf_digit((*digits[:9], first), 11)
    return digits[-2:] == (first, second)


def is_valid_cnpj(value: str) -> bool:
    if tax_identifier_kind(value) != 'CNPJ':
        return False
    if value.isdigit() and len(set(value)) == 1:
        return False
    first = _cnpj_digit(value[:12], _CNPJ_FIRST_WEIGHTS)
    second = _cnpj_digit(f'{value[:12]}{first}', _CNPJ_SECOND_WEIGHTS)
    return value[-2:] == f'{first}{second}'


def validate_tax_identifier(value: str | None) -> tuple[str, TaxIdentifierKind] | None:
    canonical = canonicalize_tax_identifier(value)
    if canonical is None:
        return None
    kind = tax_identifier_kind(canonical)
    if kind == 'CPF' and is_valid_cpf(canonical):
        return canonical, kind
    if kind == 'CNPJ' and is_valid_cnpj(canonical):
        return canonical, kind
    return None


def _cpf_digit(digits: tuple[int, ...], initial_weight: int) -> int:
    total = sum(digit * weight for digit, weight in zip(
        digits, range(initial_weight, 1, -1), strict=True,
    ))
    remainder = total % 11
    return 0 if remainder < 2 else 11 - remainder


def _cnpj_digit(base: str, weights: tuple[int, ...]) -> int:
    total = sum((ord(character) - 48) * weight for character, weight in zip(
        base, weights, strict=True,
    ))
    remainder = total % 11
    return 0 if remainder in (0, 1) else 11 - remainder
