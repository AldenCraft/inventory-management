<template>
  <div class="restocking">
    <div class="page-header">
      <h2>{{ t('restocking.title') }}</h2>
      <p>{{ t('restocking.description') }}</p>
    </div>

    <div class="card budget-card">
      <label class="budget-label" for="budget-slider">
        {{ t('restocking.budgetLabel') }}: <strong>{{ currencySymbol }}{{ budget.toLocaleString() }}</strong>
      </label>
      <input
        id="budget-slider"
        type="range"
        min="0"
        max="5000"
        step="100"
        v-model.number="budget"
        class="budget-slider"
      />
    </div>

    <div v-if="loading" class="loading">{{ t('common.loading') }}</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else>
      <div class="card">
        <div class="card-header">
          <h3 class="card-title">{{ t('restocking.recommendedTitle') }}</h3>
        </div>
        <div v-if="recommendations.length === 0" class="empty">
          {{ t('restocking.empty') }}
        </div>
        <div v-else class="table-container">
          <table class="restock-table">
            <thead>
              <tr>
                <th>{{ t('restocking.table.item') }}</th>
                <th>{{ t('restocking.table.sku') }}</th>
                <th>{{ t('restocking.table.trend') }}</th>
                <th>{{ t('restocking.table.unitCost') }}</th>
                <th>{{ t('restocking.table.quantity') }}</th>
                <th>{{ t('restocking.table.lineCost') }}</th>
                <th>{{ t('restocking.table.leadTime') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="rec in recommendations" :key="rec.item_sku">
                <td>{{ rec.item_name }}</td>
                <td>{{ rec.item_sku }}</td>
                <td><span :class="['badge', rec.trend]">{{ t(`trends.${rec.trend}`) }}</span></td>
                <td>{{ currencySymbol }}{{ rec.unit_cost.toFixed(2) }}</td>
                <td>{{ rec.recommended_quantity }}</td>
                <td>{{ currencySymbol }}{{ rec.line_cost.toLocaleString() }}</td>
                <td>{{ t('restocking.days', { count: rec.lead_time_days }) }}</td>
              </tr>
            </tbody>
          </table>
        </div>

        <div class="restock-summary">
          <span>{{ t('restocking.totalCost') }}: <strong>{{ currencySymbol }}{{ totalCost.toLocaleString() }}</strong></span>
          <span>{{ t('restocking.remaining') }}: <strong>{{ currencySymbol }}{{ remaining.toLocaleString() }}</strong></span>
        </div>

        <button
          class="place-order-btn"
          :disabled="recommendations.length === 0 || placing"
          @click="placeOrder"
        >
          {{ placing ? t('restocking.placing') : t('restocking.placeOrder') }}
        </button>
        <p v-if="successMessage" class="success">
          {{ successMessage }}
          <router-link to="/orders">{{ t('restocking.viewInOrders') }}</router-link>
        </p>
        <p v-if="placeError" class="error place-error">{{ placeError }}</p>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, watch, onMounted } from 'vue'
import { api } from '../api'
import { useI18n } from '../composables/useI18n'

export default {
  name: 'Restocking',
  setup() {
    const { t, currentCurrency } = useI18n()

    // currencySymbol isn't exposed directly by useI18n; derive it the same way Orders.vue does.
    const currencySymbol = computed(() => {
      return currentCurrency.value === 'JPY' ? '¥' : '$'
    })

    const budget = ref(2000)
    const recommendations = ref([])
    const totalCost = ref(0)
    const remaining = ref(0)
    const loading = ref(true)
    const error = ref(null)
    const placing = ref(false)
    const successMessage = ref('')
    // Separate from `error`: a failed order submission must not flip the
    // v-if/v-else-if/v-else below and wipe out the recommendations table.
    const placeError = ref(null)

    let debounceTimer = null

    const loadRecommendations = async () => {
      try {
        loading.value = true
        error.value = null
        const data = await api.getRestockingRecommendations(budget.value)
        recommendations.value = data.recommendations
        totalCost.value = data.total_cost
        remaining.value = data.remaining_budget
      } catch (err) {
        error.value = 'Failed to load recommendations: ' + err.message
      } finally {
        loading.value = false
      }
    }

    // Debounce the slider so dragging doesn't fire a request on every intermediate value.
    watch(budget, () => {
      successMessage.value = ''
      clearTimeout(debounceTimer)
      debounceTimer = setTimeout(loadRecommendations, 250)
    })

    const placeOrder = async () => {
      try {
        placing.value = true
        placeError.value = null
        const items = recommendations.value.map(rec => ({
          item_sku: rec.item_sku,
          item_name: rec.item_name,
          quantity: rec.recommended_quantity,
          unit_cost: rec.unit_cost,
          lead_time_days: rec.lead_time_days
        }))
        const order = await api.placeRestockingOrder(items)
        successMessage.value = t('restocking.success', { orderNumber: order.order_number })
        placeError.value = null
      } catch (err) {
        placeError.value = 'Failed to place order: ' + err.message
      } finally {
        placing.value = false
      }
    }

    onMounted(loadRecommendations)

    return {
      t,
      currencySymbol,
      budget,
      recommendations,
      totalCost,
      remaining,
      loading,
      error,
      placing,
      successMessage,
      placeError,
      placeOrder
    }
  }
}
</script>

<style scoped>
.budget-card {
  padding: 1.5rem;
  margin-bottom: 1.5rem;
}

.budget-label {
  display: block;
  margin-bottom: 0.75rem;
  font-size: 0.938rem;
  color: #0f172a;
}

.budget-slider {
  width: 100%;
  accent-color: #2563eb;
}

.restock-summary {
  display: flex;
  gap: 2rem;
  margin: 1rem 0;
  font-size: 0.938rem;
  color: #334155;
}

.place-order-btn {
  background: #0f172a;
  color: #fff;
  border: none;
  padding: 0.625rem 1.25rem;
  border-radius: 6px;
  font-size: 0.938rem;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.2s ease;
}

.place-order-btn:hover:not(:disabled) {
  background: #1e293b;
}

.place-order-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.success {
  color: #059669;
  margin-top: 0.75rem;
  font-size: 0.938rem;
}

.success a {
  color: #2563eb;
  font-weight: 500;
  margin-left: 0.25rem;
}

.empty {
  color: #64748b;
  padding: 1.5rem 0;
  text-align: center;
}

.place-error {
  margin-top: 0.75rem;
}
</style>
