// ⚠️ MOCK AUTHENTICATION — FOR THE DEMO ONLY. This composable does NOT implement
// real authentication and must not be mistaken for it:
//   - `isAuthenticated` is hardcoded `true` and is never read to protect routes
//     (there is no navigation guard in `main.js`), so it gates nothing.
//   - There is no real session, token, cookie or login flow. The "current user"
//     is static mock data below.
//   - `logout()` is a stub: it does not clear any real session or redirect. It
//     only flips the mock `isAuthenticated` flag and shows a demo alert.
// If real auth is ever needed, this whole file has to be replaced with a real
// session/token flow and route protection — do not extend the mock into
// production security.
import { ref, computed } from 'vue'
import { useI18n } from './useI18n'

// Base user data (language-independent)
const baseUserData = {
  id: 1,
  email: 'john.doe@catalystcomponents.com',
  phone: '+1 (111) 111-1111',
  avatar: null,
  joinDate: '2022-03-15'
}

// Localized titles for the mock tasks, keyed by task id. Only the title is
// language-dependent; everything else about a task (its priority, due date and
// completion status) is stable across locales and lives in `mockTasks` below.
const mockTaskTitles = {
  en: {
    1: 'Review Q4 inventory levels',
    2: 'Approve Tokyo warehouse orders',
    3: 'Update reorder points for Circuit Boards',
    4: 'Review monthly spending report'
  },
  ja: {
    1: '第4四半期の在庫レベルを確認',
    2: '東京倉庫の注文を承認',
    3: '回路基板の再注文点を更新',
    4: '月次支出レポートを確認'
  }
}

// Source of truth for the mock tasks (ids 1-4). This is a plain ref so that
// deletions and status toggles are real mutations that persist — unlike the
// old approach where the tasks were rebuilt from a locale literal inside the
// computed and silently reset on every language switch. The computed below
// only decorates these with a localized title; it never owns the task list.
const mockTasks = ref([
  { id: 1, priority: 'high', dueDate: '2025-10-08', status: 'pending' },
  { id: 2, priority: 'medium', dueDate: '2025-10-06', status: 'pending' },
  { id: 3, priority: 'medium', dueDate: '2025-10-10', status: 'pending' },
  { id: 4, priority: 'low', dueDate: '2025-10-15', status: 'pending' }
])

// Mock current user data with language-aware fields
const createCurrentUser = () => {
  const { currentLocale } = useI18n()

  return computed(() => {
    const isJapanese = currentLocale.value === 'ja'
    const titles = isJapanese ? mockTaskTitles.ja : mockTaskTitles.en

    return {
      ...baseUserData,
      name: isJapanese ? '田中 太郎' : 'John Doe',
      jobTitle: isJapanese ? 'オペレーションマネージャー' : 'Operations Manager',
      department: isJapanese ? 'サプライチェーン運営部' : 'Supply Chain Operations',
      location: isJapanese ? 'サンフランシスコ' : 'San Francisco',
      // Decorate the persistent mock tasks with the current locale's title.
      tasks: mockTasks.value.map(task => ({
        ...task,
        title: titles[task.id]
      }))
    }
  })
}

const currentUser = createCurrentUser()

// Mutation helpers for the mock tasks. These operate on the `mockTasks` ref
// (the source of truth) rather than on the `currentUser` computed, so the
// changes survive locale switches. Callers should route mock-task edits here
// instead of mutating `currentUser.value.tasks`.
const deleteMockTask = (taskId) => {
  const index = mockTasks.value.findIndex(task => task.id === taskId)
  if (index !== -1) {
    mockTasks.value.splice(index, 1)
  }
}

const toggleMockTask = (taskId) => {
  const task = mockTasks.value.find(task => task.id === taskId)
  if (task) {
    task.status = task.status === 'pending' ? 'completed' : 'pending'
  }
}

export function useAuth() {
  // Mock flag — always starts true and is not used for route protection.
  const isAuthenticated = ref(true)

  // Demo stub: there is no real session to clear. We flip the mock flag so the
  // state change is at least honest, then surface a demo notice. A real
  // implementation would clear tokens/cookies and redirect to a login page.
  const logout = () => {
    isAuthenticated.value = false
    alert('This is a demo — there is no real session to log out of.')
  }

  // Build initials from a name, e.g. "John Doe" -> "JD". Guarded against
  // missing, empty, or whitespace-only input (which previously threw on
  // `n[0]` / `.split` of undefined) — returns a safe fallback instead.
  const getInitials = (name) => {
    if (typeof name !== 'string' || !name.trim()) {
      return '?'
    }
    return name
      .trim()
      .split(/\s+/)
      .map(n => n[0])
      .join('')
      .toUpperCase()
  }

  return {
    currentUser,
    mockTasks,
    deleteMockTask,
    toggleMockTask,
    isAuthenticated,
    logout,
    getInitials
  }
}
