from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from aether.contracts import (
    ActionFlowResult,
    ActionProposal,
    ActionValidationResult,
    AdvanceTimeCommand,
    AgentProposalRecord,
    ConfirmedActionResult,
    GameMasterContext,
    GameMasterResult,
    LlmInvocationRecord,
    NarrativeContext,
    NarrativeDelivery,
    NarrativeDraft,
    NarrativeStateRecord,
    PlayerInput,
    PlayerKnowledgeRecord,
    PresentationRecord,
    PresentationStatus,
    SimulationRunRecord,
    SimulationRunStatus,
    TemporalAdvanceResult,
)
from aether.domain import (
    ActionValidationError,
    ActionValidationPort,
    GameMasterPort,
    NarratorPort,
    PresentationDeliveryError,
    PresentationDeliveryPort,
)
from aether.domain.ports import SimulationUnitOfWorkFactory

from .temporal import TemporalAdvanceService


class ActionExecutionService:
    def __init__(
        self,
        unit_of_work_factory: SimulationUnitOfWorkFactory,
        temporal_service: TemporalAdvanceService,
        game_master: GameMasterPort,
        validator: ActionValidationPort,
        narrator: NarratorPort,
        delivery: PresentationDeliveryPort,
    ) -> None:
        self._unit_of_work_factory = unit_of_work_factory
        self._temporal_service = temporal_service
        self._game_master = game_master
        self._validator = validator
        self._narrator = narrator
        self._delivery = delivery

    def execute(self, player_input: PlayerInput) -> ActionFlowResult:
        existing = self._load_existing(player_input.simulation_run_id)
        if existing is not None:
            return self._resume_existing(player_input, *existing)

        run, proposal, validation = self._prepare(player_input)
        temporal_result = self._temporal_service.advance_time(
            self._command_from(player_input, proposal, validation)
        )
        return self._present(player_input, run, temporal_result, proposal, validation)

    def _prepare(
        self,
        player_input: PlayerInput,
    ) -> tuple[SimulationRunRecord, ActionProposal, ActionValidationResult]:
        with self._unit_of_work_factory() as unit_of_work:
            clock = unit_of_work.repository.get_clock(
                player_input.world_id,
                player_input.timeline_id,
            )
            if clock is None:
                raise ActionValidationError("World clock was not found")
            current_world_time = clock.current_time

        interpreted = self._game_master.interpret(
            GameMasterContext(
                player_input=player_input,
                current_world_time=current_world_time,
            )
        )
        validation = self._validator.validate(player_input, interpreted.proposal)
        if not validation.accepted:
            raise ActionValidationError(
                validation.rejection_reason or "Action proposal was rejected"
            )

        command = self._command_from(player_input, interpreted.proposal, validation)
        run = self._temporal_service.prepare_time(command)
        invocation = self._invocation_record(player_input, interpreted)
        proposal = AgentProposalRecord(
            proposal_id=interpreted.proposal.proposal_id,
            simulation_run_id=player_input.simulation_run_id,
            invocation_id=interpreted.invocation_id,
            proposal_type="action",
            payload=interpreted.proposal.model_dump(mode="json"),
            validation_status="validated",
            application_result={
                "confirmed_facts": list(validation.confirmed_facts),
                "protagonist_character_id": str(
                    player_input.protagonist_character_id
                ),
                "player_id": player_input.player_id,
            },
            created_at=interpreted.completed_at,
        )
        with self._unit_of_work_factory() as unit_of_work:
            unit_of_work.repository.create_invocation(invocation)
            unit_of_work.repository.create_proposal(proposal)
            unit_of_work.commit()
        return run, interpreted.proposal, validation

    def _resume_existing(
        self,
        player_input: PlayerInput,
        run: SimulationRunRecord,
        presentation: PresentationRecord | None,
    ) -> ActionFlowResult:
        if presentation is not None:
            if presentation.status == PresentationStatus.CONFIRMED:
                return ActionFlowResult(
                    simulation_run_id=run.simulation_run_id,
                    presentation_id=presentation.presentation_id,
                    content=presentation.delivered_content or "",
                    idempotent_replay=True,
                )
            return self._confirm_generated(player_input, presentation)

        proposal, validation = self._load_action_proposal(
            run.simulation_run_id,
            player_input,
        )
        command = self._command_from(player_input, proposal, validation)
        if run.status in {
            SimulationRunStatus.PREPARED,
            SimulationRunStatus.COMPLETED,
        }:
            temporal_result = (
                self._temporal_service.result_for_completed_run(run)
                if run.status == SimulationRunStatus.COMPLETED
                else self._temporal_service.advance_time(command)
            )
            return self._present(
                player_input,
                run,
                temporal_result,
                proposal,
                validation,
            )
        raise ActionValidationError(
            f"Simulation run cannot be resumed from status {run.status.value}"
        )

    def _present(
        self,
        player_input: PlayerInput,
        run: SimulationRunRecord,
        temporal_result: TemporalAdvanceResult,
        proposal: ActionProposal,
        validation: ActionValidationResult,
    ) -> ActionFlowResult:
        confirmed_facts = validation.confirmed_facts + (
            f"world-time:{temporal_result.final_time.isoformat()}",
        )
        with self._unit_of_work_factory() as unit_of_work:
            knowledge_entries = unit_of_work.repository.list_character_knowledge(
                player_input.protagonist_character_id,
                as_of=temporal_result.final_time,
            )
        character_knowledge = tuple(
            (
                f"{entry.fact_key}:{entry.statement}"
                f"[{entry.epistemic_status.value};confidence={entry.confidence:.2f}]"
            )
            for entry in knowledge_entries
        )
        context = NarrativeContext(
            confirmed_action=ConfirmedActionResult(
                simulation_run_id=run.simulation_run_id,
                protagonist_character_id=player_input.protagonist_character_id,
                intent=proposal.intent,
                initial_time=temporal_result.initial_time.isoformat(),
                final_time=temporal_result.final_time.isoformat(),
                confirmed_facts=confirmed_facts,
            ),
            confirmed_facts=confirmed_facts,
            character_knowledge=character_knowledge,
        )
        draft = self._narrator.narrate(context)
        if not set(draft.claims_supported_by_facts).issubset(confirmed_facts):
            raise ActionValidationError(
                "Narrative draft contains a claim without a confirmed fact"
            )
        generated = PresentationRecord(
            presentation_id=draft.presentation_id,
            simulation_run_id=run.simulation_run_id,
            protagonist_character_id=player_input.protagonist_character_id,
            narrative_time=temporal_result.final_time,
            status=PresentationStatus.GENERATED,
            generated_content=draft.content,
            confirmed_fact_ids=draft.claims_supported_by_facts,
            created_at=datetime.now(UTC),
        )
        with self._unit_of_work_factory() as unit_of_work:
            unit_of_work.repository.create_presentation(generated)
            unit_of_work.commit()
        return self._confirm_generated(player_input, generated)

    def _confirm_generated(
        self,
        player_input: PlayerInput,
        generated: PresentationRecord,
    ) -> ActionFlowResult:
        delivery = self._delivery.deliver(
            NarrativeDraft(
                presentation_id=generated.presentation_id,
                simulation_run_id=generated.simulation_run_id,
                content=generated.generated_content,
                claims_supported_by_facts=generated.confirmed_fact_ids,
            )
        )
        self._validate_delivery(delivery, generated.confirmed_fact_ids)
        now = datetime.now(UTC)
        confirmed = generated.model_copy(
            update={
                "status": PresentationStatus.CONFIRMED,
                "delivered_content": delivery.delivered_content,
                "confirmed_fact_ids": delivery.delivered_claim_ids,
                "delivered_at": now,
            }
        )
        with self._unit_of_work_factory() as unit_of_work:
            unit_of_work.repository.save_presentation(confirmed)
            for fact in delivery.delivered_claim_ids:
                unit_of_work.repository.create_player_knowledge(
                    PlayerKnowledgeRecord(
                        knowledge_id=uuid4(),
                        simulation_run_id=generated.simulation_run_id,
                        player_id=player_input.player_id,
                        fact_key=fact,
                        description=fact,
                        source_presentation_id=generated.presentation_id,
                        acquired_at=now,
                    )
                )
            unit_of_work.repository.create_narrative_state(
                NarrativeStateRecord(
                    state_id=uuid4(),
                    simulation_run_id=generated.simulation_run_id,
                    protagonist_character_id=generated.protagonist_character_id,
                    scene_summary=delivery.delivered_content,
                    narrative_time=generated.narrative_time,
                    created_at=now,
                )
            )
            unit_of_work.commit()
        return ActionFlowResult(
            simulation_run_id=generated.simulation_run_id,
            presentation_id=generated.presentation_id,
            content=delivery.delivered_content,
        )

    def _load_existing(
        self,
        simulation_run_id: UUID,
    ) -> tuple[SimulationRunRecord, PresentationRecord | None] | None:
        with self._unit_of_work_factory() as unit_of_work:
            run = unit_of_work.repository.get_run(simulation_run_id)
            if run is None:
                return None
            presentation = unit_of_work.repository.get_presentation_by_run(
                simulation_run_id
            )
            return run, presentation

    def _load_action_proposal(
        self,
        simulation_run_id: UUID,
        player_input: PlayerInput,
    ) -> tuple[ActionProposal, ActionValidationResult]:
        with self._unit_of_work_factory() as unit_of_work:
            records = unit_of_work.repository.get_proposals_by_run(simulation_run_id)
        if len(records) != 1:
            raise ActionValidationError(
                "Recovering an action requires exactly one persisted proposal"
            )
        record = records[0]
        result = record.application_result or {}
        if (
            result.get("protagonist_character_id")
            != str(player_input.protagonist_character_id)
            or result.get("player_id") != player_input.player_id
        ):
            raise ActionValidationError(
                "Simulation run ID is associated with a different player or protagonist"
            )
        return ActionProposal.model_validate(record.payload), ActionValidationResult(
            accepted=True,
            duration_seconds=int(record.payload["duration_seconds"]),
            confirmed_facts=tuple(result.get("confirmed_facts", ())),
        )

    @staticmethod
    def _command_from(
        player_input: PlayerInput,
        proposal: ActionProposal,
        validation: ActionValidationResult,
    ) -> AdvanceTimeCommand:
        return AdvanceTimeCommand(
            simulation_run_id=player_input.simulation_run_id,
            world_id=player_input.world_id,
            timeline_id=player_input.timeline_id,
            duration=timedelta(seconds=validation.duration_seconds),
        )

    @staticmethod
    def _invocation_record(
        player_input: PlayerInput,
        interpreted: GameMasterResult,
    ) -> LlmInvocationRecord:
        return LlmInvocationRecord(
            invocation_id=interpreted.invocation_id,
            simulation_run_id=player_input.simulation_run_id,
            requesting_agent=interpreted.requesting_agent,
            requested_capability=interpreted.requested_capability,
            model=interpreted.model,
            model_version=interpreted.model_version,
            prompt_version=interpreted.prompt_version,
            context_hash=interpreted.context_hash,
            inference_parameters=interpreted.inference_parameters,
            response_reference=interpreted.raw_response_reference,
            status="completed",
            created_at=interpreted.created_at,
            completed_at=interpreted.completed_at,
        )

    @staticmethod
    def _validate_delivery(
        delivery: NarrativeDelivery,
        generated_claims: tuple[str, ...],
    ) -> None:
        if not set(delivery.delivered_claim_ids).issubset(generated_claims):
            raise PresentationDeliveryError(
                "Delivery confirmed a claim that was not generated"
            )
