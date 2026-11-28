from aether.contracts import (
    PublicationPayload,
    ScheduledEvent,
    ScheduledEventOutcome,
    ScheduledEventResolution,
)


class PublicExpressionResolver:
    def resolve_publication(
        self,
        event: ScheduledEvent,
    ) -> ScheduledEventResolution:
        if event.event_type != "public-publication":
            raise ValueError("Public expression resolver received another event type")
        payload = PublicationPayload.model_validate(event.payload)
        if payload.publication.world_id != event.world_id:
            raise ValueError("Publication belongs to another world")
        if payload.publication.published_at != event.scheduled_at:
            raise ValueError("Publication time must match its scheduled occurrence")
        for reception in payload.receptions:
            if reception.publication_id != payload.publication.publication_id:
                raise ValueError("Reception belongs to another publication")
            if reception.received_at < event.scheduled_at:
                raise ValueError("Reception cannot precede publication")
        return ScheduledEventResolution(
            scheduled_event_id=event.event_id,
            outcome=ScheduledEventOutcome.COMPLETED,
            payload={
                "publication_id": str(payload.publication.publication_id),
                "channel_id": str(payload.publication.channel_id),
                "reception_ids": [
                    str(reception.reception_id)
                    for reception in payload.receptions
                ],
                "resolution": "public-information-published",
            },
            publication=payload.publication,
            collective_receptions=payload.receptions,
            reason="Explicit public publication and aggregate reception recorded",
        )
