'''Códigos atômicos de permissão.'''

from dataclasses import dataclass
import re


PERMISSION_PATTERN = re.compile(r'^[a-z][a-z0-9_]*[.][a-z][a-z0-9_]*$')

INITIAL_PERMISSION_CODES: tuple[str, ...] = (
    'company.read',
    'company.manage',
    'journal.read',
    'journal.propose',
    'journal.approve',
    'reconciliation.manage',
    'lock.manage',
    'export.execute',
    'audit.read',
)


@dataclass(frozen=True, slots=True)
class PermissionCode:
    value: str

    def __post_init__(self) -> None:
        if not PERMISSION_PATTERN.fullmatch(self.value):
            raise ValueError('permissão deve representar uma única ação atômica')
        if '*' in self.value:
            raise ValueError('wildcards de permissão não são permitidos')

    def __str__(self) -> str:
        return self.value
