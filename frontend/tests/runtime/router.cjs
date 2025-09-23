function createLinkClickHandler(router, to) {
  return (event) => {
    if (!event || typeof event !== 'object') {
      return
    }
    if (event.defaultPrevented) {
      return
    }
    if (event.button !== 0) {
      return
    }
    if (event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) {
      return
    }
    if (typeof event.preventDefault === 'function') {
      event.preventDefault()
    }
    router.navigate(to)
  }
}

module.exports = { createLinkClickHandler }
