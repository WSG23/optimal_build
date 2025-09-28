const React = require('react')

const ALL_LAYERS = ['source', 'approved', 'pending', 'rejected']

function LayerTogglePanel({
    activeLayers = [],
    onToggle = () => {},
    disabled = false,
}) {
    void onToggle
    const activeSet = new Set(activeLayers)
    return React.createElement(
        'div',
        { className: 'cad-layer-toggle' },
        ALL_LAYERS.map((layer) =>
            React.createElement(
                'button',
                {
                    key: layer,
                    type: 'button',
                    className: `cad-layer-toggle__button${
                        activeSet.has(layer)
                            ? ' cad-layer-toggle__button--active'
                            : ''
                    }`,
                    disabled,
                },
                layer,
            ),
        ),
    )
}

function computeNextLayers(current, layer) {
    const set = new Set(current)
    if (set.has(layer)) {
        set.delete(layer)
    } else {
        set.add(layer)
    }
    return Array.from(set)
}

module.exports = { LayerTogglePanel, computeNextLayers }
