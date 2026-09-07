'''Composição interna do importador de NF-e modelo 55.'''

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy.orm import Session

from serdial21.bootstrap.settings import AppSettings
from serdial21.modules.access_control.adapters.outbound.persistence.repositories import (
    SqlAlchemyAuthorizationRepository,
)
from serdial21.modules.access_control.application.services.authorization import (
    AuthorizationService,
)
from serdial21.modules.audit.adapters.outbound.persistence.repositories import (
    SqlAlchemyAuditRepository,
)
from serdial21.modules.audit.application.services.audit import AuditService
from serdial21.modules.fiscal_documents.adapters.inbound.nfe55_xml import (
    SafeNFe55XmlParser,
)
from serdial21.modules.fiscal_documents.adapters.outbound.persistence.repositories import (
    SqlAlchemyFiscalDocumentRepository,
)
from serdial21.modules.fiscal_documents.application.services.nfe55_importer import (
    NFe55ImportService,
)
from serdial21.modules.intake_documents.adapters.outbound.persistence.repositories import (
    SqlAlchemyIntakeRepository,
)
from serdial21.modules.intake_documents.adapters.outbound.storage.local import (
    LocalObjectStorage,
)
from serdial21.modules.intake_documents.application.services.authorization import (
    AccessControlDocumentAuthorization,
)
from serdial21.modules.intake_documents.application.services.intake import (
    DocumentIntakeService,
)


@dataclass(frozen=True, slots=True)
class NFe55Runtime:
    intake: DocumentIntakeService
    importer: NFe55ImportService


def create_nfe55_runtime(
    session: Session,
    settings: AppSettings,
    *,
    clock: Callable[[], datetime] | None = None,
) -> NFe55Runtime:
    '''Liga Settings, autorização, storage, auditoria e persistência na mesma UoW.'''

    audit = AuditService(
        SqlAlchemyAuditRepository(session),
        clock=clock,
    )
    authorization = AccessControlDocumentAuthorization(
        AuthorizationService(SqlAlchemyAuthorizationRepository(session))
    )
    intake = DocumentIntakeService(
        SqlAlchemyIntakeRepository(session),
        LocalObjectStorage(settings.object_storage_path),
        audit,
        authorization,
        max_upload_bytes=settings.document_max_upload_bytes,
        clock=clock,
    )
    importer = NFe55ImportService(
        intake,
        SafeNFe55XmlParser(
            max_xml_bytes=settings.nfe_max_xml_bytes,
            max_xml_elements=settings.nfe_max_xml_elements,
        ),
        SqlAlchemyFiscalDocumentRepository(session),
        audit,
        clock=clock,
    )
    return NFe55Runtime(intake=intake, importer=importer)
