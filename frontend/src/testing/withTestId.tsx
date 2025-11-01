import { cloneElement, isValidElement, type ReactElement } from 'react'

export function withTestId<T extends ReactElement>(element: T, id?: string) {
  if (!id) {
    return element
  }
  if (!isValidElement(element)) {
    return element
  }
  return cloneElement(element, { 'data-testid': id })
}
