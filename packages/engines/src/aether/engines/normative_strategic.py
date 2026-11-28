from uuid import UUID, uuid4

from aether.contracts import (
    CaseStatus,
    CharacterKnowledgeRecord,
    IntelligenceOperation,
    Investigation,
    InvestigationCompletionPayload,
    InvestigationStatus,
    LegalCase,
    LegalProceeding,
    LegalProceedingTransitionPayload,
    NormativeSystem,
    ScheduledEvent,
    ScheduledEventOutcome,
    ScheduledEventResolution,
    SecurityIncident,
    SecurityResolution,
    SecurityResolutionPayload,
    SecurityThreat,
    StrategicConflict,
    StrategicEscalationPayload,
    Treaty,
    TreatyChangePayload,
)


class NormativeStrategicResolver:
    """Purely applies explicitly authored institutional transitions."""

    def resolve_legal_proceeding(
        self,
        event: ScheduledEvent,
        system: NormativeSystem,
        case: LegalCase,
        proceeding: LegalProceeding,
    ) -> ScheduledEventResolution:
        payload = LegalProceedingTransitionPayload.model_validate(event.payload)
        self._require_event_type(event, "legal-proceeding-transition")
        self._require_world(event, system.world_id, case.world_id)
        self._require_system_authority(system, payload.authority)
        if case.system_id != system.system_id or payload.case_id != case.case_id:
            raise ValueError("Legal transition targets another system or case")
        if payload.proceeding_id != proceeding.proceeding_id or proceeding.case_id != case.case_id:
            raise ValueError("Legal transition targets another proceeding")
        self._require_jurisdiction(system, payload.authority.location_id)
        if case.location_id != payload.authority.location_id:
            raise PermissionError("Legal authority is outside the case jurisdiction")
        for sanction in payload.sanctions:
            if sanction.case_id != case.case_id or sanction.proceeding_id != proceeding.proceeding_id:
                raise ValueError("Sanction belongs to another case or proceeding")
            if sanction.authority_organization_id != payload.authority.organization_id:
                raise PermissionError("Sanction names a different enforcing authority")
        updated_proceeding = proceeding.model_copy(
            update={
                "status": payload.target_status,
                "decision_summary": payload.decision_summary,
                "sanction_ids": tuple(s.sanction_id for s in payload.sanctions)
                or proceeding.sanction_ids,
                "provenance": self._advance(proceeding.provenance, event),
            }
        )
        updated_case = case.model_copy(
            update={
                "status": payload.case_status,
                "closed_at": (
                    event.scheduled_at
                    if payload.case_status == CaseStatus.CLOSED
                    else case.closed_at
                ),
                "provenance": self._advance(case.provenance, event),
            }
        )
        return ScheduledEventResolution(
            scheduled_event_id=event.event_id,
            outcome=ScheduledEventOutcome.COMPLETED,
            payload={
                "case_id": str(case.case_id),
                "proceeding_id": str(proceeding.proceeding_id),
                "case_status": payload.case_status.value,
                "proceeding_status": payload.target_status.value,
                "sanction_ids": [str(item.sanction_id) for item in payload.sanctions],
                "resolution": "legal-proceeding-transitioned",
            },
            legal_case=updated_case,
            legal_proceeding=updated_proceeding,
            sanctions=payload.sanctions,
            character_knowledge=self._knowledge(payload.knowledge_disclosures, event),
            reason="Explicit legal proceeding transition completed",
        )

    def resolve_investigation(
        self,
        event: ScheduledEvent,
        system: NormativeSystem,
        case: LegalCase,
        investigation: Investigation,
    ) -> ScheduledEventResolution:
        payload = InvestigationCompletionPayload.model_validate(event.payload)
        self._require_event_type(event, "investigation-completion")
        self._require_world(event, system.world_id, case.world_id)
        self._require_system_authority(system, payload.authority)
        if investigation.investigation_id != payload.investigation_id:
            raise ValueError("Investigation completion targets another investigation")
        if investigation.case_id != case.case_id or case.system_id != system.system_id:
            raise ValueError("Investigation does not belong to the case and system")
        if investigation.responsible_organization_id != payload.authority.organization_id:
            raise PermissionError("Investigation authority is not its responsible organization")
        self._require_jurisdiction(system, payload.authority.location_id)
        if case.location_id != payload.authority.location_id:
            raise PermissionError("Investigator is outside the case jurisdiction")
        for evidence in payload.evidence:
            if (
                evidence.investigation_id != investigation.investigation_id
                or evidence.case_id != case.case_id
            ):
                raise ValueError("Evidence belongs to another investigation or case")
            if evidence.acquired_at > event.scheduled_at:
                raise ValueError("Evidence cannot be acquired after investigation completion")
        updated = investigation.model_copy(
            update={
                "status": InvestigationStatus.COMPLETED,
                "evidence_ids": tuple(item.evidence_id for item in payload.evidence),
                "findings_summary": payload.findings_summary,
                "completed_at": event.scheduled_at,
                "provenance": self._advance(investigation.provenance, event),
            }
        )
        return ScheduledEventResolution(
            scheduled_event_id=event.event_id,
            outcome=ScheduledEventOutcome.COMPLETED,
            payload={
                "case_id": str(case.case_id),
                "investigation_id": str(investigation.investigation_id),
                "evidence_ids": [str(item.evidence_id) for item in payload.evidence],
                "resolution": "investigation-completed",
            },
            investigation=updated,
            evidence_records=payload.evidence,
            character_knowledge=self._knowledge(payload.knowledge_disclosures, event),
            reason="Explicit investigation completion recorded",
        )

    def resolve_treaty(
        self,
        event: ScheduledEvent,
        treaty: Treaty,
    ) -> ScheduledEventResolution:
        payload = TreatyChangePayload.model_validate(event.payload)
        self._require_event_type(event, "treaty-change")
        self._require_world(event, treaty.world_id)
        if payload.treaty_id != treaty.treaty_id:
            raise ValueError("Treaty event targets another treaty")
        if payload.authority.organization_id not in treaty.party_organization_ids:
            raise PermissionError("Treaty authority is not a treaty party")
        updated = treaty.model_copy(
            update={
                "status": payload.target_status,
                "provenance": self._advance(treaty.provenance, event),
            }
        )
        return ScheduledEventResolution(
            scheduled_event_id=event.event_id,
            outcome=ScheduledEventOutcome.COMPLETED,
            payload={
                "treaty_id": str(treaty.treaty_id),
                "status": payload.target_status.value,
                "resolution": "treaty-changed",
            },
            treaty=updated,
            reason="Explicit treaty state change completed",
        )

    def resolve_strategic_escalation(
        self,
        event: ScheduledEvent,
        conflict: StrategicConflict,
    ) -> ScheduledEventResolution:
        payload = StrategicEscalationPayload.model_validate(event.payload)
        self._require_event_type(event, "strategic-escalation")
        self._require_world(event, conflict.world_id)
        if payload.conflict_id != conflict.conflict_id:
            raise ValueError("Strategic event targets another conflict")
        if payload.authority.organization_id not in conflict.party_organization_ids:
            raise PermissionError("Strategic authority is not a conflict party")
        if not payload.target_stage.strip():
            raise ValueError("Strategic target stage cannot be blank")
        if any(factor.category.strip() == "" or factor.value.strip() == "" for factor in payload.added_factors):
            raise ValueError("Strategic factors require semantic category and value")
        updated = conflict.model_copy(
            update={
                "escalation_stage": payload.target_stage,
                "stage_metadata": payload.stage_metadata,
                "factors": conflict.factors + payload.added_factors,
                "provenance": self._advance(conflict.provenance, event),
            }
        )
        return ScheduledEventResolution(
            scheduled_event_id=event.event_id,
            outcome=ScheduledEventOutcome.COMPLETED,
            payload={
                "conflict_id": str(conflict.conflict_id),
                "escalation_stage": payload.target_stage,
                "stage_metadata": payload.stage_metadata,
                "resolution": "strategic-stage-recorded",
            },
            strategic_conflict=updated,
            reason="Explicit non-linear strategic state recorded",
        )

    def resolve_security(
        self,
        event: ScheduledEvent,
        threat: SecurityThreat,
        operation: IntelligenceOperation | None,
        incident: SecurityIncident | None,
    ) -> ScheduledEventResolution:
        payload = SecurityResolutionPayload.model_validate(event.payload)
        self._require_event_type(event, "security-resolution")
        self._require_world(event, threat.world_id)
        if payload.threat_id != threat.threat_id:
            raise ValueError("Security resolution targets another threat")
        if payload.operation_id is None and operation is not None:
            raise ValueError("Security resolver received an unexpected operation")
        if operation is not None and (
            payload.operation_id != operation.operation_id
            or operation.world_id != threat.world_id
            or threat.threat_id not in operation.threat_ids
            or operation.organization_id != payload.authority.organization_id
            or operation.location_id != payload.authority.location_id
        ):
            raise PermissionError("Security authority does not own the intelligence operation")
        if (
            threat.location_ids
            and payload.authority.location_id not in threat.location_ids
        ):
            raise PermissionError("Security authority is outside the threat area")
        if incident is not None and (
            payload.incident_id != incident.incident_id
            or incident.threat_id != threat.threat_id
        ):
            raise ValueError("Security incident does not match its threat")
        if payload.incident_id is not None and incident is None:
            raise ValueError("Security resolution references an unknown incident")
        if payload.resulting_operation_status is None and operation is not None:
            raise ValueError("Intelligence operation resolution requires a resulting status")
        updated_threat = threat.model_copy(
            update={
                "status": payload.resulting_threat_status,
                "provenance": self._advance(threat.provenance, event),
            }
        )
        updated_operation = (
            operation.model_copy(
                update={
                    "status": payload.resulting_operation_status,
                    "provenance": self._advance(operation.provenance, event),
                }
            )
            if operation is not None
            else None
        )
        resolution = SecurityResolution(
            resolution_id=uuid4(),
            operation_id=payload.operation_id,
            threat_id=payload.threat_id,
            outcome=payload.outcome,
            status="resolved",
            summary=payload.summary,
            resolved_at=event.scheduled_at,
            source_event_id=event.event_id,
            provenance=self._advance(threat.provenance, event),
        )
        return ScheduledEventResolution(
            scheduled_event_id=event.event_id,
            outcome=ScheduledEventOutcome.COMPLETED,
            payload={
                "threat_id": str(threat.threat_id),
                "operation_id": str(operation.operation_id) if operation else None,
                "outcome": payload.outcome.value,
                "resolution_id": str(resolution.resolution_id),
                "resolution": "security-resolved",
            },
            security_threat=updated_threat,
            intelligence_operation=updated_operation,
            security_resolutions=(resolution,),
            character_knowledge=self._knowledge(payload.knowledge_disclosures, event),
            reason="Explicit security outcome recorded",
        )

    @staticmethod
    def _knowledge(disclosures, event: ScheduledEvent) -> tuple[CharacterKnowledgeRecord, ...]:
        return tuple(
            CharacterKnowledgeRecord(
                knowledge_id=uuid4(),
                character_id=item.character_id,
                fact_key=item.fact_key,
                statement=item.statement,
                source_event_id=event.event_id,
                acquisition_event_id=event.event_id,
                acquired_at=event.scheduled_at,
                confidence=item.confidence,
                epistemic_status=item.epistemic_status,
                temporal_scope=None,
            )
            for item in disclosures
        )

    @staticmethod
    def _require_event_type(event: ScheduledEvent, expected: str) -> None:
        if event.event_type != expected:
            raise ValueError(f"{expected} resolver received another event type")

    @staticmethod
    def _require_world(event: ScheduledEvent, *world_ids: UUID) -> None:
        if any(world_id != event.world_id for world_id in world_ids):
            raise ValueError("Normative or strategic record belongs to another world")

    @staticmethod
    def _require_jurisdiction(system: NormativeSystem, location_id: UUID) -> None:
        if (
            system.jurisdiction.location_ids
            and location_id not in system.jurisdiction.location_ids
        ):
            raise PermissionError("Actor location is outside normative jurisdiction")

    @staticmethod
    def _advance(provenance, event: ScheduledEvent):
        return provenance.model_copy(
            update={
                "origin_event_id": event.event_id,
                "updated_at": event.scheduled_at,
                "version": provenance.version + 1,
            }
        )

    @staticmethod
    def _require_system_authority(system, authority) -> None:
        if not any(
            grant.organization_id == authority.organization_id
            and grant.permission_code == authority.permission_code
            for grant in system.authorities
        ):
            raise PermissionError("Normative system does not confer this authority")
