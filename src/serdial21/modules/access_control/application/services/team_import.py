'''Import manual e idempotente da equipe interna (ADR 0013, item 2).

Nunca lê senha, endereço, contato de emergência, telefone ou observação do
sistema de origem: só o mínimo para identificar e vincular a pessoa. O vínculo
com empresa usa somente correspondência EXATA de nome normalizado; ambiguidade
ou ausência é reportada, nunca resolvida por aproximação.
'''

from dataclasses import dataclass
from datetime import datetime
import re
from typing import Protocol
from unicodedata import normalize
from uuid import UUID

from serdial21.modules.access_control.application.services.company_import import (
    EXTERNAL_SYSTEM_SISTEMA_A,
    CLIENT_EXTERNAL_TYPE,
    ConflictDetail,
    SkippedRecord,
)


STAFF_EXTERNAL_TYPE = 'funcionario'
RESPONSIBLE_ROLE_LABEL = 'responsavel'
_STATUS_MAP = {'Ativo': 'active', 'Inativo': 'inactive'}


@dataclass(frozen=True, slots=True)
class ExternalStaffRecord:
    external_id: str
    nome_funcionario: str
    email: str | None
    cargo: str | None
    status: str


@dataclass(frozen=True, slots=True)
class MappedTeamMember:
    external_id: str
    display_name: str
    email: str | None
    job_title: str | None
    status: str


def map_external_staff(record: ExternalStaffRecord) -> MappedTeamMember | SkippedRecord:
    status = _STATUS_MAP.get(record.status)
    if status is None:
        return SkippedRecord(record.external_id, reason=f'status_nao_mapeado:{record.status}')
    name = ' '.join(record.nome_funcionario.split())
    if not name:
        return SkippedRecord(record.external_id, reason='sem_nome')
    email = (record.email or '').strip().lower() or None
    title = (record.cargo or '').strip() or None
    return MappedTeamMember(record.external_id, name, email, title, status)


def normalize_person_name(value: str) -> str:
    stripped = ''.join(
        char for char in normalize('NFKD', value) if not re.match(r'[̀-ͯ]', char)
    )
    return ' '.join(stripped.casefold().split())


@dataclass(frozen=True, slots=True)
class TeamMemberSnapshot:
    id: UUID
    display_name: str
    email: str | None
    job_title: str | None
    status: str
    external_id: str | None


class TeamImportRepository(Protocol):
    def find_member_by_external_reference(
        self, tenant_id: UUID, external_system: str, external_type: str, external_id: str,
    ) -> TeamMemberSnapshot | None: ...

    def find_member_by_email(self, tenant_id: UUID, email: str) -> TeamMemberSnapshot | None: ...

    def list_members(self, tenant_id: UUID) -> list[TeamMemberSnapshot]: ...

    def create_member(
        self, tenant_id: UUID, mapped: MappedTeamMember, *, external_system: str,
        external_type: str, now: datetime,
    ) -> UUID: ...

    def find_company_id_by_external_reference(
        self, tenant_id: UUID, external_system: str, external_type: str, external_id: str,
    ) -> UUID | None: ...

    def assignment_exists(
        self, tenant_id: UUID, company_id: UUID, member_id: UUID, role_label: str,
    ) -> bool: ...

    def create_assignment(
        self, tenant_id: UUID, company_id: UUID, member_id: UUID, role_label: str,
        *, now: datetime,
    ) -> UUID: ...


@dataclass(frozen=True, slots=True)
class TeamImportReport:
    created: tuple[UUID, ...]
    unchanged: tuple[str, ...]
    conflicts: tuple[ConflictDetail, ...]
    skipped: tuple[SkippedRecord, ...]


class ImportExternalTeam:
    def __init__(self, repository: TeamImportRepository) -> None:
        self._repository = repository

    def execute(
        self, tenant_id: UUID, records: list[ExternalStaffRecord], *, now: datetime,
    ) -> TeamImportReport:
        created: list[UUID] = []
        unchanged: list[str] = []
        conflicts: list[ConflictDetail] = []
        skipped: list[SkippedRecord] = []
        for record in records:
            decision = map_external_staff(record)
            if isinstance(decision, SkippedRecord):
                skipped.append(decision)
                continue
            existing = self._repository.find_member_by_external_reference(
                tenant_id, EXTERNAL_SYSTEM_SISTEMA_A, STAFF_EXTERNAL_TYPE, decision.external_id,
            )
            if existing is not None:
                same = (
                    existing.display_name == decision.display_name
                    and existing.email == decision.email
                    and existing.job_title == decision.job_title
                    and existing.status == decision.status
                )
                if same:
                    unchanged.append(decision.external_id)
                else:
                    conflicts.append(ConflictDetail(decision.external_id, 'conteudo_divergente'))
                continue
            if decision.email is not None:
                by_email = self._repository.find_member_by_email(tenant_id, decision.email)
                if by_email is not None:
                    conflicts.append(ConflictDetail(decision.external_id, 'email_em_uso'))
                    continue
            created.append(self._repository.create_member(
                tenant_id, decision, external_system=EXTERNAL_SYSTEM_SISTEMA_A,
                external_type=STAFF_EXTERNAL_TYPE, now=now,
            ))
        return TeamImportReport(tuple(created), tuple(unchanged), tuple(conflicts), tuple(skipped))


@dataclass(frozen=True, slots=True)
class ExternalResponsibleRecord:
    '''Par (cliente, `responsavel` em texto livre) vindo de `clientes`.'''

    company_external_id: str
    responsavel: str | None


@dataclass(frozen=True, slots=True)
class AssignmentReport:
    created: tuple[UUID, ...]
    unchanged: tuple[str, ...]
    without_responsible: tuple[str, ...]
    company_missing: tuple[str, ...]
    unmatched: tuple[str, ...]
    ambiguous: tuple[str, ...]
    inactive_member: tuple[str, ...]


class AssignResponsibleFromExternalClients:
    '''Vincula empresa -> membro por nome exato normalizado; nunca por aproximação.'''

    def __init__(self, repository: TeamImportRepository) -> None:
        self._repository = repository

    def execute(
        self, tenant_id: UUID, records: list[ExternalResponsibleRecord], *, now: datetime,
    ) -> AssignmentReport:
        by_name: dict[str, list[TeamMemberSnapshot]] = {}
        for member in self._repository.list_members(tenant_id):
            by_name.setdefault(normalize_person_name(member.display_name), []).append(member)

        created: list[UUID] = []
        unchanged: list[str] = []
        without: list[str] = []
        missing: list[str] = []
        unmatched: list[str] = []
        ambiguous: list[str] = []
        inactive: list[str] = []
        for record in records:
            key = normalize_person_name(record.responsavel or '')
            if not key:
                without.append(record.company_external_id)
                continue
            company_id = self._repository.find_company_id_by_external_reference(
                tenant_id, EXTERNAL_SYSTEM_SISTEMA_A, CLIENT_EXTERNAL_TYPE,
                record.company_external_id,
            )
            if company_id is None:
                missing.append(record.company_external_id)
                continue
            candidates = by_name.get(key, [])
            if not candidates:
                unmatched.append(record.company_external_id)
                continue
            if len(candidates) > 1:
                ambiguous.append(record.company_external_id)
                continue
            member = candidates[0]
            if member.status != 'active':
                inactive.append(record.company_external_id)
                continue
            if self._repository.assignment_exists(
                tenant_id, company_id, member.id, RESPONSIBLE_ROLE_LABEL,
            ):
                unchanged.append(record.company_external_id)
                continue
            created.append(self._repository.create_assignment(
                tenant_id, company_id, member.id, RESPONSIBLE_ROLE_LABEL, now=now,
            ))
        return AssignmentReport(
            tuple(created), tuple(unchanged), tuple(without), tuple(missing),
            tuple(unmatched), tuple(ambiguous), tuple(inactive),
        )
