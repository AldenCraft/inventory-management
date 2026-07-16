import { ref } from 'vue'

// Reusable click-to-sort state + logic for data tables.
//
// Sort cycle for a single column: asc -> desc -> off.
// "off" (sortDir null) intentionally returns rows untouched so each view's
// existing default order (e.g. Inventory's low-stock-first) shows through
// unchanged — the base filtered computed already carries that order, and we
// only layer sorting on top of it.
export function useTableSort() {
  const sortKey = ref(null) // string | null — the active column key
  const sortDir = ref(null) // 'asc' | 'desc' | null

  const toggleSort = (key) => {
    if (key !== sortKey.value) {
      // New column: start ascending.
      sortKey.value = key
      sortDir.value = 'asc'
      return
    }

    // Same column: advance through asc -> desc -> off.
    if (sortDir.value === 'asc') {
      sortDir.value = 'desc'
    } else if (sortDir.value === 'desc') {
      // Third click turns sorting off entirely.
      sortDir.value = null
      sortKey.value = null
    } else {
      sortDir.value = 'asc'
    }
  }

  const applySort = (rows, accessors) => {
    const key = sortKey.value
    const dir = sortDir.value

    // Off state, or a column with no accessor: leave the view's default order.
    if (!key || !dir || !accessors || !accessors[key]) {
      return rows
    }

    const accessor = accessors[key]
    const factor = dir === 'asc' ? 1 : -1

    // Sort a copy so we never mutate the source array.
    return rows.slice().sort((rowA, rowB) => {
      const a = accessor(rowA)
      const b = accessor(rowB)

      // Nulls/undefined always sort last, regardless of direction.
      const aMissing = a === null || a === undefined
      const bMissing = b === null || b === undefined
      if (aMissing && bMissing) return 0
      if (aMissing) return 1
      if (bMissing) return -1

      let cmp
      if (typeof a === 'number' && typeof b === 'number') {
        cmp = a - b
      } else {
        cmp = String(a).localeCompare(String(b))
      }

      return cmp * factor
    })
  }

  return { sortKey, sortDir, toggleSort, applySort }
}
