from __future__ import annotations

import argparse
import json
import platform
import statistics
import subprocess
import threading
import time
import urllib.error
import urllib.request
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


def load_scenarios(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as handle:
        document = json.load(handle)
    scenarios = document.get("scenarios")
    if not isinstance(scenarios, list) or not scenarios:
        raise ValueError("Scenario file must contain a non-empty scenarios list")
    required = {"id", "capability", "system", "user", "required_keys", "forbidden_terms"}
    for scenario in scenarios:
        if not isinstance(scenario, dict) or not required.issubset(scenario):
            raise ValueError(f"Scenario is missing required fields: {scenario!r}")
    return scenarios


def request_ollama(
    base_url: str,
    model: str,
    scenario: dict[str, Any],
    timeout: float,
) -> tuple[str, dict[str, Any]]:
    body = {
        "model": model,
        "stream": False,
        "messages": [
            {"role": "system", "content": scenario["system"]},
            {"role": "user", "content": scenario["user"]},
        ],
    }
    if scenario["required_keys"]:
        body["format"] = "json"
    result = post_json(f"{base_url}/api/chat", body, timeout)
    message = result.get("message")
    if not isinstance(message, dict) or not isinstance(message.get("content"), str):
        raise ValueError("Ollama response omitted message.content")
    return message["content"], result


def request_openai(
    base_url: str,
    model: str,
    scenario: dict[str, Any],
    timeout: float,
) -> tuple[str, dict[str, Any]]:
    body = {
        "model": model,
        "messages": [
            {"role": "system", "content": scenario["system"]},
            {"role": "user", "content": scenario["user"]},
        ],
        "temperature": 0,
    }
    result = post_json(f"{base_url}/v1/chat/completions", body, timeout)
    choices = result.get("choices")
    if not isinstance(choices, list) or not choices:
        raise ValueError("OpenAI-compatible response omitted choices")
    content = choices[0].get("message", {}).get("content")
    if not isinstance(content, str):
        raise ValueError("OpenAI-compatible response omitted message content")
    return content, result


def post_json(url: str, body: dict[str, Any], timeout: float) -> dict[str, Any]:
    request = urllib.request.Request(
        url,
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            result = json.loads(response.read().decode("utf-8"))
    except urllib.error.URLError as error:
        raise RuntimeError(f"Benchmark endpoint is unavailable: {url}") from error
    if not isinstance(result, dict):
        raise ValueError("Benchmark endpoint returned a non-object response")
    return result


def evaluate_output(
    scenario: dict[str, Any],
    content: str,
) -> dict[str, Any]:
    required_keys = tuple(scenario["required_keys"])
    forbidden_terms = tuple(term.casefold() for term in scenario["forbidden_terms"])
    lower_content = content.casefold()
    leaked_terms = [term for term in forbidden_terms if term in lower_content]
    parsed: Any | None = None
    parse_error: str | None = None
    if required_keys:
        try:
            parsed = json.loads(content)
        except json.JSONDecodeError as error:
            parse_error = str(error)
    missing_keys: list[str] = []
    if isinstance(parsed, dict):
        missing_keys = [key for key in required_keys if key not in parsed]
        if scenario["id"] == "gm-structured-wait":
            if parsed.get("action_kind") not in {
                "instantaneous",
                "interval",
                "interruptible",
                "scheduled",
            }:
                missing_keys.append("valid_action_kind")
        if scenario["id"] == "epistemic-separation":
            if parsed.get("world_truth_disclosed") is not False:
                missing_keys.append("world_truth_disclosed_false")
    elif required_keys:
        missing_keys = list(required_keys)
    return {
        "valid": (
            not leaked_terms
            and parse_error is None
            and not missing_keys
        ),
        "parse_error": parse_error,
        "missing_keys": missing_keys,
        "forbidden_terms_found": leaked_terms,
    }


def sample_vram(stop: threading.Event, samples: list[int]) -> None:
    while not stop.is_set():
        completed = subprocess.run(
            [
                "nvidia-smi",
                "--query-gpu=memory.used",
                "--format=csv,noheader,nounits",
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        if completed.returncode == 0:
            values = [
                int(value.strip())
                for value in completed.stdout.splitlines()
                if value.strip().isdigit()
            ]
            if values:
                samples.append(sum(values))
        stop.wait(0.25)


def run(args: argparse.Namespace) -> dict[str, Any]:
    scenarios = load_scenarios(args.scenarios)
    requester = request_ollama if args.runtime == "ollama" else request_openai
    runs: list[dict[str, Any]] = []
    for repetition in range(args.repetitions):
        for scenario in scenarios:
            samples: list[int] = []
            stop = threading.Event()
            sampler = threading.Thread(
                target=sample_vram,
                args=(stop, samples),
                daemon=True,
            )
            sampler.start()
            started_ns = time.monotonic_ns()
            error: str | None = None
            content = ""
            raw: dict[str, Any] = {}
            try:
                content, raw = requester(
                    args.base_url,
                    args.model,
                    scenario,
                    args.timeout,
                )
            except (RuntimeError, ValueError, TimeoutError) as exception:
                error = f"{type(exception).__name__}: {exception}"
            duration = (time.monotonic_ns() - started_ns) / 1_000_000_000
            stop.set()
            sampler.join(timeout=1)
            evaluation = evaluate_output(scenario, content) if error is None else {
                "valid": False,
                "parse_error": None,
                "missing_keys": [],
                "forbidden_terms_found": [],
            }
            runs.append(
                {
                    "scenario_id": scenario["id"],
                    "capability": scenario["capability"],
                    "repetition": repetition + 1,
                    "duration_seconds": duration,
                    "vram_used_mib_peak": max(samples, default=None),
                    "vram_used_mib_median": (
                        statistics.median(samples) if samples else None
                    ),
                    "evaluation": evaluation,
                    "error": error,
                    "output": content,
                    "runtime_metrics": raw,
                }
            )
    valid_count = sum(run["evaluation"]["valid"] for run in runs)
    return {
        "schema_version": "1",
        "recorded_at": datetime.now(UTC).isoformat(),
        "platform": {
            "system": platform.system(),
            "release": platform.release(),
            "machine": platform.machine(),
            "python_version": platform.python_version(),
        },
        "runtime": args.runtime,
        "base_url": args.base_url,
        "model": args.model,
        "repetitions": args.repetitions,
        "summary": {
            "runs": len(runs),
            "valid_runs": valid_count,
            "validity_rate": valid_count / len(runs),
        },
        "runs": runs,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run Aether's local model capability benchmark."
    )
    parser.add_argument("--runtime", choices=("ollama", "openai"), required=True)
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument(
        "--scenarios",
        type=Path,
        default=Path("tools/model_benchmark_scenarios.json"),
    )
    parser.add_argument("--repetitions", type=int, default=5)
    parser.add_argument("--timeout", type=float, default=120)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.repetitions <= 0:
        parser.error("--repetitions must be positive")
    if args.timeout <= 0:
        parser.error("--timeout must be positive")
    return args


def main() -> None:
    args = parse_args()
    result = run(args)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, indent=2, ensure_ascii=True),
        encoding="utf-8",
    )
    print(
        f"Benchmark complete: {result['summary']['valid_runs']}/"
        f"{result['summary']['runs']} valid runs; output={args.output}"
    )


if __name__ == "__main__":
    main()
