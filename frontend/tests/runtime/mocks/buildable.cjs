const DEFAULT_FALLBACK_RESPONSE = {
    input_kind: 'address',
    zone_code: null,
    overlays: [],
    advisory_hints: [],
    metrics: {
        gfa_cap_m2: 0,
        floors_max: 0,
        footprint_m2: 0,
        nsa_est_m2: 0,
    },
    zone_source: {
        kind: 'unknown',
        layer_name: null,
        jurisdiction: null,
        parcel_ref: null,
        parcel_source: null,
        note: null,
    },
    rules: [],
}

const DEFAULT_RESPONSES = {
    '123 example ave': {
        input_kind: 'address',
        zone_code: 'R2',
        overlays: ['heritage', 'daylight'],
        advisory_hints: [
            'Heritage impact assessment required before façade alterations.',
            'Respect daylight plane controls along the street frontage.',
        ],
        metrics: {
            gfa_cap_m2: 4375,
            floors_max: 8,
            footprint_m2: 563,
            nsa_est_m2: 3588,
        },
        zone_source: {
            kind: 'parcel',
            layer_name: 'MasterPlan',
            jurisdiction: 'SG',
            parcel_ref: 'MK01-01234',
            parcel_source: 'sample_loader',
        },
        rules: [
            {
                id: 1,
                authority: 'URA',
                parameter_key: 'parking.min_car_spaces_per_unit',
                operator: '>=',
                value: '1.5',
                unit: 'spaces_per_unit',
                provenance: {
                    rule_id: 1,
                    clause_ref: '4.2.1',
                    document_id: 345,
                    pages: [7],
                    seed_tag: 'zoning',
                },
            },
        ],
    },
    '456 river road': {
        input_kind: 'address',
        zone_code: 'C1',
        overlays: ['airport'],
        advisory_hints: [
            'Coordinate with CAAS on height limits under the airport safeguarding zone.',
        ],
        metrics: {
            gfa_cap_m2: 3430,
            floors_max: 8,
            footprint_m2: 441,
            nsa_est_m2: 2813,
        },
        zone_source: {
            kind: 'parcel',
            layer_name: 'MasterPlan',
            jurisdiction: 'SG',
            parcel_ref: 'MK02-00021',
            parcel_source: 'sample_loader',
        },
        rules: [],
    },
    '789 coastal way': {
        input_kind: 'address',
        zone_code: 'B1',
        overlays: ['coastal'],
        advisory_hints: [
            'Implement coastal flood resilience measures for ground floors.',
            'Consult PUB on shoreline protection obligations.',
        ],
        metrics: {
            gfa_cap_m2: 3920,
            floors_max: 8,
            footprint_m2: 504,
            nsa_est_m2: 3214,
        },
        zone_source: {
            kind: 'parcel',
            layer_name: 'MasterPlan',
            jurisdiction: 'SG',
            parcel_ref: 'MK03-04567',
            parcel_source: 'sample_loader',
        },
        rules: [],
    },
}

function normaliseAddress(address) {
    return address.trim().toLowerCase()
}

function cloneBuildableResponse(payload) {
    return {
        input_kind: payload.input_kind,
        zone_code: payload.zone_code,
        overlays: [...payload.overlays],
        advisory_hints: payload.advisory_hints
            ? [...payload.advisory_hints]
            : null,
        metrics: { ...payload.metrics },
        zone_source: { ...payload.zone_source },
        rules: payload.rules.map((rule) => ({
            ...rule,
            provenance: { ...rule.provenance },
        })),
    }
}

function createMockBuildableTransport(options = {}) {
    const {
        responses = DEFAULT_RESPONSES,
        fallbackResponse = DEFAULT_FALLBACK_RESPONSE,
    } = options
    return async (_baseUrl, request) => {
        const key = normaliseAddress(request.address)
        const response = responses[key] ?? fallbackResponse
        return cloneBuildableResponse(response)
    }
}

function createMockBuildableOptions(options = {}) {
    return { transport: createMockBuildableTransport(options) }
}

module.exports = {
    createMockBuildableOptions,
    createMockBuildableTransport,
}
