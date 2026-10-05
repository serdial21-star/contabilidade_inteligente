from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from threading import Barrier
from uuid import UUID, uuid4

from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session, sessionmaker

from serdial21.bootstrap.model_registry import load_models
from serdial21.modules.workflow.adapters.outbound.persistence.journeys import (
    JourneyDocumentReservationModel, SqlAlchemyJourneyRepository,
)
from serdial21.modules.workflow.application.journey import JourneyConflictError


def test_concurrent_document_claims_leave_one_active_reservation(tmp_path) -> None:
    load_models()
    engine = create_engine(
        f"sqlite+pysqlite:///{(tmp_path / 'reservation-race.db').as_posix()}",
        connect_args={'check_same_thread': False, 'timeout': 10},
    )
    JourneyDocumentReservationModel.__table__.create(engine)
    factory = sessionmaker(engine, expire_on_commit=False)
    tenant_id, company_id, document_id, actor_id = uuid4(), uuid4(), uuid4(), uuid4()
    journeys = (uuid4(), uuid4())
    barrier = Barrier(2)

    def claim(journey_id: UUID) -> UUID | str | None:
        with factory() as session:
            repository = SqlAlchemyJourneyRepository(session)
            barrier.wait()
            try:
                owner = repository.reserve_document(
                    tenant_id, company_id, document_id, journey_id,
                    created_by=actor_id, created_at=datetime.now(UTC),
                )
                session.commit()
                return owner
            except JourneyConflictError:
                session.rollback()
                return 'conflict'

    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = tuple(pool.map(claim, journeys))

    with Session(engine) as session:
        active = session.scalar(select(func.count()).select_from(
            JourneyDocumentReservationModel,
        ).where(JourneyDocumentReservationModel.active_marker == 'ACTIVE'))
        owner = session.scalar(select(JourneyDocumentReservationModel.journey_id).where(
            JourneyDocumentReservationModel.active_marker == 'ACTIVE',
        ))
    assert active == 1
    assert owner in journeys
    assert outcomes.count(None) == 1
    assert outcomes[0] in {None, owner, 'conflict'}
    assert outcomes[1] in {None, owner, 'conflict'}
    engine.dispose()
