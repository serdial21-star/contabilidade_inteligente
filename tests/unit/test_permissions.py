import pytest

from serdial21.modules.access_control.domain.permissions import (
    INITIAL_PERMISSION_CODES,
    PermissionCode,
)


@pytest.mark.parametrize('code', INITIAL_PERMISSION_CODES)
def test_initial_permissions_are_atomic(code: str) -> None:
    assert str(PermissionCode(code)) == code


@pytest.mark.parametrize(
    'code',
    (
        'company',
        'company.*',
        '*.read',
        'Company.read',
        'company read',
    ),
)
def test_non_atomic_permission_is_rejected(code: str) -> None:
    with pytest.raises(ValueError, match='atômica|wildcards'):
        PermissionCode(code)
