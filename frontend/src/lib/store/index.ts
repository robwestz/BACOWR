import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type { JobPackage, ToastMessage, UserSettings } from '@/types'

// Toast Store
interface ToastStore {
  toasts: ToastMessage[]
  addToast: (toast: Omit<ToastMessage, 'id'>) => void
  removeToast: (id: string) => void
  clearToasts: () => void
}

export const useToastStore = create<ToastStore>((set) => ({
  toasts: [],
  addToast: (toast) => {
    const id = Math.random().toString(36).substring(7)
    const newToast: ToastMessage = { id, ...toast }
    set((state) => ({ toasts: [...state.toasts, newToast] }))

    // Auto-remove after duration
    setTimeout(() => {
      set((state) => ({
        toasts: state.toasts.filter((t) => t.id !== id),
      }))
    }, toast.duration || 5000)
  },
  removeToast: (id) =>
    set((state) => ({
      toasts: state.toasts.filter((t) => t.id !== id),
    })),
  clearToasts: () => set({ toasts: [] }),
}))

// Jobs Store
interface JobsStore {
  recentJobs: JobPackage[]
  activeJobs: Map<string, JobPackage>
  addJob: (job: JobPackage) => void
  updateJob: (jobId: string, updates: Partial<JobPackage>) => void
  removeJob: (jobId: string) => void
  clearJobs: () => void
}

export const useJobsStore = create<JobsStore>((set) => ({
  recentJobs: [],
  activeJobs: new Map(),
  addJob: (job) =>
    set((state) => ({
      recentJobs: [job, ...state.recentJobs].slice(0, 10),
      activeJobs: new Map(state.activeJobs).set(job.job_meta.job_id, job),
    })),
  updateJob: (jobId, updates) =>
    set((state) => {
      const job = state.activeJobs.get(jobId)
      if (!job) return state

      const updatedJob = { ...job, ...updates }
      const newActiveJobs = new Map(state.activeJobs)
      newActiveJobs.set(jobId, updatedJob)

      return {
        activeJobs: newActiveJobs,
        recentJobs: state.recentJobs.map((j) =>
          j.job_meta.job_id === jobId ? updatedJob : j
        ),
      }
    }),
  removeJob: (jobId) =>
    set((state) => {
      const newActiveJobs = new Map(state.activeJobs)
      newActiveJobs.delete(jobId)
      return {
        activeJobs: newActiveJobs,
        recentJobs: state.recentJobs.filter((j) => j.job_meta.job_id !== jobId),
      }
    }),
  clearJobs: () => set({ recentJobs: [], activeJobs: new Map() }),
}))

// Settings Store (persisted)
interface SettingsStore {
  settings: UserSettings | null
  setSettings: (settings: UserSettings) => void
  updateSettings: (updates: Partial<UserSettings>) => void
  clearSettings: () => void
}

export const useSettingsStore = create<SettingsStore>()(
  persist(
    (set) => ({
      settings: null,
      setSettings: (settings) => set({ settings }),
      updateSettings: (updates) =>
        set((state) => ({
          settings: state.settings ? { ...state.settings, ...updates } : null,
        })),
      clearSettings: () => set({ settings: null }),
    }),
    {
      name: 'bacowr-settings',
    }
  )
)

// UI Store
interface UIStore {
  sidebarCollapsed: boolean
  darkMode: boolean
  commandPaletteOpen: boolean
  toggleSidebar: () => void
  toggleDarkMode: () => void
  toggleCommandPalette: () => void
}

export const useUIStore = create<UIStore>()(
  persist(
    (set) => ({
      sidebarCollapsed: false,
      darkMode: false,
      commandPaletteOpen: false,
      toggleSidebar: () =>
        set((state) => ({ sidebarCollapsed: !state.sidebarCollapsed })),
      toggleDarkMode: () => set((state) => ({ darkMode: !state.darkMode })),
      toggleCommandPalette: () =>
        set((state) => ({ commandPaletteOpen: !state.commandPaletteOpen })),
    }),
    {
      name: 'bacowr-ui',
    }
  )
)

// Create Job Wizard Store
interface CreateJobWizardStore {
  step: number
  input: {
    publisher_domain: string
    target_url: string
    anchor_text: string
    llm_provider: string
    strategy: string
    country: string
  }
  setStep: (step: number) => void
  updateInput: (updates: Partial<CreateJobWizardStore['input']>) => void
  reset: () => void
}

export const useCreateJobWizard = create<CreateJobWizardStore>((set) => ({
  step: 0,
  input: {
    publisher_domain: '',
    target_url: '',
    anchor_text: '',
    llm_provider: 'auto',
    strategy: 'multi_stage',
    country: 'se',
  },
  setStep: (step) => set({ step }),
  updateInput: (updates) =>
    set((state) => ({ input: { ...state.input, ...updates } })),
  reset: () =>
    set({
      step: 0,
      input: {
        publisher_domain: '',
        target_url: '',
        anchor_text: '',
        llm_provider: 'auto',
        strategy: 'multi_stage',
        country: 'se',
      },
    }),
}))
