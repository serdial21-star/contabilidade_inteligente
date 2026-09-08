'''Composição da borda operacional sobre casos de uso existentes.'''

from sqlalchemy.orm import Session

from serdial21.bootstrap.nfe55 import create_nfe55_runtime
from serdial21.bootstrap.nfe_to_dominio import create_nfe_to_dominio_runtime
from serdial21.bootstrap.settings import AppSettings
from serdial21.modules.access_control.adapters.outbound.persistence.repositories import SqlAlchemyAuthorizationRepository
from serdial21.modules.access_control.application.services.authorization import AuthorizationService
from serdial21.modules.audit.adapters.outbound.persistence.repositories import SqlAlchemyAuditRepository
from serdial21.modules.audit.application.services.audit import AuditService
from serdial21.modules.banking.adapters.inbound.ofx import SafeOfxParser
from serdial21.modules.banking.adapters.outbound.persistence.repositories import SqlAlchemyBankingRepository
from serdial21.modules.banking.application.services.ofx_importer import OfxImportService
from serdial21.modules.operations.adapters.outbound.persistence.repositories import SqlAlchemyOperationalQueryRepository
from serdial21.modules.operations.application.services.operations import OperationalService


def create_operational_runtime(
    session: Session, settings: AppSettings,
) -> OperationalService:
    nfe_runtime = create_nfe55_runtime(session, settings)
    audit = AuditService(SqlAlchemyAuditRepository(session))
    return OperationalService(
        SqlAlchemyOperationalQueryRepository(session),
        AuthorizationService(SqlAlchemyAuthorizationRepository(session)),
        nfe_runtime.intake,
        create_nfe_to_dominio_runtime(session, settings),
        OfxImportService(
            nfe_runtime.intake,
            SafeOfxParser(max_ofx_bytes=settings.document_max_upload_bytes),
            SqlAlchemyBankingRepository(session), audit,
        ),
        audit,
    )
