/**
 *  Get element from array from a given step
 *
 * @example
 * ```tsx
 * getFromIndex(['peach', 'apple', 'orange'], 0, 1) // => 'apple'
 * getFromIndex(['peach', 'apple', 'orange'], 0, -1) // => 'orange'
 * ```
 */
export const getFromIndex = <T extends unknown[]>(
  array: T,
  currentIndex: number,
  step: number
): T[number] => {
  switch (true) {
    case step === 0:
      return array[currentIndex]
    case step < 0: {
      return array[(currentIndex + array.length + step) % array.length]
    }
    case step > 0: {
      return array[(currentIndex + step) % array.length]
    }
  }
}
