from aether.contracts import (
    CreativeWork,
    GeneratedAsset,
    LeisureRoutine,
    PublicChannel,
    ScheduledEvent,
    SonicIdentity,
    VisualIdentity,
)
from aether.domain.ports import SimulationUnitOfWorkFactory


class ExpressionService:
    def __init__(self, unit_of_work_factory: SimulationUnitOfWorkFactory) -> None:
        self._unit_of_work_factory = unit_of_work_factory

    def register_public_channel(self, channel: PublicChannel) -> None:
        self._create("create_public_channel", channel)

    def register_creative_work(self, work: CreativeWork) -> None:
        self._create("create_creative_work", work)

    def register_leisure_routine(self, routine: LeisureRoutine) -> None:
        self._create("create_leisure_routine", routine)

    def register_visual_identity(self, identity: VisualIdentity) -> None:
        self._create("create_visual_identity", identity)

    def register_sonic_identity(self, identity: SonicIdentity) -> None:
        self._create("create_sonic_identity", identity)

    def register_generated_asset(self, asset: GeneratedAsset) -> None:
        self._create("create_generated_asset", asset)

    def schedule_publication(self, event: ScheduledEvent) -> None:
        if event.event_type != "public-publication":
            raise ValueError("Expression service only schedules public publications")
        with self._unit_of_work_factory() as unit_of_work:
            unit_of_work.repository.schedule_event(event)

    def _create(self, method: str, entity) -> None:
        with self._unit_of_work_factory() as unit_of_work:
            getattr(unit_of_work.repository, method)(entity)
