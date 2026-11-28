from pathlib import Path

from tools.model_benchmark import evaluate_output, load_scenarios


def test_benchmark_scenarios_are_loadable() -> None:
    scenarios = load_scenarios(
        Path("tools/model_benchmark_scenarios.json")
    )

    assert scenarios
    assert {scenario["id"] for scenario in scenarios} == {
        "gm-structured-wait",
        "npc-filtered-context",
        "narrator-confirmed-only",
        "canon-classification",
        "epistemic-separation",
    }


def test_evaluation_rejects_forbidden_hidden_fact() -> None:
    scenario = {
        "required_keys": [],
        "forbidden_terms": ["hidden pyre"],
    }

    result = evaluate_output(scenario, "The patrol destroyed the hidden pyre.")

    assert not result["valid"]
    assert result["forbidden_terms_found"] == ["hidden pyre"]


def test_evaluation_requires_json_contract_keys() -> None:
    scenario = {
        "required_keys": ["intent", "duration_seconds"],
        "forbidden_terms": [],
    }

    result = evaluate_output(scenario, '{"intent": "wait"}')

    assert not result["valid"]
    assert result["missing_keys"] == ["duration_seconds"]
