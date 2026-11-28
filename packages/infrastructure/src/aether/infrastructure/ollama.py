import json
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any

from aether.contracts import (
    InferenceProviderKind,
    InferenceRequest,
    InferenceResult,
)


class OllamaProviderError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class OllamaProvider:
    base_url: str = "http://127.0.0.1:11434"
    timeout_seconds: float = 120

    def generate(self, request: InferenceRequest) -> InferenceResult:
        options: dict[str, Any] = {"temperature": request.temperature}
        if request.max_output_tokens is not None:
            options["num_predict"] = request.max_output_tokens
        body: dict[str, Any] = {
            "model": request.model,
            "stream": False,
            "messages": [
                {"role": item.role, "content": item.content}
                for item in request.messages
            ],
            "options": options,
        }
        if request.response_schema is not None:
            body["format"] = request.response_schema
        started = time.monotonic()
        result = self._post("/api/chat", body)
        duration = time.monotonic() - started
        message = result.get("message")
        if not isinstance(message, dict) or not isinstance(
            message.get("content"), str
        ):
            raise OllamaProviderError("Ollama omitted message content")
        return InferenceResult(
            request_id=request.request_id,
            provider=InferenceProviderKind.OLLAMA,
            model=request.model,
            content=message["content"],
            prompt_tokens=result.get("prompt_eval_count"),
            output_tokens=result.get("eval_count"),
            duration_seconds=duration,
        )

    def list_models(self) -> tuple[str, ...]:
        result = self._get("/api/tags")
        models = result.get("models")
        if not isinstance(models, list):
            raise OllamaProviderError("Ollama omitted the model list")
        names: list[str] = []
        for model in models:
            if not isinstance(model, dict) or not isinstance(model.get("name"), str):
                raise OllamaProviderError("Ollama returned an invalid model entry")
            names.append(model["name"])
        return tuple(names)

    def health(self) -> bool:
        try:
            self._get("/api/tags")
        except OllamaProviderError:
            return False
        return True

    def _get(self, path: str) -> dict[str, Any]:
        return self._exchange(path, method="GET")

    def _post(self, path: str, body: dict[str, Any]) -> dict[str, Any]:
        return self._exchange(path, method="POST", body=body)

    def _exchange(
        self,
        path: str,
        *,
        method: str,
        body: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        data = json.dumps(body).encode("utf-8") if body is not None else None
        request = urllib.request.Request(
            f"{self.base_url.rstrip('/')}{path}",
            data=data,
            headers={"Content-Type": "application/json"},
            method=method,
        )
        try:
            with urllib.request.urlopen(
                request,
                timeout=self.timeout_seconds,
            ) as response:
                value = json.loads(response.read().decode("utf-8"))
        except (urllib.error.URLError, TimeoutError) as error:
            raise OllamaProviderError(
                f"Ollama service is unavailable at {self.base_url}"
            ) from error
        if not isinstance(value, dict):
            raise OllamaProviderError("Ollama returned a non-object response")
        return value
