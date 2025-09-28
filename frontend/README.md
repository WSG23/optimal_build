# Frontend development notes

## Opting into buildable mocks locally

`fetchBuildable` now always performs a real network request unless you explicitly
provide a mock transport. This keeps production behaviour predictable while
still allowing local development and tests to exercise the UI without the API.

Use the helpers in `src/mocks/buildable.ts` to opt into the default mock
responses (the same dataset that used to be driven by
`VITE_FEASIBILITY_USE_MOCKS`). The helper returns an options object that can be
passed straight into `fetchBuildable`.

```ts
import { fetchBuildable } from './api/buildable'
import { createMockBuildableOptions } from './mocks/buildable'

const summary = await fetchBuildable(
    {
        address: '123 Example Ave',
        typFloorToFloorM: 3.4,
        efficiencyRatio: 0.8,
    },
    createMockBuildableOptions(),
)
```

Because the helper simply wraps the existing `fetchBuildable` request options,
you can feature-gate it however you like during development. For example:

```ts
const buildableOptions = import.meta.env.DEV
    ? createMockBuildableOptions()
    : undefined

fetchBuildable(payload, { signal: controller.signal, ...buildableOptions })
```

You can also customise the responses that are returned:

```ts
const mockOptions = createMockBuildableOptions({
    responses: {
        '10 downing street': {
            input_kind: 'address',
            zone_code: 'R5',
            overlays: [],
            advisory_hints: [],
            metrics: {
                gfa_cap_m2: 100,
                floors_max: 2,
                footprint_m2: 50,
                nsa_est_m2: 80,
            },
            zone_source: {
                kind: 'parcel',
                layer_name: null,
                jurisdiction: null,
                parcel_ref: null,
                parcel_source: null,
                note: null,
            },
            rules: [],
        },
    },
})

await fetchBuildable(payload, mockOptions)
```

The helper normalises address keys to lower case, matching the behaviour of the
previous in-module mock table.
