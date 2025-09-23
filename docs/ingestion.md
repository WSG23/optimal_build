# Ingestion flows

The ingestion utilities are implemented as Prefect flows so they can be
scheduled by the real Prefect runtime when it is available. The test
environment that powers this repository does not depend on Prefect,
therefore a lightweight shim lives at `prefect/__init__.py`. The shim
exposes a no-op `@flow` decorator that leaves the wrapped coroutine intact
and provides a `.with_options()` helper so commands such as
`prefect deployment build` can still introspect the flow object.

Because the decorator returns the original coroutine, the CLI entry points
in `backend/flows/watch_fetch.py` and `backend/flows/parse_segment.py` invoke
flows directly in the local environment. Both modules resolve the underlying
callable by probing for common Prefect attributes such as `__wrapped__` or
`fn`, only falling back to the object itself when necessary. This keeps the
code path independent of Prefect internals while remaining compatible with
the real runtime. The same approach is mirrored in `backend/flows/__init__.py`,
which re-exports callables that can be awaited during tests.

When Prefect is installed the actual package will supply richer behaviour,
including orchestration and state management. The shim is only intended for
offline testing and should not be used in production deployments.

## How Buildable consumes ref_rules

The buildable service queries `RefRule` records tagged with the `zoning`
topic whenever a zoning code is resolved. Only rules that are approved and
published are considered, and each matching rule is surfaced in the response
payload so downstream consumers can see the exact text that informed the
calculation. When multiple rules apply to the same zoning parameter, the
service keeps the most restrictive value – lower plot ratios, tighter site
coverage fractions, and larger front setbacks take precedence over any
defaults that may also be present in the dataset. The override values are
captured before defaults are merged, ensuring that seed data cannot relax an
ingested requirement if both are present for the same zone.
