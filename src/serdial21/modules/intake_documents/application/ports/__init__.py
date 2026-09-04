'''Portas do intake documental.'''

from serdial21.modules.intake_documents.application.ports.object_storage import (
    ObjectStorage,
    StoredObject,
)
from serdial21.modules.intake_documents.application.ports.repository import (
    IntakeRepository,
)

__all__ = ['IntakeRepository', 'ObjectStorage', 'StoredObject']
