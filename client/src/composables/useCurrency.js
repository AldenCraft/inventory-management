import { computed } from 'vue'
import { useI18n } from './useI18n'

// Single source of truth for the currency symbol that was previously copy-pasted
// as `currentCurrency.value === 'JPY' ? '¥' : '$'` across the views and modals.
// Currency follows locale (see useI18n: ja -> JPY, otherwise USD).
export function useCurrency() {
  const { currentCurrency } = useI18n()

  const currencySymbol = computed(() => {
    return currentCurrency.value === 'JPY' ? '¥' : '$'
  })

  return { currencySymbol }
}
