// Session storage + read/write helpers. No user model beyond "logged in or
// not" yet (see the plan: RBAC is Fase Web 1+) — this just holds the JWT
// and the display name returned at login.

const TOKEN_KEY = 'idp_access_token'
const USER_NAME_KEY = 'idp_user_name'

export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY)
}

export function getUserName(): string | null {
  return localStorage.getItem(USER_NAME_KEY)
}

export function setSession(token: string, userName: string): void {
  localStorage.setItem(TOKEN_KEY, token)
  localStorage.setItem(USER_NAME_KEY, userName)
}

export function clearSession(): void {
  localStorage.removeItem(TOKEN_KEY)
  localStorage.removeItem(USER_NAME_KEY)
}

export function isAuthenticated(): boolean {
  return getToken() !== null
}
