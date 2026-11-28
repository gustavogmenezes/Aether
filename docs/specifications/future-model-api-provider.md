# Future Model API Provider

**Status:** Planned capability adapter; not required for essential execution

## Purpose

The current local path uses a replaceable `InferenceProviderPort` with the
Ollama adapter. A future external-provider adapter may implement the same
contract for a user-supplied model service or API.

## Non-negotiable constraints

- External inference remains optional.
- Essential Aether behavior continues to operate locally.
- Provider credentials are supplied through runtime secret input or the user's
  environment, never repository files, prompts, events, logs, or lore.
- Agent domain logic depends only on `InferenceProviderPort`.
- Model-specific response metadata remains inside the provider adapter.
- The same structured proposal, validation, invocation, and recovery records
  apply to local and external providers.
- Users select capability-to-model mappings; the system does not silently
  redirect a local request to a paid remote service.
- Requests sent externally must have an explicit user action and a clear
  data-boundary policy for prompt/context content.

## Proposed configuration

An external provider configuration should contain:

- Provider identifier and base URL.
- Capability mapping.
- Model identifier.
- Timeout and retry policy.
- Whether the provider receives full context or a minimized projection.
- Secret environment-variable name.
- Per-request maximum tokens.
- Cost/accounting and opt-in state.

Secrets themselves are not configuration values committed to disk.

## Required implementation stages

1. Define an external provider adapter behind `InferenceProviderPort`.
2. Add configuration validation and secret redaction.
3. Add a user-visible provider selection and opt-in boundary.
4. Run the same `operational-model-benchmark.md` gates.
5. Add provider failure and cancellation recovery tests.
6. Record the specific provider as an ADR after technical validation.

No external provider or API credential is selected by the current
implementation.
