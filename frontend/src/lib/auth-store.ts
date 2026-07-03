import { create } from "zustand"
import { persist } from "zustand/middleware"
import { authApi, ApiError } from "./api"

interface AuthState {
  apiKey: string | null
  operator: string | null
  isAuthenticated: boolean
  isLoading: boolean
  error: string | null

  login: (apiKey: string) => Promise<boolean>
  logout: () => void
  clearError: () => void
}

function setCookie(name: string, value: string, days = 7) {
  if (typeof document === 'undefined') return
  const expires = new Date(Date.now() + days * 864e5).toUTCString()
  document.cookie = `${name}=${encodeURIComponent(value)}; expires=${expires}; path=/; SameSite=Lax`
}

function deleteCookie(name: string) {
  if (typeof document === 'undefined') return
  document.cookie = `${name}=; expires=Thu, 01 Jan 1970 00:00:00 GMT; path=/`
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      apiKey: null,
      operator: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,

      login: async (apiKey: string) => {
        set({ isLoading: true, error: null })
        try {
          const res = await authApi.login(apiKey)
          if (res.status === "ok") {
            localStorage.setItem("opsiq_api_key", apiKey)
            setCookie("opsiq_api_key", apiKey)
            setCookie("opsiq_auth", "true")
            set({
              apiKey,
              operator: res.operator,
              isAuthenticated: true,
              isLoading: false,
            })
            return true
          }
          set({ isLoading: false, error: "Login failed" })
          return false
        } catch (err) {
          const message =
            err instanceof ApiError
              ? err.status === 401
                ? "Invalid API key"
                : `Server error (${err.status})`
              : "Connection failed — is the backend running?"
          set({ isLoading: false, error: message })
          return false
        }
      },

      logout: () => {
        localStorage.removeItem("opsiq_api_key")
        deleteCookie("opsiq_api_key")
        deleteCookie("opsiq_auth")
        set({
          apiKey: null,
          operator: null,
          isAuthenticated: false,
          error: null,
        })
      },

      clearError: () => set({ error: null }),
    }),
    {
      name: "opsiq-auth",
      partialize: (state) => ({
        apiKey: state.apiKey,
        operator: state.operator,
        isAuthenticated: state.isAuthenticated,
      }),
    },
  ),
)
