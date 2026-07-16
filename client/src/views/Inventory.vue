<template>
  <div class="inventory">
    <div class="page-header">
      <h2>{{ t('inventory.title') }}</h2>
      <p>{{ t('inventory.description') }}</p>
    </div>

    <div v-if="loading" class="loading">{{ t('common.loading') }}</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else>
      <div class="card">
        <div class="card-header">
          <h3 class="card-title">{{ t('inventory.stockLevels') }} ({{ filteredItems.length }} {{ t('inventory.skus') }})</h3>
          <div class="search-box">
            <svg class="search-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
              <path fill-rule="evenodd" d="M8 4a4 4 0 100 8 4 4 0 000-8zM2 8a6 6 0 1110.89 3.476l4.817 4.817a1 1 0 01-1.414 1.414l-4.816-4.816A6 6 0 012 8z" clip-rule="evenodd" />
            </svg>
            <input
              v-model="searchQuery"
              type="text"
              :placeholder="t('inventory.searchPlaceholder')"
              class="search-input"
            />
            <button
              v-if="searchQuery"
              @click="searchQuery = ''"
              class="clear-search"
              :title="t('inventory.clearSearch')"
            >
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd" />
              </svg>
            </button>
          </div>
        </div>
        <div class="table-container">
          <table>
            <thead>
              <tr>
                <SortableTh column-key="sku" :label="t('inventory.table.sku')" :sort-key="sortKey" :sort-dir="sortDir" @sort="toggleSort" />
                <SortableTh column-key="name" :label="t('inventory.table.itemName')" :sort-key="sortKey" :sort-dir="sortDir" @sort="toggleSort" />
                <SortableTh column-key="category" :label="t('inventory.table.category')" :sort-key="sortKey" :sort-dir="sortDir" @sort="toggleSort" />
                <SortableTh column-key="quantityOnHand" :label="t('inventory.table.quantityOnHand')" :sort-key="sortKey" :sort-dir="sortDir" @sort="toggleSort" />
                <SortableTh column-key="reorderPoint" :label="t('inventory.table.reorderPoint')" :sort-key="sortKey" :sort-dir="sortDir" @sort="toggleSort" />
                <SortableTh column-key="unitCost" :label="t('inventory.table.unitCost')" :sort-key="sortKey" :sort-dir="sortDir" @sort="toggleSort" />
                <SortableTh column-key="totalValue" :label="t('inventory.table.totalValue')" :sort-key="sortKey" :sort-dir="sortDir" @sort="toggleSort" />
                <SortableTh column-key="location" :label="t('inventory.table.location')" :sort-key="sortKey" :sort-dir="sortDir" @sort="toggleSort" />
                <SortableTh column-key="status" :label="t('inventory.table.status')" :sort-key="sortKey" :sort-dir="sortDir" @sort="toggleSort" />
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="item in sortedItems"
                :key="item.id"
                class="clickable-row"
                role="button"
                tabindex="0"
                :aria-label="t('common.viewDetails')"
                @click="showItemDetail(item)"
                @keydown.enter="showItemDetail(item)"
                @keydown.space.prevent="showItemDetail(item)"
              >
                <td><strong>{{ item.sku }}</strong></td>
                <td>{{ translateProductName(item.name) }}</td>
                <td>{{ translateCategory(item.category) }}</td>
                <td><strong>{{ item.quantity_on_hand }}</strong></td>
                <td>{{ item.reorder_point }}</td>
                <td>{{ formatCurrency(item.unit_cost) }}</td>
                <td><strong>{{ formatCurrency(item.quantity_on_hand * item.unit_cost) }}</strong></td>
                <td>{{ translateWarehouse(item.location) }}</td>
                <td>
                  <span :class="['badge', getStockStatusClass(item)]">
                    {{ getStockStatus(item) }}
                  </span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <InventoryDetailModal
      :is-open="showItemModal"
      :inventory-item="selectedItem"
      @close="showItemModal = false"
    />
  </div>
</template>

<script>
import { ref, onMounted, watch, computed } from 'vue'
import { api } from '../api'
import { useFilters } from '../composables/useFilters'
import { useI18n } from '../composables/useI18n'
import { formatCurrencyWithDecimals } from '../utils/currency'
import { useStockStatus } from '../composables/useStockStatus'
import { useTableSort } from '../composables/useTableSort'
import InventoryDetailModal from '../components/InventoryDetailModal.vue'
import SortableTh from '../components/SortableTh.vue'

export default {
  name: 'Inventory',
  components: {
    InventoryDetailModal,
    SortableTh
  },
  setup() {
    const { t, currentCurrency, translateProductName, translateWarehouse } = useI18n()

    // Convert USD unit cost / total value to the active currency (×150 for JPY)
    // rather than prepending ¥ to a raw USD figure. Both columns keep 2 decimals.
    const formatCurrency = (value) => formatCurrencyWithDecimals(value, currentCurrency.value, 2)

    // Shared reorder-point classification (single source of truth). The per-item helper
    // forms are used for the table rows and for sort accessors below.
    const {
      getKey: getStockStatusKey,
      getLabel: getStockStatus,
      getClass: getStockStatusClass
    } = useStockStatus()

    const loading = ref(true)
    const error = ref(null)
    const items = ref([])
    const searchQuery = ref('')

    // Modal state
    const showItemModal = ref(false)
    const selectedItem = ref(null)

    // Use shared filters
    const { selectedLocation, selectedCategory, getCurrentFilters } = useFilters()

    // Stock status order for sorting (using status keys from useStockStatus)
    const STATUS_ORDER = { 'lowStock': 0, 'adequate': 1, 'inStock': 2 }

    // Computed property to filter items by search query and sort by stock status
    const filteredItems = computed(() => {
      let filtered = items.value

      // Apply search filter if query exists
      if (searchQuery.value.trim()) {
        const query = searchQuery.value.toLowerCase().trim()
        filtered = filtered.filter(item =>
          item.name.toLowerCase().includes(query)
        )
      }

      // Sort by stock status: Low Stock first, then Adequate, then In Stock
      // Always create a copy to avoid mutating the original array
      return filtered.slice().sort((a, b) => {
        const statusA = getStockStatusKey(a)
        const statusB = getStockStatusKey(b)
        return STATUS_ORDER[statusA] - STATUS_ORDER[statusB]
      })
    })

    // Click-to-sort layered on top of filteredItems. When sort is "off",
    // applySort returns filteredItems untouched, preserving the low-stock-first default.
    const { sortKey, sortDir, toggleSort, applySort } = useTableSort()

    const sortAccessors = {
      sku: (i) => i.sku,
      // i18n columns sort on the raw field, not the translated label, for stable ordering
      name: (i) => i.name,
      category: (i) => i.category,
      quantityOnHand: (i) => i.quantity_on_hand,
      reorderPoint: (i) => i.reorder_point,
      unitCost: (i) => i.unit_cost,
      // Derived: total value = quantity on hand * unit cost
      totalValue: (i) => i.quantity_on_hand * i.unit_cost,
      location: (i) => i.location,
      // Derived: rank by stock status so it matches the low-stock-first default ordering
      status: (i) => STATUS_ORDER[getStockStatusKey(i)]
    }

    const sortedItems = computed(() => applySort(filteredItems.value, sortAccessors))

    const loadInventory = async () => {
      try {
        loading.value = true
        const filters = getCurrentFilters()
        // Inventory doesn't support month/status filters, only warehouse and category
        items.value = await api.getInventory({
          warehouse: filters.warehouse,
          category: filters.category
        })
      } catch (err) {
        error.value = 'Failed to load inventory: ' + err.message
      } finally {
        loading.value = false
      }
    }

    // Watch for filter changes and reload data
    watch([selectedLocation, selectedCategory], () => {
      loadInventory()
    })

    const translateCategory = (category) => {
      const categoryMap = {
        'Circuit Boards': t('categories.circuitBoards'),
        'Sensors': t('categories.sensors'),
        'Actuators': t('categories.actuators'),
        'Controllers': t('categories.controllers'),
        'Power Supplies': t('categories.powerSupplies')
      }
      return categoryMap[category] || category
    }

    const showItemDetail = (item) => {
      selectedItem.value = item
      showItemModal.value = true
    }

    onMounted(loadInventory)

    return {
      t,
      loading,
      error,
      items,
      searchQuery,
      filteredItems,
      sortedItems,
      sortKey,
      sortDir,
      toggleSort,
      getStockStatus,
      getStockStatusClass,
      translateCategory,
      showItemModal,
      selectedItem,
      showItemDetail,
      formatCurrency,
      translateProductName,
      translateWarehouse
    }
  }
}
</script>

<style scoped>
.page-header {
  margin-bottom: 1.5rem;
}

.page-header h2 {
  margin-bottom: 0.25rem;
}

.page-header p {
  color: #64748b;
  font-size: 0.875rem;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 1.5rem;
  padding: 1.25rem 1.5rem;
  border-bottom: 1px solid #e2e8f0;
}

.card-title {
  font-size: 1rem;
  font-weight: 600;
  color: #0f172a;
  margin: 0;
}

.search-box {
  position: relative;
  display: flex;
  align-items: center;
  min-width: 300px;
}

.search-icon {
  position: absolute;
  left: 0.75rem;
  width: 18px;
  height: 18px;
  color: #94a3b8;
  pointer-events: none;
}

.search-input {
  width: 100%;
  padding: 0.5rem 2.5rem 0.5rem 2.5rem;
  border: 1px solid #cbd5e1;
  border-radius: 8px;
  font-size: 0.875rem;
  color: #0f172a;
  background: #f8fafc;
  transition: all 0.2s;
}

.search-input:focus {
  outline: none;
  border-color: #3b82f6;
  background: white;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.search-input::placeholder {
  color: #94a3b8;
}

.clear-search {
  position: absolute;
  right: 0.5rem;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0.25rem;
  background: transparent;
  border: none;
  border-radius: 4px;
  color: #94a3b8;
  cursor: pointer;
  transition: all 0.2s;
}

.clear-search:hover {
  background: #e2e8f0;
  color: #64748b;
}

.clear-search svg {
  width: 18px;
  height: 18px;
}

.loading,
.error {
  padding: 2rem;
  text-align: center;
  color: #64748b;
}

.error {
  color: #ef4444;
}

.clickable-row {
  cursor: pointer;
  transition: background-color 0.15s ease;
}

.clickable-row:hover {
  background: #eff6ff !important;
}

/* Keyboard focus indicator so the now-focusable rows show where focus is. */
.clickable-row:focus-visible {
  outline: 2px solid #2563eb;
  outline-offset: -2px;
  background: #eff6ff !important;
}
</style>
