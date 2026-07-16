<template>
  <div ref="rootRef" class="language-switcher">
    <button
      ref="buttonRef"
      class="language-button"
      aria-haspopup="true"
      :aria-expanded="isDropdownOpen"
      @click="toggleDropdown"
    >
      <svg
        width="20"
        height="20"
        viewBox="0 0 20 20"
        fill="none"
        class="globe-icon"
      >
        <circle cx="10" cy="10" r="7.5" stroke="currentColor" stroke-width="1.5"/>
        <path d="M3 10H17" stroke="currentColor" stroke-width="1.5"/>
        <path d="M10 3C10 3 7.5 5.5 7.5 10C7.5 14.5 10 17 10 17" stroke="currentColor" stroke-width="1.5"/>
        <path d="M10 3C10 3 12.5 5.5 12.5 10C12.5 14.5 10 17 10 17" stroke="currentColor" stroke-width="1.5"/>
      </svg>
      <span class="language-label">{{ localeName }}</span>
      <svg
        class="chevron"
        :class="{ 'chevron-open': isDropdownOpen }"
        width="16"
        height="16"
        viewBox="0 0 16 16"
        fill="none"
      >
        <path d="M4 6L8 10L12 6" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
      </svg>
    </button>

    <div v-if="isDropdownOpen" class="dropdown-menu" role="menu">
      <button
        v-for="locale in availableLocales"
        :key="locale"
        class="dropdown-item"
        role="menuitem"
        :class="{ active: currentLocale === locale }"
        @click="selectLanguage(locale)"
      >
        <span class="language-name">{{ getLanguageName(locale) }}</span>
        <svg
          v-if="currentLocale === locale"
          width="18"
          height="18"
          viewBox="0 0 18 18"
          fill="none"
          class="check-icon"
        >
          <path d="M4 9L7.5 12.5L14 6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, onBeforeUnmount } from 'vue'
import { useI18n } from '../composables/useI18n'

const { currentLocale, setLocale, availableLocales, localeName } = useI18n()

const isDropdownOpen = ref(false)
const rootRef = ref(null)
const buttonRef = ref(null)

const languageNames = {
  en: 'English',
  ja: '日本語'
}

const getLanguageName = (locale) => {
  return languageNames[locale] || locale
}

const toggleDropdown = () => {
  isDropdownOpen.value = !isDropdownOpen.value
}

const closeDropdown = () => {
  isDropdownOpen.value = false
}

// Close on any click outside the menu root. The toggle button lives inside rootRef, so
// the opening click is naturally ignored here (contains() is true) and won't re-close it.
const onClickOutside = (e) => {
  if (rootRef.value && !rootRef.value.contains(e.target)) {
    closeDropdown()
  }
}

// Escape closes and returns focus to the trigger; Arrow keys move between menu items.
const onKeydown = (e) => {
  if (e.key === 'Escape') {
    closeDropdown()
    buttonRef.value?.focus()
  } else if (e.key === 'ArrowDown' || e.key === 'ArrowUp') {
    e.preventDefault()
    const items = Array.from(rootRef.value?.querySelectorAll('.dropdown-item') || [])
    if (items.length === 0) return
    const currentIndex = items.indexOf(document.activeElement)
    const nextIndex = e.key === 'ArrowDown'
      ? (currentIndex + 1) % items.length
      : (currentIndex - 1 + items.length) % items.length
    items[nextIndex].focus()
  }
}

// Listeners are added only while open and removed on close, so nothing leaks. This
// replaces the previous racy @blur + setTimeout(...,200) dismissal.
watch(isDropdownOpen, (open) => {
  if (open) {
    document.addEventListener('click', onClickOutside)
    document.addEventListener('keydown', onKeydown)
  } else {
    document.removeEventListener('click', onClickOutside)
    document.removeEventListener('keydown', onKeydown)
  }
})

onBeforeUnmount(() => {
  document.removeEventListener('click', onClickOutside)
  document.removeEventListener('keydown', onKeydown)
})

const selectLanguage = (locale) => {
  setLocale(locale)
  isDropdownOpen.value = false
}
</script>

<style scoped>
.language-switcher {
  position: relative;
}

.language-button {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 0.875rem;
  background: white;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s ease;
  font-family: inherit;
  font-size: 0.875rem;
  color: #334155;
}

.language-button:hover {
  background: #f8fafc;
  border-color: #cbd5e1;
}

.globe-icon {
  color: #64748b;
  flex-shrink: 0;
}

.language-label {
  font-weight: 500;
}

.chevron {
  color: #64748b;
  transition: transform 0.2s ease;
  flex-shrink: 0;
}

.chevron-open {
  transform: rotate(180deg);
}

.dropdown-menu {
  position: absolute;
  top: calc(100% + 0.5rem);
  right: 0;
  min-width: 160px;
  background: white;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.1);
  z-index: 1000;
  overflow: hidden;
}

.dropdown-item {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
  padding: 0.75rem 1rem;
  background: none;
  border: none;
  text-align: left;
  cursor: pointer;
  transition: background 0.15s ease;
  font-family: inherit;
  font-size: 0.875rem;
  font-weight: 500;
  color: #334155;
}

.dropdown-item:hover {
  background: #f8fafc;
}

.dropdown-item.active {
  background: #eff6ff;
  color: #2563eb;
}

.language-name {
  flex: 1;
}

.check-icon {
  color: #2563eb;
  flex-shrink: 0;
}
</style>
