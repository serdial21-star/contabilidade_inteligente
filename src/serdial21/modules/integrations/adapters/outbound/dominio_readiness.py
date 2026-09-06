'''Gate determinístico anterior ao adaptador Domínio, sem gerar qualquer TXT.'''

from dataclasses import dataclass


class DominioExportNotReadyError(RuntimeError):
    '''Recusa uma exportação que não atingiu todos os controles prévios.'''


@dataclass(frozen=True, slots=True)
class DominioExportReadiness:
    layout_version_approved: bool
    golden_file_registered: bool
    mandatory_mapping_complete: bool
    proposal_approved: bool
    accounting_lock_active: bool


def assert_dominio_export_ready(readiness: DominioExportReadiness) -> None:
    failures: list[str] = []
    if not readiness.layout_version_approved:
        failures.append('LAYOUT_VERSION_NOT_APPROVED')
    if not readiness.golden_file_registered:
        failures.append('GOLDEN_FILE_NOT_REGISTERED')
    if not readiness.mandatory_mapping_complete:
        failures.append('MANDATORY_MAPPING_INCOMPLETE')
    if not readiness.proposal_approved:
        failures.append('PROPOSAL_NOT_APPROVED')
    if readiness.accounting_lock_active:
        failures.append('ACCOUNTING_LOCK_ACTIVE')
    if failures:
        raise DominioExportNotReadyError(','.join(failures))
