'''Persistência SQLAlchemy do intake documental.'''

from serdial21.modules.intake_documents.adapters.outbound.persistence.repositories import (
    SqlAlchemyIntakeRepository,
)

__all__ = ['SqlAlchemyIntakeRepository']

