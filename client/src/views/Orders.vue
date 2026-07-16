<template>
  <div class="orders">
    <div class="page-header">
      <h2>{{ t('orders.title') }}</h2>
      <p>{{ t('orders.description') }}</p>
    </div>

    <div v-if="loading" class="loading">{{ t('common.loading') }}</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else>
      <div class="stats-grid">
        <div class="stat-card success">
          <div class="stat-label">{{ t('status.delivered') }}</div>
          <div class="stat-value">{{ getOrdersByStatus('Delivered').length }}</div>
        </div>
        <div class="stat-card info">
          <div class="stat-label">{{ t('status.shipped') }}</div>
          <div class="stat-value">{{ getOrdersByStatus('Shipped').length }}</div>
        </div>
        <div class="stat-card warning">
          <div class="stat-label">{{ t('status.processing') }}</div>
          <div class="stat-value">{{ getOrdersByStatus('Processing').length }}</div>
        </div>
        <div class="stat-card danger">
          <div class="stat-label">{{ t('status.backordered') }}</div>
          <div class="stat-value">{{ getOrdersByStatus('Backordered').length }}</div>
        </div>
      </div>

      <!-- Independent of the global filter (see loadSubmittedOrders): submitted orders
           carry warehouse=null/category=null and a 2026 order_date, so they must never
           depend on the warehouse/category/month/status selection to stay visible. -->
      <div class="card" v-if="submittedOrders.length">
        <div class="card-header">
          <h3 class="card-title">{{ t('orders.submittedTitle') }} ({{ submittedOrders.length }})</h3>
        </div>
        <div class="table-container">
          <table class="orders-table">
            <thead>
              <tr>
                <th>{{ t('orders.table.orderNumber') }}</th>
                <th>{{ t('orders.table.items') }}</th>
                <th>{{ t('orders.table.orderDate') }}</th>
                <th>{{ t('orders.table.expectedDelivery') }}</th>
                <th>{{ t('orders.table.leadTime') }}</th>
                <th>{{ t('orders.table.totalValue') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="order in submittedOrders" :key="order.id">
                <td><strong>{{ order.order_number }}</strong></td>
                <td>{{ t('orders.itemsCount', { count: order.items.length }) }}</td>
                <td>{{ formatDate(order.order_date) }}</td>
                <td>{{ formatDate(order.expected_delivery) }}</td>
                <td>{{ t('restocking.days', { count: submittedLeadTime(order) }) }}</td>
                <td><strong>{{ formatCurrency(order.total_value) }}</strong></td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <div class="card">
        <div class="card-header">
          <h3 class="card-title">{{ t('orders.allOrders') }} ({{ otherOrders.length }})</h3>
        </div>
        <div class="table-container">
          <table class="orders-table">
            <thead>
              <tr>
                <SortableTh class="col-order-number" column-key="orderNumber" :label="t('orders.table.orderNumber')" :sort-key="sortKey" :sort-dir="sortDir" @sort="toggleSort" />
                <SortableTh class="col-customer" column-key="customer" :label="t('orders.table.customer')" :sort-key="sortKey" :sort-dir="sortDir" @sort="toggleSort" />
                <SortableTh class="col-items" column-key="items" :label="t('orders.table.items')" :sort-key="sortKey" :sort-dir="sortDir" @sort="toggleSort" />
                <SortableTh class="col-status" column-key="status" :label="t('orders.table.status')" :sort-key="sortKey" :sort-dir="sortDir" @sort="toggleSort" />
                <SortableTh class="col-date" column-key="orderDate" :label="t('orders.table.orderDate')" :sort-key="sortKey" :sort-dir="sortDir" @sort="toggleSort" />
                <SortableTh class="col-date" column-key="expectedDelivery" :label="t('orders.table.expectedDelivery')" :sort-key="sortKey" :sort-dir="sortDir" @sort="toggleSort" />
                <SortableTh class="col-value" column-key="totalValue" :label="t('orders.table.totalValue')" :sort-key="sortKey" :sort-dir="sortDir" @sort="toggleSort" />
              </tr>
            </thead>
            <tbody>
              <tr v-for="order in sortedOrders" :key="order._rowKey">
                <td class="col-order-number"><strong>{{ order.order_number }}</strong></td>
                <td class="col-customer">{{ translateCustomerName(order.customer) }}</td>
                <td class="col-items">
                  <details class="items-details">
                    <summary class="items-summary">
                      {{ t('orders.itemsCount', { count: order.items.length }) }}
                    </summary>
                    <div class="items-dropdown">
                      <div v-for="item in order.items" :key="item.sku" class="item-entry">
                        <span class="item-name">{{ translateProductName(item.name) }}</span>
                        <span class="item-meta">{{ t('orders.quantity') }}: {{ item.quantity }} @ {{ formatUnitPrice(item.unit_price) }}</span>
                      </div>
                    </div>
                  </details>
                </td>
                <td class="col-status">
                  <span :class="['badge', getOrderStatusClass(order.status)]">
                    {{ t(`status.${order.status.toLowerCase()}`) }}
                  </span>
                </td>
                <td class="col-date">{{ formatDate(order.order_date) }}</td>
                <td class="col-date">{{ formatDate(order.expected_delivery) }}</td>
                <td class="col-value"><strong>{{ formatCurrency(order.total_value) }}</strong></td>
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
import { formatCurrency as formatCurrencyUtil, formatCurrencyWithDecimals } from '../utils/currency'
import { useTableSort } from '../composables/useTableSort'
import SortableTh from '../components/SortableTh.vue'

export default {
  name: 'Orders',
  components: {
    SortableTh
  },
  setup() {
    const { t, currentLocale, currentCurrency, translateProductName, translateCustomerName } = useI18n()

    // Convert USD figures to the active currency (×150 for JPY) instead of just
    // prepending a ¥ over a raw USD number. Whole-value totals use formatCurrency;
    // per-unit prices keep 2 decimals via formatCurrencyWithDecimals.
    const formatCurrency = (value) => formatCurrencyUtil(value, currentCurrency.value)
    const formatUnitPrice = (value) => formatCurrencyWithDecimals(value, currentCurrency.value, 2)

    const loading = ref(true)
    const error = ref(null)
    const orders = ref([])
    const submittedOrders = ref([])

    // Use shared filters
    const {
      selectedPeriod,
      selectedLocation,
      selectedCategory,
      selectedStatus,
      getCurrentFilters
    } = useFilters()

    const loadOrders = async () => {
      try {
        loading.value = true
        const filters = getCurrentFilters()
        const fetchedOrders = await api.getOrders(filters)

        // Sort orders by order_date (earliest first)
        // The source data has duplicate `id` values, so we stamp a stable, unique
        // _rowKey once here. applySort reorders the same object refs, so each row
        // keeps its key across asc/desc/off and Vue patches rows correctly.
        orders.value = fetchedOrders
          .sort((a, b) => {
            // Validate before comparing so a missing/malformed order_date can't produce a
            // NaN comparison and an unstable sort; invalid dates sort to the start.
            const timeA = new Date(a.order_date).getTime()
            const timeB = new Date(b.order_date).getTime()
            const safeA = isNaN(timeA) ? 0 : timeA
            const safeB = isNaN(timeB) ? 0 : timeB
            return safeA - safeB
          })
          .map((o, i) => ({ ...o, _rowKey: i }))
      } catch (err) {
        error.value = 'Failed to load orders: ' + err.message
      } finally {
        loading.value = false
      }
    }

    // Loads submitted orders on their own, bypassing the shared filter composable.
    // Submitted orders (from the Restocking flow) have warehouse=null, category=null,
    // and a 2026 order_date, so filtering by the global warehouse/category/month/status
    // selection could blank the section even though it has nothing to do with those
    // filters. Only the status param is sent, and this is never added to the filter watch.
    const loadSubmittedOrders = async () => {
      try {
        submittedOrders.value = await api.getOrders({ status: 'Submitted' })
      } catch (err) {
        // non-fatal: the main table still renders
        console.error('Failed to load submitted orders:', err)
      }
    }

    // Watch for filter changes and reload data
    watch([selectedPeriod, selectedLocation, selectedCategory, selectedStatus], () => {
      loadOrders()
    })

    const getOrdersByStatus = (status) => {
      return orders.value.filter(order => order.status === status)
    }

    // Submitted orders get their own card above, so exclude them here to avoid
    // double-listing when the status filter is "all".
    const otherOrders = computed(() =>
      orders.value.filter(o => o.status !== 'Submitted')
    )

    const getOrderStatusClass = (status) => {
      const statusMap = {
        'Delivered': 'success',
        'Shipped': 'info',
        'Processing': 'warning',
        'Backordered': 'danger',
        'Submitted': 'info'
      }
      return statusMap[status] || 'info'
    }

    const formatDate = (dateString) => {
      if (!dateString) return '-'
      const date = new Date(dateString)
      // Guard against invalid/malformed dates so the UI shows a placeholder instead of
      // "Invalid Date" (per the repo date rule).
      if (isNaN(date.getTime())) return '-'
      const locale = currentLocale.value === 'ja' ? 'ja-JP' : 'en-US'
      return date.toLocaleDateString(locale, {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
      })
    }

    // Lead time in whole days between order and expected delivery, for the
    // Submitted Orders table. Dates are validated first per repo convention.
    const submittedLeadTime = (order) => {
      const start = new Date(order.order_date)
      const end = new Date(order.expected_delivery)
      if (isNaN(start.getTime()) || isNaN(end.getTime())) return '-'
      return Math.round((end - start) / 86400000) // ms per day
    }

    // Click-to-sort layered on top of the date-ascending default order.
    // When sort is "off", applySort returns orders untouched.
    const { sortKey, sortDir, toggleSort, applySort } = useTableSort()

    const sortAccessors = {
      orderNumber: (o) => o.order_number,
      // i18n column: sort on the raw customer name, not the translated label
      customer: (o) => o.customer,
      // Derived: sort by number of line items
      items: (o) => o.items.length,
      status: (o) => o.status,
      // ISO date strings compare chronologically as strings
      orderDate: (o) => o.order_date,
      expectedDelivery: (o) => o.expected_delivery,
      totalValue: (o) => o.total_value
    }

    // Sort over the Submitted-excluded set so All Orders stays both sorted and
    // free of rows already shown in the Submitted Orders card above.
    const sortedOrders = computed(() => applySort(otherOrders.value, sortAccessors))

    onMounted(() => {
      loadOrders()
      loadSubmittedOrders()
    })

    return {
      t,
      loading,
      error,
      orders,
      otherOrders,
      submittedOrders,
      sortedOrders,
      sortKey,
      sortDir,
      toggleSort,
      getOrdersByStatus,
      getOrderStatusClass,
      formatDate,
      submittedLeadTime,
      formatCurrency,
      formatUnitPrice,
      translateProductName,
      translateCustomerName
    }
  }
}
</script>

<style scoped>
/* Fixed table layout to prevent column shifting */
.orders-table {
  table-layout: fixed;
  width: 100%;
}

/* Column widths */
.col-order-number {
  width: 130px;
}

.col-customer {
  width: 180px;
}

.col-items {
  width: 200px;
}

.col-status {
  width: 130px;
}

.col-date {
  width: 140px;
}

.col-value {
  width: 120px;
}

/* Items details styling */
.items-details {
  position: relative;
}

.items-summary {
  cursor: pointer;
  color: #3b82f6;
  font-weight: 500;
  list-style: none;
  user-select: none;
  display: inline-block;
}

.items-summary::-webkit-details-marker {
  display: none;
}

.items-summary::before {
  content: '▶';
  display: inline-block;
  margin-right: 0.375rem;
  font-size: 0.75rem;
  transition: transform 0.2s;
}

.items-details[open] .items-summary::before {
  transform: rotate(90deg);
}

.items-summary:hover {
  color: #2563eb;
  text-decoration: underline;
}

/* Dropdown container */
.items-dropdown {
  position: absolute;
  top: 100%;
  left: 0;
  margin-top: 0.5rem;
  background: white;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
  padding: 0.75rem;
  z-index: 10;
  min-width: 300px;
  max-width: 400px;
}

.item-entry {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  padding: 0.5rem;
  border-bottom: 1px solid #f1f5f9;
}

.item-entry:last-child {
  border-bottom: none;
}

.item-name {
  font-size: 0.875rem;
  font-weight: 500;
  color: #0f172a;
}

.item-meta {
  font-size: 0.813rem;
  color: #64748b;
}
</style>
