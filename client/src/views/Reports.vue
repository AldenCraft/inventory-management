<template>
  <div class="reports">
    <div class="page-header">
      <h2>{{ t('reports.title') }}</h2>
      <p>{{ t('reports.description') }}</p>
    </div>

    <div v-if="loading" class="loading">{{ t('reports.loading') }}</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else>
      <!-- Quarterly Performance -->
      <div class="card">
        <div class="card-header">
          <h3 class="card-title">{{ t('reports.quarterlyPerformance') }}</h3>
        </div>
        <div class="table-container">
          <table class="reports-table">
            <thead>
              <tr>
                <SortableTh column-key="quarter" :label="t('reports.table.quarter')" :sort-key="quarterlySortKey" :sort-dir="quarterlySortDir" @sort="toggleQuarterlySort" />
                <SortableTh column-key="totalOrders" :label="t('reports.table.totalOrders')" :sort-key="quarterlySortKey" :sort-dir="quarterlySortDir" @sort="toggleQuarterlySort" />
                <SortableTh column-key="totalRevenue" :label="t('reports.table.totalRevenue')" :sort-key="quarterlySortKey" :sort-dir="quarterlySortDir" @sort="toggleQuarterlySort" />
                <SortableTh column-key="avgOrderValue" :label="t('reports.table.avgOrderValue')" :sort-key="quarterlySortKey" :sort-dir="quarterlySortDir" @sort="toggleQuarterlySort" />
                <SortableTh column-key="fulfillmentRate" :label="t('reports.table.fulfillmentRate')" :sort-key="quarterlySortKey" :sort-dir="quarterlySortDir" @sort="toggleQuarterlySort" />
              </tr>
            </thead>
            <tbody>
              <tr v-for="q in sortedQuarterly" :key="q.quarter">
                <td><strong>{{ q.quarter }}</strong></td>
                <td>{{ q.total_orders }}</td>
                <td>{{ formatCurrency(q.total_revenue) }}</td>
                <td>{{ formatCurrency(q.avg_order_value) }}</td>
                <td>
                  <span :class="getFulfillmentClass(q.fulfillment_rate)">
                    {{ q.fulfillment_rate }}%
                  </span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Monthly Trends Chart: always shows every month, independent of the Time Period filter -->
      <div class="card">
        <div class="card-header">
          <h3 class="card-title">{{ t('reports.monthlyRevenueTrend') }}</h3>
        </div>
        <div class="chart-container">
          <div class="bar-chart">
            <div v-for="month in chartMonthly" :key="month.month" class="bar-wrapper">
              <div class="bar-container">
                <div
                  class="bar"
                  :style="{ height: getBarHeight(month.revenue) + 'px' }"
                  :title="formatCurrency(month.revenue)"
                ></div>
              </div>
              <div class="bar-label">{{ formatMonth(month.month) }}</div>
            </div>
          </div>
        </div>
      </div>

      <!-- Month-over-Month Comparison -->
      <div class="card">
        <div class="card-header">
          <h3 class="card-title">{{ t('reports.monthOverMonthAnalysis') }}</h3>
        </div>
        <div class="table-container">
          <table class="reports-table">
            <thead>
              <tr>
                <SortableTh column-key="month" :label="t('reports.table.month')" :sort-key="monthlySortKey" :sort-dir="monthlySortDir" @sort="toggleMonthlySort" />
                <SortableTh column-key="orders" :label="t('reports.table.orders')" :sort-key="monthlySortKey" :sort-dir="monthlySortDir" @sort="toggleMonthlySort" />
                <SortableTh column-key="revenue" :label="t('reports.table.revenue')" :sort-key="monthlySortKey" :sort-dir="monthlySortDir" @sort="toggleMonthlySort" />
                <SortableTh column-key="change" :label="t('reports.table.change')" :sort-key="monthlySortKey" :sort-dir="monthlySortDir" @sort="toggleMonthlySort" />
                <SortableTh column-key="growthRate" :label="t('reports.table.growthRate')" :sort-key="monthlySortKey" :sort-dir="monthlySortDir" @sort="toggleMonthlySort" />
              </tr>
            </thead>
            <tbody>
              <tr v-for="month in sortedMonthly" :key="month.month">
                <td><strong>{{ formatMonth(month.month) }}</strong></td>
                <td>{{ month.order_count }}</td>
                <td>{{ formatCurrency(month.revenue) }}</td>
                <td>
                  <!-- Change/Growth compare to the chronologically previous month (prevRevenue),
                       precomputed from the full, unfiltered monthly series so a single filtered
                       row (or any sort order) still shows the correct real-world comparison. -->
                  <span v-if="month.prevRevenue !== null" :class="getChangeClass(month.revenue, month.prevRevenue)">
                    {{ getChangeValue(month.revenue, month.prevRevenue) }}
                  </span>
                  <span v-else>{{ t('reports.noChange') }}</span>
                </td>
                <td>
                  <span v-if="month.prevRevenue !== null" :class="getChangeClass(month.revenue, month.prevRevenue)">
                    {{ getGrowthRate(month.revenue, month.prevRevenue) }}
                  </span>
                  <span v-else>{{ t('reports.noChange') }}</span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Summary Stats -->
      <div class="stats-grid">
        <div class="stat-card">
          <div class="stat-label">{{ t('reports.summary.totalRevenueYtd') }}</div>
          <div class="stat-value">{{ formatCurrency(summaryStats.totalRevenue) }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">{{ t('reports.summary.avgMonthlyRevenue') }}</div>
          <div class="stat-value">{{ formatCurrency(summaryStats.avgMonthlyRevenue) }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">{{ t('reports.summary.totalOrdersYtd') }}</div>
          <div class="stat-value">{{ summaryStats.totalOrders }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">{{ t('reports.summary.bestQuarter') }}</div>
          <div class="stat-value">{{ summaryStats.bestQuarter || t('reports.noChange') }}</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted } from 'vue'
import { api } from '../api'
import { useFilters } from '../composables/useFilters'
import { useI18n } from '../composables/useI18n'
import { useTableSort } from '../composables/useTableSort'
import { formatCurrency as formatCurrencyUtil, formatCurrencyWithDecimals } from '../utils/currency'
import SortableTh from '../components/SortableTh.vue'

export default {
  name: 'Reports',
  components: {
    SortableTh
  },
  setup() {
    const { t, currentLocale, currentCurrency } = useI18n()

    const loading = ref(true)
    const error = ref(null)

    // Raw data from the API, unfiltered. The monthly trend chart reads straight
    // from these so it always shows the full year regardless of Time Period.
    const allQuarterly = ref([])
    const allMonthly = ref([])

    // Time Period is the only filter this page supports, and it's applied
    // entirely client-side (data is fetched once, on mount).
    const { selectedPeriod } = useFilters()

    // Attach each month's chronologically previous revenue on the FULL series,
    // before any Time Period filtering is applied, so a filtered single-month
    // row still shows the correct change vs its real previous month.
    const monthlyWithPrev = computed(() => {
      return allMonthly.value.map((m, i) => ({
        ...m,
        prevRevenue: i > 0 ? allMonthly.value[i - 1].revenue : null
      }))
    })

    // Chart always shows every month (matches Spending.vue's monthly chart behavior).
    const chartMonthly = computed(() => allMonthly.value)

    // Converts a "YYYY-MM" period into this API's quarter label (e.g. "Q3-2025")
    // so the quarterly table can be narrowed to the quarter containing the
    // selected month.
    const periodToQuarter = (period) => {
      const parts = period.split('-')
      if (parts.length !== 2) return null
      const year = parts[0]
      const monthNum = parseInt(parts[1], 10)
      if (isNaN(monthNum) || monthNum < 1 || monthNum > 12) return null
      const quarterNum = Math.ceil(monthNum / 3)
      return `Q${quarterNum}-${year}`
    }

    const filteredMonthly = computed(() => {
      if (selectedPeriod.value === 'all') return monthlyWithPrev.value
      return monthlyWithPrev.value.filter(m => m.month === selectedPeriod.value)
    })

    const filteredQuarterly = computed(() => {
      if (selectedPeriod.value === 'all') return allQuarterly.value
      const quarter = periodToQuarter(selectedPeriod.value)
      return allQuarterly.value.filter(q => q.quarter === quarter)
    })

    // Click-to-sort, one instance per table. Sorting operates on the
    // already-filtered rows; prevRevenue travels with each row so Change/Growth
    // stay correct no matter how the table is sorted.
    const quarterly = useTableSort()
    const monthly = useTableSort()

    const sortedQuarterly = computed(() => quarterly.applySort(filteredQuarterly.value, {
      quarter: (q) => q.quarter,
      totalOrders: (q) => q.total_orders,
      totalRevenue: (q) => q.total_revenue,
      avgOrderValue: (q) => q.avg_order_value,
      fulfillmentRate: (q) => q.fulfillment_rate
    }))

    const sortedMonthly = computed(() => monthly.applySort(filteredMonthly.value, {
      month: (m) => m.month,
      orders: (m) => m.order_count,
      revenue: (m) => m.revenue,
      // Derived: null prevRevenue (first month in the series) always sorts last
      change: (m) => (m.prevRevenue === null ? null : m.revenue - m.prevRevenue),
      growthRate: (m) => (m.prevRevenue === null || m.prevRevenue === 0 ? null : (m.revenue - m.prevRevenue) / m.prevRevenue)
    }))

    // Summary recomputes from the filtered monthly/quarterly data, not the
    // unfiltered chart data.
    const summaryStats = computed(() => {
      const rows = filteredMonthly.value
      const totalRevenue = rows.reduce((sum, m) => sum + (m.revenue || 0), 0)
      const totalOrders = rows.reduce((sum, m) => sum + (m.order_count || 0), 0)
      const avgMonthlyRevenue = rows.length > 0 ? totalRevenue / rows.length : 0

      let bestQuarter = ''
      let bestRevenue = 0
      for (const q of filteredQuarterly.value) {
        if (q.total_revenue > bestRevenue) {
          bestRevenue = q.total_revenue
          bestQuarter = q.quarter
        }
      }

      return { totalRevenue, avgMonthlyRevenue, totalOrders, bestQuarter }
    })

    // Bar heights are scaled against the unfiltered chart data's max, computed
    // once rather than re-scanning all months for every bar rendered.
    const maxRevenue = computed(() => {
      if (chartMonthly.value.length === 0) return 0
      return Math.max(...chartMonthly.value.map(m => m.revenue))
    })

    const loadData = async () => {
      try {
        loading.value = true
        error.value = null
        const [quarterlyRes, monthlyRes] = await Promise.all([
          api.getQuarterlyReports(),
          api.getMonthlyTrends()
        ])
        allQuarterly.value = quarterlyRes
        allMonthly.value = monthlyRes
      } catch (err) {
        error.value = `${t('reports.error')}: ${err.message}`
      } finally {
        loading.value = false
      }
    }

    const formatCurrency = (value) => formatCurrencyUtil(value ?? 0, currentCurrency.value)

    // "YYYY-MM" -> localized "Mon YYYY". Falls back to the raw string on
    // malformed input instead of throwing (bad data shouldn't crash the page).
    const formatMonth = (monthStr) => {
      if (!monthStr || typeof monthStr !== 'string') return ''
      const parts = monthStr.split('-')
      if (parts.length !== 2) return monthStr

      const year = parseInt(parts[0], 10)
      const monthIndex = parseInt(parts[1], 10) - 1
      if (isNaN(year) || isNaN(monthIndex) || monthIndex < 0 || monthIndex > 11) return monthStr

      const date = new Date(year, monthIndex, 1)
      if (isNaN(date.getTime())) return monthStr

      const locale = currentLocale.value === 'ja' ? 'ja-JP' : 'en-US'
      return date.toLocaleDateString(locale, { year: 'numeric', month: 'short' })
    }

    const getBarHeight = (revenue) => {
      if (!maxRevenue.value) return 0
      return (revenue / maxRevenue.value) * 200
    }

    const getFulfillmentClass = (rate) => {
      if (rate >= 90) return 'badge success'
      if (rate >= 75) return 'badge warning'
      return 'badge danger'
    }

    const getChangeValue = (current, previous) => {
      const change = current - previous
      // Currency + sign are handled separately: formatCurrencyWithDecimals gives
      // symbol-correct, JPY-converted magnitude; the +/- prefix mirrors the sign.
      const formatted = formatCurrencyWithDecimals(Math.abs(change), currentCurrency.value, 2)
      if (change > 0) return `+${formatted}`
      if (change < 0) return `-${formatted}`
      return formatted
    }

    const getChangeClass = (current, previous) => {
      const change = current - previous
      if (change > 0) return 'positive-change'
      if (change < 0) return 'negative-change'
      return ''
    }

    const getGrowthRate = (current, previous) => {
      if (!previous) return t('reports.notAvailable')
      const rate = ((current - previous) / previous) * 100
      const sign = rate > 0 ? '+' : ''
      return `${sign}${rate.toFixed(1)}%`
    }

    onMounted(loadData)

    return {
      t,
      loading,
      error,
      chartMonthly,
      sortedQuarterly,
      sortedMonthly,
      summaryStats,
      quarterlySortKey: quarterly.sortKey,
      quarterlySortDir: quarterly.sortDir,
      toggleQuarterlySort: quarterly.toggleSort,
      monthlySortKey: monthly.sortKey,
      monthlySortDir: monthly.sortDir,
      toggleMonthlySort: monthly.toggleSort,
      formatCurrency,
      formatMonth,
      getBarHeight,
      getFulfillmentClass,
      getChangeValue,
      getChangeClass,
      getGrowthRate
    }
  }
}
</script>

<style scoped>
.reports {
  padding: 0;
}

.card {
  background: white;
  border-radius: 12px;
  padding: 1.5rem;
  margin-bottom: 1.5rem;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.card-header {
  margin-bottom: 1.5rem;
}

.card-title {
  font-size: 1.25rem;
  font-weight: 600;
  color: #0f172a;
  margin: 0;
}

.reports-table {
  width: 100%;
  border-collapse: collapse;
}

.reports-table th {
  background: #f8fafc;
  padding: 0.75rem;
  text-align: left;
  font-weight: 600;
  color: #64748b;
  border-bottom: 2px solid #e2e8f0;
}

.reports-table td {
  padding: 0.75rem;
  border-bottom: 1px solid #e2e8f0;
}

.reports-table tr:hover {
  background: #f8fafc;
}

.chart-container {
  padding: 2rem 1rem;
  min-height: 300px;
}

.bar-chart {
  display: flex;
  align-items: flex-end;
  justify-content: space-around;
  height: 250px;
  gap: 0.5rem;
}

.bar-wrapper {
  display: flex;
  flex-direction: column;
  align-items: center;
  flex: 1;
  max-width: 80px;
}

.bar-container {
  height: 200px;
  display: flex;
  align-items: flex-end;
  width: 100%;
}

.bar {
  width: 100%;
  background: linear-gradient(to top, #3b82f6, #60a5fa);
  border-radius: 4px 4px 0 0;
  transition: all 0.3s;
  cursor: pointer;
}

.bar:hover {
  background: linear-gradient(to top, #2563eb, #3b82f6);
}

.bar-label {
  margin-top: 1.5rem;
  font-size: 0.75rem;
  color: #64748b;
  text-align: center;
  transform: rotate(-45deg);
  white-space: nowrap;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 1rem;
  margin-top: 1.5rem;
}

.stat-card {
  background: white;
  border-radius: 12px;
  padding: 1.5rem;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  border-left: 4px solid #3b82f6;
}

.stat-label {
  font-size: 0.875rem;
  color: #64748b;
  margin-bottom: 0.5rem;
}

.stat-value {
  font-size: 1.875rem;
  font-weight: 700;
  color: #0f172a;
}

.badge {
  padding: 0.25rem 0.75rem;
  border-radius: 9999px;
  font-size: 0.875rem;
  font-weight: 500;
}

.badge.success {
  background: #dcfce7;
  color: #166534;
}

.badge.warning {
  background: #fef3c7;
  color: #92400e;
}

.badge.danger {
  background: #fee2e2;
  color: #991b1b;
}

.positive-change {
  color: #16a34a;
  font-weight: 600;
}

.negative-change {
  color: #dc2626;
  font-weight: 600;
}

.loading {
  text-align: center;
  padding: 3rem;
  color: #64748b;
}

.error {
  background: #fee2e2;
  color: #991b1b;
  padding: 1rem;
  border-radius: 8px;
  margin: 1rem 0;
}
</style>
