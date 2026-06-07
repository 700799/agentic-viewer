# License Recommendation

Deliverable **#10**. **Recommended and adopted: Apache License 2.0** (see [`LICENSE`](../LICENSE)).

## Rationale

1. **Permissive — maximizes adapter ecosystem adoption.** Agent Canvas is an
   observability tool whose value grows with the number of frameworks that emit traces to
   it. A permissive license lets teams embed it in proprietary stacks and contributors
   ship adapters without legal friction — the same dynamic that made OpenTelemetry
   (Apache-2.0) ubiquitous.
2. **Explicit patent grant** (§3) — unlike MIT, Apache-2.0 grants contributors' patent
   rights and includes a retaliation clause. This matters for a tool that implements
   around evolving, sometimes patent-encumbered SDK/trace formats.
3. **Ecosystem alignment.** The projects Agent Canvas integrates and draws inspiration
   from — OpenTelemetry, LangChain/LangGraph, many agent SDKs — are predominantly
   Apache-2.0 or MIT, minimizing compatibility concerns when bundling adapters.
4. **Trademark and NOTICE handling** are spelled out, giving the project room to protect
   its name while staying open.

## Alternatives considered

| License | When to prefer | Why not the default here |
|---|---|---|
| **MIT** | Absolute minimal ceremony | No explicit patent grant; weaker protection for a format-tracking tool |
| **AGPL-3.0** | To stop closed-source SaaS forks of a hosted product | Copyleft deters the corporate adoption and adapter contributions we want for the OSS core |
| **BSL / SSPL** | Commercial-source-available strategy | Not OSI-approved; would suppress community adapters |

## Future option

If a hosted/commercial offering emerges later, a common pattern is to keep the **core and
adapters Apache-2.0** (to preserve the ecosystem) while licensing a separate **server /
enterprise module under AGPL-3.0 or a commercial license**. Starting Apache-2.0 keeps that
door open without alienating early contributors.
