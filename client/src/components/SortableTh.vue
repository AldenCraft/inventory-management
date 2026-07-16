<template>
  <th
    class="sortable-th"
    :class="{ active: isActive }"
    :aria-sort="ariaSort"
    tabindex="0"
    role="columnheader"
    @click="emitSort"
    @keydown.enter.prevent="emitSort"
    @keydown.space.prevent="emitSort"
  >
    <span class="th-content">
      <span class="th-label">{{ label }}</span>
      <!-- Caret only shows on the active column; standard glyphs, not emojis. -->
      <span v-if="isActive" class="th-caret">{{ caret }}</span>
    </span>
  </th>
</template>

<script>
import { computed } from 'vue'

export default {
  name: 'SortableTh',
  props: {
    columnKey: {
      type: String,
      required: true
    },
    label: {
      type: String,
      required: true
    },
    sortKey: {
      type: String,
      default: null
    },
    sortDir: {
      type: String,
      default: null
    }
  },
  emits: ['sort'],
  setup(props, { emit }) {
    const isActive = computed(() => props.columnKey === props.sortKey)

    const caret = computed(() => {
      if (!isActive.value) return ''
      return props.sortDir === 'asc' ? '▲' : '▼'
    })

    const ariaSort = computed(() => {
      if (!isActive.value) return 'none'
      return props.sortDir === 'asc' ? 'ascending' : 'descending'
    })

    const emitSort = () => {
      emit('sort', props.columnKey)
    }

    return {
      isActive,
      caret,
      ariaSort,
      emitSort
    }
  }
}
</script>

<style scoped>
.sortable-th {
  cursor: pointer;
  user-select: none;
  transition: background-color 0.15s ease;
}

.sortable-th:hover {
  background: #f1f5f9;
}

.sortable-th:focus {
  outline: none;
  box-shadow: inset 0 0 0 2px rgba(59, 130, 246, 0.35);
}

.th-content {
  display: inline-flex;
  align-items: center;
  gap: 0.375rem;
}

.th-caret {
  font-size: 0.7rem;
  line-height: 1;
  color: #64748b;
}
</style>
