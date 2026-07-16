<template>
  <div class="backlog">
    <div class="page-header">
      <h2>{{ t('dashboard.backlog.title') }}</h2>
      <p>{{ t('dashboard.backlog.description') }}</p>
    </div>

    <div v-if="loading" class="loading">{{ t('common.loading') }}</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else>
      <div class="stats-grid">
        <div class="stat-card danger">
          <div class="stat-label">{{ t('dashboard.backlog.highPriority') }}</div>
          <div class="stat-value">{{ getBacklogByPriority('high').length }}</div>
        </div>
        <div class="stat-card warning">
          <div class="stat-label">{{ t('dashboard.backlog.mediumPriority') }}</div>
          <div class="stat-value">{{ getBacklogByPriority('medium').length }}</div>
        </div>
        <div class="stat-card info">
          <div class="stat-label">{{ t('dashboard.backlog.lowPriority') }}</div>
          <div class="stat-value">{{ getBacklogByPriority('low').length }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">{{ t('dashboard.backlog.totalBacklogItems') }}</div>
          <div class="stat-value">{{ backlogItems.length }}</div>
        </div>
      </div>

      <div class="card">
        <div class="card-header">
          <h3 class="card-title">{{ t('dashboard.backlog.backlogItems') }}</h3>
        </div>
        <div v-if="backlogItems.length === 0" style="padding: 3rem; text-align: center;">
          <p style="font-size: 1.125rem; color: #10b981; font-weight: 600;">
            ✓ {{ t('dashboard.backlog.noBacklogItems') }}
          </p>
        </div>
        <div v-else class="table-container">
          <table>
            <thead>
              <tr>
                <SortableTh column-key="orderId" :label="t('dashboard.inventoryShortages.orderId')" :sort-key="sortKey" :sort-dir="sortDir" @sort="toggleSort" />
                <SortableTh column-key="sku" :label="t('dashboard.inventoryShortages.sku')" :sort-key="sortKey" :sort-dir="sortDir" @sort="toggleSort" />
                <SortableTh column-key="itemName" :label="t('dashboard.inventoryShortages.itemName')" :sort-key="sortKey" :sort-dir="sortDir" @sort="toggleSort" />
                <SortableTh column-key="quantityNeeded" :label="t('dashboard.inventoryShortages.quantityNeeded')" :sort-key="sortKey" :sort-dir="sortDir" @sort="toggleSort" />
                <SortableTh column-key="quantityAvailable" :label="t('dashboard.inventoryShortages.quantityAvailable')" :sort-key="sortKey" :sort-dir="sortDir" @sort="toggleSort" />
                <SortableTh column-key="shortage" :label="t('dashboard.inventoryShortages.shortage')" :sort-key="sortKey" :sort-dir="sortDir" @sort="toggleSort" />
                <SortableTh column-key="daysDelayed" :label="t('dashboard.inventoryShortages.daysDelayed')" :sort-key="sortKey" :sort-dir="sortDir" @sort="toggleSort" />
                <SortableTh column-key="priority" :label="t('dashboard.inventoryShortages.priority')" :sort-key="sortKey" :sort-dir="sortDir" @sort="toggleSort" />
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in sortedBacklogItems" :key="item.id">
                <td><strong>{{ item.order_id }}</strong></td>
                <td><strong>{{ item.item_sku }}</strong></td>
                <td>{{ item.item_name }}</td>
                <td>{{ item.quantity_needed }}</td>
                <td>{{ item.quantity_available }}</td>
                <td>
                  <span class="badge danger">
                    {{ item.quantity_needed - item.quantity_available }} {{ t('dashboard.inventoryShortages.unitsShort') }}
                  </span>
                </td>
                <td>
                  <span :style="{ color: item.days_delayed > 7 ? '#ef4444' : '#f59e0b' }">
                    {{ item.days_delayed }} {{ t('dashboard.inventoryShortages.days') }}
                  </span>
                </td>
                <td>
                  <span :class="['badge', item.priority]">
                    {{ translatePriority(item.priority) }}
                  </span>
                </td>
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
  name: 'Backlog',
  components: {
    SortableTh
  },
  setup() {
    const { t } = useI18n()

    const loading = ref(true)
    const error = ref(null)
    const allBacklogItems = ref([])
    const inventoryItems = ref([])

    // Use shared filters
    const { selectedLocation, selectedCategory, getCurrentFilters } = useFilters()

    // Filter backlog based on inventory filters
    const backlogItems = computed(() => {
      if (selectedLocation.value === 'all' && selectedCategory.value === 'all') {
        return allBacklogItems.value
      }

      // Get SKUs of items that match the filters
      const validSkus = new Set(inventoryItems.value.map(item => item.sku))
      return allBacklogItems.value.filter(b => validSkus.has(b.item_sku))
    })

    const loadBacklog = async () => {
      try {
        loading.value = true
        const filters = getCurrentFilters()

        const [backlogData, inventoryData] = await Promise.all([
          api.getBacklog(),
          api.getInventory({
            warehouse: filters.warehouse,
            category: filters.category
          })
        ])

        allBacklogItems.value = backlogData
        inventoryItems.value = inventoryData
      } catch (err) {
        error.value = 'Failed to load backlog: ' + err.message
      } finally {
        loading.value = false
      }
    }

    // Click-to-sort layered on top of the filtered backlog list.
    // When sort is "off", applySort returns backlogItems untouched.
    const { sortKey, sortDir, toggleSort, applySort } = useTableSort()

    const sortAccessors = {
      orderId: (i) => i.order_id,
      sku: (i) => i.item_sku,
      itemName: (i) => i.item_name,
      quantityNeeded: (i) => i.quantity_needed,
      quantityAvailable: (i) => i.quantity_available,
      // Derived: units short = needed - available
      shortage: (i) => i.quantity_needed - i.quantity_available,
      daysDelayed: (i) => i.days_delayed,
      priority: (i) => i.priority
    }

    const sortedBacklogItems = computed(() => applySort(backlogItems.value, sortAccessors))

    const getBacklogByPriority = (priority) => {
      return backlogItems.value.filter(item => item.priority === priority)
    }

    // Translate the raw priority value (e.g. "high") into the localized label.
    // Handles both lowercase (API) and capitalized forms, mirroring Dashboard.vue.
    const translatePriority = (priority) => {
      const priorityMap = {
        'high': t('priority.high'),
        'medium': t('priority.medium'),
        'low': t('priority.low'),
        'High': t('priority.high'),
        'Medium': t('priority.medium'),
        'Low': t('priority.low')
      }
      return priorityMap[priority] || priority
    }

    // Watch for filter changes and reload data
    watch([selectedLocation, selectedCategory], () => {
      loadBacklog()
    })

    onMounted(loadBacklog)

    return {
      t,
      loading,
      error,
      backlogItems,
      sortedBacklogItems,
      sortKey,
      sortDir,
      toggleSort,
      getBacklogByPriority,
      translatePriority
    }
  }
}
</script>
