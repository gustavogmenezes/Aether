# ADR 0017 — Local Inference Service Boundary

## Context

DEC-001 through DEC-003 require benchmark evidence before selecting a concrete
model and resource policy. The user additionally requires a current local
service path and a future user-supplied API path.

## Decision

Use `InferenceProviderPort` as the stable agent boundary. The current local
adapter is `OllamaProvider`, configured with a base URL and model name selected
by the user. Ollama's service owns model loading while Aether records invocation
capability, model identifier, tokens, response, and duration.

Game Master and Narrator adapters consume the provider through the protocol,
produce structured proposals/drafts, and still pass through existing
application validation. No provider may write directly to persistence or
mechanical state.

Concrete local model, quantization, keep-alive values, concurrency, and
context limits remain benchmark-derived DEC-001/002/003 choices. The adapter
does not approve them.

Future API providers may implement the same protocol under
`future-model-api-provider.md`. Secrets remain runtime inputs, and external
requests require explicit user opt-in.

## Consequences

- A user can select any installed Ollama model without changing domain code.
- An unavailable service fails explicitly and remains recoverable.
- Benchmarking and production agent calls use the same capability boundary.
- API credentials and provider-specific schemas do not enter domain state.
- Model loading policy and remote-provider selection remain separate decisions.
