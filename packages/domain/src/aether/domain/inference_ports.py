from typing import Protocol

from aether.contracts import InferenceRequest, InferenceResult


class InferenceProviderPort(Protocol):
    def generate(self, request: InferenceRequest) -> InferenceResult: ...

    def list_models(self) -> tuple[str, ...]: ...

    def health(self) -> bool: ...
