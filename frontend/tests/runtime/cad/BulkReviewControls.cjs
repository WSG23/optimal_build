const React = require('react')
const { useTranslation } = require('../i18n/index.cjs')

function BulkReviewControls({
  pendingCount = 0,
  onApproveAll = () => {},
  onRejectAll = () => {},
  disabled = false,
}) {
  void onApproveAll
  void onRejectAll
  const { t } = useTranslation()
  return React.createElement(
    'section',
    { className: 'bulk-review-controls' },
    React.createElement(
      'p',
      { className: 'bulk-review-controls__count' },
      `${t('bulk.pendingLabel')}: ${pendingCount}`,
    ),
    React.createElement(
      'div',
      { className: 'bulk-review-controls__actions' },
      React.createElement(
        'button',
        { type: 'button', disabled },
        t('bulk.approveAll'),
      ),
      React.createElement(
        'button',
        { type: 'button', disabled },
        t('bulk.rejectAll'),
      ),
    ),
  )
}

module.exports = { BulkReviewControls }
