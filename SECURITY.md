# Security Policy

## Supported versions

Agent Canvas is pre-1.0. Security fixes land on `main` and in the next release; there are
no long-term support branches yet.

## Reporting a vulnerability

**Please do not open a public issue for security problems.** Use GitHub's private
reporting instead: go to the repository's **Security** tab → **Report a vulnerability**.

Please include a description of the issue, reproduction steps, and the impact you believe
it has. We aim to acknowledge reports within a few days and will keep you updated as we
work on a fix. Let us know how you'd like to be credited.

## Scope and threat model

Agent Canvas ingests **execution traces**, which routinely contain prompts, tool
arguments, file contents, and file paths from the systems an agent touched. Treat a trace
as sensitive by default.

Things worth knowing when deploying:

- **Traces are not sanitized on ingest.** If your agent handled secrets, those secrets may
  appear in prompts, tool inputs, or file contents stored in `span_io`.
- **There is no authentication or multi-tenancy yet** (both are on the V1 roadmap). Anyone
  who can reach the API can read every ingested session. Do not expose an instance holding
  real traces to an untrusted network.
- **The public demo deployment is seeded with a synthetic sample trace only** and its
  storage is ephemeral — do not upload real traces to it.
- Ingestion parses untrusted JSON. Parser crashes or resource-exhaustion issues in the
  adapters or projector are in scope.
