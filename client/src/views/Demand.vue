<template>
  <div class="demand">
    <div class="page-header">
      <h2>{{ t('demand.title') }}</h2>
      <p>{{ t('demand.description') }}</p>
    </div>

    <div v-if="loading" class="loading">{{ t('common.loading') }}</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else>
      <div class="demand-trend-cards">
        <div class="trend-card increasing-card">
          <div class="trend-header">
            <div class="trend-icon">↑</div>
            <div>
              <div class="trend-label">{{ t('demand.increasingDemand') }}</div>
              <div class="trend-count">{{ t('demand.itemsCount', { count: getForecastsByTrend('increasing').length }) }}</div>
            </div>
          </div>
          <div class="trend-items">
            <div v-for="item in getForecastsByTrend('increasing').slice(0, 5)" :key="item.id" class="trend-item">
              <span class="item-name">{{ item.item_name }}</span>
              <span class="item-change">+{{ getChangePercent(item) }}%</span>
            </div>
            <div v-if="getForecastsByTrend('increasing').length > 5" class="more-items">
              +{{ getForecastsByTrend('increasing').length - 5 }} {{ t('demand.more') }}
            </div>
          </div>
        </div>

        <div class="trend-card stable-card">
          <div class="trend-header">
            <div class="trend-icon">→</div>
            <div>
              <div class="trend-label">{{ t('demand.stableDemand') }}</div>
              <div class="trend-count">{{ t('demand.itemsCount', { count: getForecastsByTrend('stable').length }) }}</div>
            </div>
          </div>
          <div class="trend-items">
            <div v-for="item in getForecastsByTrend('stable').slice(0, 5)" :key="item.id" class="trend-item">
              <span class="item-name">{{ item.item_name }}</span>
              <span class="item-change neutral">{{ getChangePercent(item) }}%</span>
            </div>
            <div v-if="getForecastsByTrend('stable').length > 5" class="more-items">
              +{{ getForecastsByTrend('stable').length - 5 }} {{ t('demand.more') }}
            </div>
          </div>
        </div>

        <div class="trend-card decreasing-card">
          <div class="trend-header">
            <div class="trend-icon">↓</div>
            <div>
              <div class="trend-label">{{ t('demand.decreasingDemand') }}</div>
              <div class="trend-count">{{ t('demand.itemsCount', { count: getForecastsByTrend('decreasing').length }) }}</div>
            </div>
          </div>
          <div class="trend-items">
            <div v-for="item in getForecastsByTrend('decreasing').slice(0, 5)" :key="item.id" class="trend-item">
              <span class="item-name">{{ item.item_name }}</span>
              <span class="item-change">{{ getChangePercent(item) }}%</span>
            </div>
            <div v-if="getForecastsByTrend('decreasing').length > 5" class="more-items">
              +{{ getForecastsByTrend('decreasing').length - 5 }} {{ t('demand.more') }}
            </div>
          </div>
        </div>
      </div>

      <div class="card">
        <div class="card-header">
          <h3 class="card-title">{{ t('demand.demandForecasts') }}</h3>
        </div>
        <div class="table-container">
          <table>
            <thead>
              <tr>
                <SortableTh column-key="sku" :label="t('demand.table.sku')" :sort-key="sortKey" :sort-dir="sortDir" @sort="toggleSort" />
                <SortableTh column-key="itemName" :label="t('demand.table.itemName')" :sort-key="sortKey" :sort-dir="sortDir" @sort="toggleSort" />
                <SortableTh column-key="currentDemand" :label="t('demand.table.currentDemand')" :sort-key="sortKey" :sort-dir="sortDir" @sort="toggleSort" />
                <SortableTh column-key="forecastedDemand" :label="t('demand.table.forecastedDemand')" :sort-key="sortKey" :sort-dir="sortDir" @sort="toggleSort" />
                <SortableTh column-key="change" :label="t('demand.table.change')" :sort-key="sortKey" :sort-dir="sortDir" @sort="toggleSort" />
                <SortableTh column-key="trend" :label="t('demand.table.trend')" :sort-key="sortKey" :sort-dir="sortDir" @sort="toggleSort" />
                <SortableTh column-key="period" :label="t('demand.table.period')" :sort-key="sortKey" :sort-dir="sortDir" @sort="toggleSort" />
              </tr>
            </thead>
            <tbody>
              <tr v-for="forecast in sortedForecasts" :key="forecast.id">
                <td><strong>{{ forecast.item_sku }}</strong></td>
                <td>{{ forecast.item_name }}</td>
                <td>{{ forecast.current_demand }}</td>
                <td><strong>{{ forecast.forecasted_demand }}</strong></td>
                <td>
                  <span :style="{ color: getChangeColor(forecast) }">
                    {{ getChangePercent(forecast) }}%
                  </span>
                </td>
                <td>
                  <span :class="['badge', forecast.trend]">
                    {{ t(`trends.${forecast.trend}`) }}
                  </span>
                </td>
                <td>{{ translatePeriod(forecast.period) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, watch, computed } from 'vue'
import { api } from '../api'
import { useFilters } from '../composables/useFilters'
import { useI18n } from '../composables/useI18n'
import { useTableSort } from '../composables/useTableSort'
import SortableTh from '../components/SortableTh.vue'

export default {
  name: 'Demand',
  components: {
    SortableTh
  },
  setup() {
    const { t } = useI18n()
    const loading = ref(true)
    const error = ref(null)
    const allForecasts = ref([])
    const inventoryItems = ref([])

    // Use shared filters
    const { selectedLocation, selectedCategory, getCurrentFilters } = useFilters()

    // Filter forecasts based on inventory filters
    const forecasts = computed(() => {
      if (selectedLocation.value === 'all' && selectedCategory.value === 'all') {
        return allForecasts.value
      }

      // Get SKUs of items that match the filters
      const validSkus = new Set(inventoryItems.value.map(item => item.sku))
      return allForecasts.value.filter(f => validSkus.has(f.item_sku))
    })

    const loadForecasts = async () => {
      try {
        loading.value = true
        const filters = getCurrentFilters()

        const [forecastsData, inventoryData] = await Promise.all([
          api.getDemandForecasts(),
          api.getInventory({
            warehouse: filters.warehouse,
            category: filters.category
          })
        ])

        allForecasts.value = forecastsData
        inventoryItems.value = inventoryData
      } catch (err) {
        error.value = 'Failed to load demand forecasts: ' + err.message
      } finally {
        loading.value = false
      }
    }

    // Watch for filter changes and reload data
    watch([selectedLocation, selectedCategory], () => {
      loadForecasts()
    })

    // Click-to-sort layered on top of the filtered forecasts.
    // When sort is "off", applySort returns forecasts untouched.
    const { sortKey, sortDir, toggleSort, applySort } = useTableSort()

    const sortAccessors = {
      sku: (f) => f.item_sku,
      // i18n/text column: sort on the raw item name for stable ordering
      itemName: (f) => f.item_name,
      currentDemand: (f) => f.current_demand,
      forecastedDemand: (f) => f.forecasted_demand,
      // Derived: fractional change between current and forecasted demand
      change: (f) => (f.forecasted_demand - f.current_demand) / f.current_demand,
      // Sort on the raw trend key, not the translated label
      trend: (f) => f.trend,
      // Sort on the raw period string, not the translated label
      period: (f) => f.period
    }

    const sortedForecasts = computed(() => applySort(forecasts.value, sortAccessors))

    const getForecastsByTrend = (trend) => {
      return forecasts.value.filter(f => f.trend === trend)
    }

    const getChangePercent = (forecast) => {
      // Guard against divide-by-zero: with no current demand the percent change is
      // undefined (would be Infinity/NaN), so surface "N/A" instead of a bad number.
      if (!forecast.current_demand) {
        return 'N/A'
      }
      const change = ((forecast.forecasted_demand - forecast.current_demand) / forecast.current_demand * 100).toFixed(1)
      return change > 0 ? `+${change}` : change
    }

    // Trend badge and change color both read from forecast.trend (the same source the
    // trend cards group by), so the label and the color can never contradict each other.
    const trendColors = {
      increasing: '#10b981', // Green
      stable: '#3b82f6',     // Blue
      decreasing: '#ef4444'  // Red
    }

    const getChangeColor = (forecast) => {
      return trendColors[forecast.trend] || '#3b82f6'
    }

    const translatePeriod = (period) => {
      // Period values like "Next 3 months", "Q1 2025", "30 days", etc.
      const { currentLocale } = useI18n()
      if (currentLocale.value === 'ja') {
        return period
          .replace(/Next\s+/i, '次の')
          .replace(/\s+months/i, 'か月')
          .replace(/\s+month/i, 'か月')
          .replace(/\s+days/i, '日間')
          .replace(/\s+day/i, '日')
          .replace('Q1', '第1四半期')
          .replace('Q2', '第2四半期')
          .replace('Q3', '第3四半期')
          .replace('Q4', '第4四半期')
      }
      return period
    }

    onMounted(loadForecasts)

    return {
      t,
      loading,
      error,
      forecasts,
      sortedForecasts,
      sortKey,
      sortDir,
      toggleSort,
      getForecastsByTrend,
      getChangePercent,
      getChangeColor,
      translatePeriod
    }
  }
}
</script>

<style scoped>
.demand-trend-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
  gap: 1.5rem;
  margin-bottom: 2rem;
}

.trend-card {
  background: white;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  padding: 1.5rem;
  transition: all 0.2s ease;
}

.trend-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
}

.increasing-card {
  border-left: 4px solid #10b981;
}

.stable-card {
  border-left: 4px solid #3b82f6;
}

.decreasing-card {
  border-left: 4px solid #ef4444;
}

.trend-header {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-bottom: 1rem;
  padding-bottom: 1rem;
  border-bottom: 1px solid #f1f5f9;
}

.trend-icon {
  width: 48px;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 10px;
  font-size: 1.75rem;
  font-weight: 700;
  flex-shrink: 0;
}

.increasing-card .trend-icon {
  background: #d1fae5;
  color: #059669;
}

.stable-card .trend-icon {
  background: #dbeafe;
  color: #2563eb;
}

.decreasing-card .trend-icon {
  background: #fee2e2;
  color: #dc2626;
}

.trend-label {
  font-size: 0.875rem;
  font-weight: 600;
  color: #64748b;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.trend-count {
  font-size: 1.5rem;
  font-weight: 700;
  color: #0f172a;
  margin-top: 0.25rem;
}

.trend-items {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.trend-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.5rem 0.75rem;
  background: #f8fafc;
  border-radius: 6px;
  transition: background 0.2s;
}

.trend-item:hover {
  background: #f1f5f9;
}

.item-name {
  font-size: 0.875rem;
  color: #0f172a;
  font-weight: 500;
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  margin-right: 1rem;
}

.item-change {
  font-size: 0.813rem;
  font-weight: 700;
  flex-shrink: 0;
}

.increasing-card .item-change {
  color: #059669;
}

.stable-card .item-change {
  color: #3b82f6;
}

.decreasing-card .item-change {
  color: #dc2626;
}

.item-change.neutral {
  color: #64748b;
}

.more-items {
  font-size: 0.813rem;
  color: #64748b;
  font-style: italic;
  text-align: center;
  padding: 0.5rem;
}
</style>
