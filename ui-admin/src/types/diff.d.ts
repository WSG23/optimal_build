declare module 'diff' {
  export interface Change<T = string> {
    value: T
    count?: number
    added?: boolean
    removed?: boolean
  }

  export interface DiffOptions {
    ignoreCase?: boolean
    ignoreWhitespace?: boolean
    newlineIsToken?: boolean
  }

  export function diffLines(
    oldStr: string,
    newStr: string,
    options?: DiffOptions,
  ): Array<Change>
}
