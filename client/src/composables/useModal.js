import { ref, watch, nextTick, onBeforeUnmount } from 'vue'

// Shared modal shell behavior + accessibility for the six detail modals.
// Handles, while the modal is open:
//  - Escape-to-close
//  - body scroll-lock
//  - a focus trap (Tab/Shift+Tab cycle within the dialog)
//  - focus return to the element that opened the modal
// All global listeners/side effects are added when the modal opens and removed when it
// closes (and on unmount), so nothing leaks.
//
// Params:
//  - isOpen: a getter fn `() => boolean` or a ref tracking the modal's open state
//  - emit:   the component's emit function; `close()` emits `'close'`
// Returns:
//  - modalRef: bind to the dialog container element (drives the focus trap / initial focus)
//  - close:    emits `'close'` (use for overlay click, close button, footer button)
export function useModal(isOpen, emit) {
  const modalRef = ref(null)
  // Element focused before the modal opened, restored on close for keyboard/SR users.
  let triggerEl = null

  const getOpen = typeof isOpen === 'function' ? isOpen : () => isOpen.value

  const close = () => emit('close')

  // Interactive, focusable descendants in DOM order, skipping hidden ones.
  const focusableSelector = [
    'a[href]',
    'button:not([disabled])',
    'textarea:not([disabled])',
    'input:not([disabled])',
    'select:not([disabled])',
    '[tabindex]:not([tabindex="-1"])'
  ].join(', ')

  const getFocusable = () => {
    if (!modalRef.value) return []
    return Array.from(modalRef.value.querySelectorAll(focusableSelector))
      .filter((el) => el.offsetParent !== null)
  }

  const trapFocus = (e) => {
    const focusable = getFocusable()
    if (focusable.length === 0) {
      // Nothing to focus inside: keep focus on the dialog container itself.
      e.preventDefault()
      modalRef.value?.focus()
      return
    }
    const first = focusable[0]
    const last = focusable[focusable.length - 1]
    const active = document.activeElement
    const inside = modalRef.value?.contains(active)

    if (e.shiftKey) {
      if (active === first || !inside) {
        e.preventDefault()
        last.focus()
      }
    } else if (active === last || !inside) {
      e.preventDefault()
      first.focus()
    }
  }

  const onKeydown = (e) => {
    if (e.key === 'Escape') {
      e.stopPropagation()
      close()
    } else if (e.key === 'Tab') {
      trapFocus(e)
    }
  }

  const activate = async () => {
    triggerEl = document.activeElement
    document.addEventListener('keydown', onKeydown)
    document.body.style.overflow = 'hidden'
    // Wait for the Teleport/Transition content to render before moving focus into it.
    await nextTick()
    const focusable = getFocusable()
    ;(focusable[0] || modalRef.value)?.focus()
  }

  const deactivate = () => {
    document.removeEventListener('keydown', onKeydown)
    document.body.style.overflow = ''
    if (triggerEl && typeof triggerEl.focus === 'function') {
      triggerEl.focus()
    }
    triggerEl = null
  }

  watch(getOpen, (open) => {
    if (open) {
      activate()
    } else {
      deactivate()
    }
  })

  // Safety net: if the component unmounts while still open, drop the listener and
  // release the scroll lock so we never strand a global side effect.
  onBeforeUnmount(() => {
    document.removeEventListener('keydown', onKeydown)
    if (getOpen()) {
      document.body.style.overflow = ''
    }
  })

  return { modalRef, close }
}
