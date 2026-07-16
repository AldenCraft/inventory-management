<template>
  <div class="backlog">
    <div class="page-header">
      <h2>Backlog Management</h2>
      <p>Track and resolve inventory shortages</p>
    </div>

    <div v-if="loading" class="loading">Loading backlog...</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else>
      <div class="stats-grid">
        <div class="stat-card danger">
          <div class="stat-label">High Priority</div>
          <div class="stat-value">{{ getBacklogByPriority('high').length }}</div>
        </div>
        <div class="stat-card warning">
          <div class="stat-label">Medium Priority</div>
          <div class="stat-value">{{ getBacklogByPriority('medium').length }}</div>
        </div>
        <div class="stat-card info">
          <div class="stat-label">Low Priority</div>
          <div class="stat-value">{{ getBacklogByPriority('low').length }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">Total Backlog Items</div>
          <div class="stat-value">{{ backlogItems.length }}</div>
        </div>
      </div>

      <div class="card">
        <div class="card-header">
          <h3 class="card-title">Backlog Items</h3>
        </div>
        <div v-if="backlogItems.length === 0" style="padding: 3rem; text-align: center;">
          <p style="font-size: 1.125rem; color: #10b981; font-weight: 600;">
            ✓ No backlog items - all orders can be fulfilled!
          </p>
        </div>
        <div v-else class="table-container">
          <table>
            <thead>
              <tr>
                <SortableTh column-key="orderId" label="Order ID" :sort-key="sortKey" :sort-dir="sortDir" @sort="toggleSort" />
                <SortableTh column-key="sku" label="SKU" :sort-key="sortKey" :sort-dir="sortDir" @sort="toggleSort" />
                <SortableTh column-key="itemName" label="Item Name" :sort-key="sortKey" :sort-dir="sortDir" @sort="toggleSort" />
                <SortableTh column-key="quantityNeeded" label="Quantity Needed" :sort-key="sortKey" :sort-dir="sortDir" @sort="toggleSort" />
                <SortableTh column-key="quantityAvailable" label="Quantity Available" :sort-key="sortKey" :sort-dir="sortDir" @sort="toggleSort" />
                <SortableTh column-key="shortage" label="Shortage" :sort-key="sortKey" :sort-dir="sortDir" @sort="toggleSort" />
                <SortableTh column-key="daysDelayed" label="Days Delayed" :sort-key="sortKey" :sort-dir="sortDir" @sort="toggleSort" />
                <SortableTh column-key="priority" label="Priority" :sort-key="sortKey" :sort-dir="sortDir" @sort="toggleSort" />
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
                    {{ item.quantity_needed - item.quantity_available }} units short
                  </span>
                </td>
                <td>
                  <span :style="{ color: item.days_delayed > 7 ? '#ef4444' : '#f59e0b' }">
                    {{ item.days_delayed }} days
                  </span>
                </td>
                <td>
                  <span :class="['badge', item.priority]">
                    {{ item.priority }}
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
import { useTableSort } from '../composables/useTableSort'
import SortableTh from '../components/SortableTh.vue'

export default {
  name: 'Backlog',
  components: {
    SortableTh
  },
  setup() {
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

    // Watch for filter changes and reload data
    watch([selectedLocation, selectedCategory], () => {
      loadBacklog()
    })

    onMounted(loadBacklog)

    return {
      loading,
      error,
      backlogItems,
      sortedBacklogItems,
      sortKey,
      sortDir,
      toggleSort,
      getBacklogByPriority
    }
  }
}
</script>
