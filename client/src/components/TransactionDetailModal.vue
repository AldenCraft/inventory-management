<template>
  <Teleport to="body">
    <Transition name="modal">
      <div v-if="isOpen && transaction" class="modal-overlay" @click="close">
        <div
          ref="modalRef"
          class="modal-container"
          role="dialog"
          aria-modal="true"
          aria-labelledby="transaction-modal-title"
          tabindex="-1"
          @click.stop
        >
          <div class="modal-header">
            <h3 id="transaction-modal-title" class="modal-title">{{ transaction.description }}</h3>
            <button class="close-button" :aria-label="t('common.close')" @click="close">
              <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
                <path d="M15 5L5 15M5 5L15 15" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
              </svg>
            </button>
          </div>

          <div class="modal-body">
            <!-- Amount headline, converted to the active currency via formatCurrency
                 (the whole point of this modal vs. the old fake 4-bucket breakdown). -->
            <div class="amount-headline">
              <div class="amount-label">{{ t('finance.transactions.amount') }}</div>
              <div class="amount-value">{{ formatCurrency(transaction.amount) }}</div>
            </div>

            <!-- Honest transaction fields: the real record, not a shoehorned cost split. -->
            <dl class="detail-grid">
              <div class="detail-row">
                <dt class="detail-label">{{ t('finance.transactions.id') }}</dt>
                <dd class="detail-value transaction-id">{{ transaction.id }}</dd>
              </div>
              <div class="detail-row">
                <dt class="detail-label">{{ t('finance.transactions.vendor') }}</dt>
                <dd class="detail-value">{{ transaction.vendor }}</dd>
              </div>
              <div class="detail-row">
                <dt class="detail-label">{{ t('finance.transactions.date') }}</dt>
                <dd class="detail-value">{{ formatDate(transaction.date) }}</dd>
              </div>
              <div class="detail-row">
                <dt class="detail-label">{{ t('orders.table.category') }}</dt>
                <dd class="detail-value">{{ translateCategory(transaction.category) }}</dd>
              </div>
              <div class="detail-row">
                <!-- No existing i18n key covers a transaction "type" label, and this view's
                     scope excludes editing the locale files, so the label is hardcoded
                     English. Adding a finance.transactions.type key later would localize it. -->
                <dt class="detail-label">Type</dt>
                <dd class="detail-value">{{ transaction.type }}</dd>
              </div>
            </dl>
          </div>

          <div class="modal-footer">
            <button class="btn-secondary" @click="close">{{ t('common.close') }}</button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { useI18n } from '../composables/useI18n'
import { useModal } from '../composables/useModal'
import { formatCurrency as formatCurrencyUtil } from '../utils/currency'

const { t, currentCurrency } = useI18n()

const props = defineProps({
  isOpen: {
    type: Boolean,
    default: false
  },
  transaction: {
    type: Object,
    default: null
  },
  // Injected from the parent so category values map through the same translation
  // table the transactions table uses; falls back to the raw value when absent.
  translateCategory: {
    type: Function,
    default: (category) => category
  }
})

const emit = defineEmits(['close'])

// Same modal shell/accessibility (escape, scroll-lock, focus trap/return) as the
// other detail modals.
const { modalRef, close } = useModal(() => props.isOpen && !!props.transaction, emit)

const formatCurrency = (value) => formatCurrencyUtil(value, currentCurrency.value)

// Longer, human-readable date for the detail view (the table uses a compact MM/DD/YY).
const formatDate = (dateString) => {
  const date = new Date(dateString)
  if (isNaN(date.getTime())) return dateString
  return date.toLocaleDateString(currentCurrency.value === 'JPY' ? 'ja-JP' : 'en-US', {
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  })
}
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2000;
  padding: 1rem;
}

.modal-container {
  background: white;
  border-radius: 12px;
  box-shadow: 0 20px 50px rgba(0, 0, 0, 0.15);
  max-width: 480px;
  width: 100%;
  max-height: 90vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1.5rem;
  border-bottom: 1px solid #e2e8f0;
  gap: 1rem;
}

.modal-title {
  font-size: 1.25rem;
  font-weight: 700;
  color: #0f172a;
  letter-spacing: -0.025em;
}

.close-button {
  background: none;
  border: none;
  color: #64748b;
  cursor: pointer;
  padding: 0.5rem;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 6px;
  transition: all 0.15s ease;
  flex-shrink: 0;
}

.close-button:hover {
  background: #f1f5f9;
  color: #0f172a;
}

.modal-body {
  flex: 1;
  overflow-y: auto;
  padding: 2rem;
}

.amount-headline {
  padding: 1.5rem;
  border-radius: 10px;
  text-align: center;
  background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
  color: white;
  margin-bottom: 2rem;
}

.amount-label {
  font-size: 0.875rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  opacity: 0.9;
  margin-bottom: 0.5rem;
}

.amount-value {
  font-size: 2.25rem;
  font-weight: 700;
}

.detail-grid {
  display: flex;
  flex-direction: column;
  gap: 0;
  margin: 0;
}

.detail-row {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 1rem;
  padding: 0.875rem 0;
  border-bottom: 1px solid #f1f5f9;
}

.detail-row:last-child {
  border-bottom: none;
}

.detail-label {
  font-size: 0.813rem;
  font-weight: 600;
  color: #64748b;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin: 0;
}

.detail-value {
  font-size: 0.938rem;
  font-weight: 500;
  color: #0f172a;
  text-align: right;
  margin: 0;
}

.detail-value.transaction-id {
  font-family: 'Monaco', 'Courier New', monospace;
  font-size: 0.813rem;
  color: #64748b;
}

.modal-footer {
  padding: 1.5rem;
  border-top: 1px solid #e2e8f0;
  display: flex;
  justify-content: flex-end;
}

.btn-secondary {
  padding: 0.625rem 1.25rem;
  background: #f1f5f9;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  font-weight: 500;
  font-size: 0.875rem;
  color: #334155;
  cursor: pointer;
  transition: all 0.15s ease;
  font-family: inherit;
}

.btn-secondary:hover {
  background: #e2e8f0;
  border-color: #cbd5e1;
}

/* Modal transition animations */
.modal-enter-active,
.modal-leave-active {
  transition: opacity 0.2s ease;
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}

.modal-enter-active .modal-container,
.modal-leave-active .modal-container {
  transition: transform 0.2s ease;
}

.modal-enter-from .modal-container,
.modal-leave-to .modal-container {
  transform: scale(0.95);
}
</style>
