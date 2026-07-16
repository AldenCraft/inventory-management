// Currency conversion utility
// USD to JPY exchange rate (approximate)
const USD_TO_JPY = 150

export function formatCurrency(amount, currency = 'USD') {
  // Coerce null/undefined/NaN to 0 so the USD path can't crash on
  // .toLocaleString and the JPY path can't emit ¥NaN — both currencies
  // now render a stable zero for missing values (e.g. empty/filtered KPIs).
  if (amount == null || isNaN(amount)) amount = 0
  // Put the minus before the symbol (-$1,234), not after it ($-1,234):
  // toLocaleString keeps the sign on the number, so we format the magnitude
  // and prepend the sign ourselves.
  const sign = amount < 0 ? '-' : ''
  const magnitude = Math.abs(amount)
  if (currency === 'JPY') {
    const yenAmount = Math.round(magnitude * USD_TO_JPY)
    return `${sign}¥${yenAmount.toLocaleString('ja-JP')}`
  }
  // Default USD
  return `${sign}$${magnitude.toLocaleString('en-US', { maximumFractionDigits: 0 })}`
}

export function formatCurrencyWithDecimals(amount, currency = 'USD', decimals = 0) {
  if (amount == null || isNaN(amount)) amount = 0
  // Same sign-before-symbol handling as formatCurrency (see note there).
  const sign = amount < 0 ? '-' : ''
  const magnitude = Math.abs(amount)
  if (currency === 'JPY') {
    const yenAmount = Math.round(magnitude * USD_TO_JPY)
    return `${sign}¥${yenAmount.toLocaleString('ja-JP')}`
  }
  // Default USD
  return `${sign}$${magnitude.toLocaleString('en-US', { minimumFractionDigits: decimals, maximumFractionDigits: decimals })}`
}

export function convertAmount(amount, currency = 'USD') {
  if (amount == null || isNaN(amount)) amount = 0
  if (currency === 'JPY') {
    return Math.round(amount * USD_TO_JPY)
  }
  return amount
}
