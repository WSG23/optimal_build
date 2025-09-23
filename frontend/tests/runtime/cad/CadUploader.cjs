const React = require('react')
const { useTranslation } = require('../i18n/index.cjs')

function resolveStatusLabel(status, t) {
  switch (status?.status) {
    case 'completed':
      return t('uploader.ready')
    case 'failed':
      return t('uploader.error')
    case 'queued':
    case 'running':
    case 'pending':
      return t('uploader.parsing')
    default:
      return null
  }
}

function CadUploader({ onUpload = () => {}, isUploading = false, status = null, summary = null }) {
  void onUpload
  const { t } = useTranslation()
  const fallbackDash = t('common.fallback.dash')
  const detectedFloors = status?.detectedFloors ?? summary?.detectedFloors ?? []
  const detectedUnits = status?.detectedUnits ?? summary?.detectedUnits ?? []
  const latestStatus = resolveStatusLabel(status, t) ?? t('uploader.parsing')

  return React.createElement(
    'div',
    { className: 'cad-uploader' },
    React.createElement(
      'div',
      { className: 'cad-uploader__dropzone', role: 'presentation' },
      React.createElement('input', {
        type: 'file',
        accept: '.dxf,.dwg,.zip',
        className: 'cad-uploader__input',
        disabled: isUploading,
      }),
      React.createElement('p', { className: 'cad-uploader__hint' }, t('uploader.dropHint')),
      React.createElement(
        'button',
        { type: 'button', className: 'cad-uploader__browse', disabled: isUploading },
        t('uploader.browseLabel'),
      ),
    ),
    React.createElement(
      'aside',
      { className: 'cad-uploader__status' },
      React.createElement('h3', null, t('uploader.latestStatus')),
      summary
        ? React.createElement('p', { className: 'cad-uploader__filename' }, summary.fileName)
        : null,
      React.createElement('p', null, latestStatus),
      status?.error ? React.createElement('p', { className: 'cad-uploader__message' }, status.error) : null,
      React.createElement(
        'dl',
        { className: 'cad-uploader__meta' },
        React.createElement(
          'div',
          null,
          React.createElement('dt', null, t('uploader.floors')),
          React.createElement(
            'dd',
            null,
            detectedFloors.length > 0
              ? detectedFloors.map((floor) => floor.name).join(', ')
              : fallbackDash,
          ),
        ),
        React.createElement(
          'div',
          null,
          React.createElement('dt', null, t('uploader.units')),
          React.createElement('dd', null, detectedUnits.length > 0 ? detectedUnits.length : fallbackDash),
        ),
      ),
    ),
  )
}

module.exports = { CadUploader }
