import { computed, unref } from 'vue'
import { useI18n } from './useI18n'

// Reorder-point thresholds, previously duplicated (and drifted) across Inventory.vue
// and InventoryDetailModal.vue. Locale-independent key so styling stays correct in any
// language; the visible label is translated via the existing `status.*` i18n keys.
const stockStatusKey = (item) => {
  if (!item) return null
  if (item.quantity_on_hand <= item.reorder_point) {
    return 'lowStock'
  } else if (item.quantity_on_hand <= item.reorder_point * 1.5) {
    return 'adequate'
  } else {
    return 'inStock'
  }
}

const KEY_TO_CLASS = {
  lowStock: 'danger',
  adequate: 'warning',
  inStock: 'success'
}

// Usable two ways:
//  - Per-item helpers (`getKey`/`getLabel`/`getClass`) for table rows that classify many
//    items in a loop (Inventory.vue).
//  - Reactive `{ key, label, class }` computeds when passed a single item as a ref or a
//    getter (InventoryDetailModal.vue), matching the shape requested in the review thread.
export function useStockStatus(item) {
  const { t } = useI18n()

  const getKey = (i) => stockStatusKey(i)
  const getClass = (i) => KEY_TO_CLASS[stockStatusKey(i)] || 'success'
  const getLabel = (i) => {
    const key = stockStatusKey(i)
    return key ? t(`status.${key}`) : ''
  }

  // Resolve the (optional) reactive item: supports a getter fn, a ref, or a plain object.
  const resolve = () => (typeof item === 'function' ? item() : unref(item))

  const key = computed(() => getKey(resolve()))
  const label = computed(() => getLabel(resolve()))
  const stockClass = computed(() => getClass(resolve()))

  return { key, label, class: stockClass, getKey, getLabel, getClass }
}
