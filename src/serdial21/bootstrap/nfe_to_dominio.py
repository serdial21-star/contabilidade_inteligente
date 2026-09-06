"""Composição interna: catálogo confiável obrigatório, Domínio real fail-closed."""
from collections.abc import Callable
from datetime import datetime

from sqlalchemy.orm import Session

from serdial21.bootstrap.nfe55 import create_nfe55_runtime
from serdial21.bootstrap.settings import AppSettings
from serdial21.modules.access_control.adapters.outbound.persistence.repositories import SqlAlchemyAuthorizationRepository
from serdial21.modules.access_control.application.services.authorization import AuthorizationService
from serdial21.modules.audit.adapters.outbound.persistence.repositories import SqlAlchemyAuditRepository
from serdial21.modules.audit.application.services.audit import AuditService
from serdial21.modules.fiscal_documents.adapters.outbound.persistence.repositories import SqlAlchemyFiscalDocumentRepository
from serdial21.modules.integrations.adapters.outbound.dominio import DominioConnector
from serdial21.modules.workflow.adapters.outbound.persistence.journeys import SqlAlchemyJourneyRepository
from serdial21.modules.workflow.application.journey import JourneyCatalog
from serdial21.modules.workflow.application.services.nfe_to_dominio import NFeToDominioService


def create_nfe_to_dominio_runtime(
    session: Session, settings: AppSettings, catalog: JourneyCatalog,
    *, clock: Callable[[], datetime] | None = None,
) -> NFeToDominioService:
    nfe = create_nfe55_runtime(session, settings, clock=clock)
    return NFeToDominioService(
        SqlAlchemyJourneyRepository(session), catalog,
        AuthorizationService(SqlAlchemyAuthorizationRepository(session)),
        nfe.intake, nfe.importer, SqlAlchemyFiscalDocumentRepository(session),
        AuditService(SqlAlchemyAuditRepository(session), clock=clock),
        DominioConnector(), clock=clock,
    )

