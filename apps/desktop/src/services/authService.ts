/**
 * Local Desktop Authentication Service.
 *
 * Communicates with the local FastAPI backend (http://127.0.0.1:8765/api/v1/auth)
 * to manage user login, first-run setup, and session lifecycle.
 */
import {
  UserProfile,
  AuthSession,
  LoginCredentials,
  FirstRunSetupData,
  SetupStatus,
} from '../types';
import { getApiBaseUrl } from './config';

const API_BASE = `${getApiBaseUrl()}/api/v1`;
const SESSION_STORAGE_KEY = 'mineintel_active_session_token';

class AuthService {
  private activeToken: string | null = null;
  private currentUser: UserProfile | null = null;

  constructor() {
    // Restore session token from sessionStorage if present
    try {
      this.activeToken = sessionStorage.getItem(SESSION_STORAGE_KEY);
    } catch {
      this.activeToken = null;
    }
  }

  public getToken(): string | null {
    return this.activeToken;
  }

  public getCurrentUser(): UserProfile | null {
    return this.currentUser;
  }

  public getAuthHeader(): Record<string, string> {
    if (!this.activeToken) return {};
    return { Authorization: `Bearer ${this.activeToken}` };
  }

  /**
   * Check whether any local accounts exist or if first-run setup is required.
   */
  public async getSetupStatus(): Promise<SetupStatus> {
    try {
      const resp = await fetch(`${API_BASE}/auth/setup-status`, {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' },
      });
      if (resp.ok) {
        return await resp.json();
      }
    } catch (e) {
      console.warn('Backend unavailable during setup check, assuming offline fallback:', e);
    }
    // Fallback if backend is offline or initial state
    return { has_users: true, requires_setup: false };
  }

  /**
   * Perform initial admin profile setup on fresh installation.
   */
  public async firstRunSetup(data: FirstRunSetupData): Promise<AuthSession> {
    const resp = await fetch(`${API_BASE}/auth/first-run-setup`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });

    if (!resp.ok) {
      const errData = await resp.json().catch(() => ({}));
      throw new Error(errData.detail || 'First-run setup failed. Please retry.');
    }

    const session: AuthSession = await resp.json();
    this.setSession(session.session_token, session.user);
    return session;
  }

  /**
   * Authenticate local user with username and password.
   */
  public async login(credentials: LoginCredentials): Promise<AuthSession> {
    const resp = await fetch(`${API_BASE}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(credentials),
    });

    if (!resp.ok) {
      const errData = await resp.json().catch(() => ({}));
      throw new Error(errData.detail || 'Invalid username or password.');
    }

    const session: AuthSession = await resp.json();
    this.setSession(session.session_token, session.user);
    return session;
  }

  /**
   * Validate current session with backend and retrieve profile.
   */
  public async validateSession(): Promise<UserProfile | null> {
    if (!this.activeToken) return null;

    try {
      const resp = await fetch(`${API_BASE}/auth/session`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${this.activeToken}`,
        },
      });

      if (resp.ok) {
        const data = await resp.json();
        this.currentUser = data.user;
        return data.user;
      }
    } catch {
      // Backend offline or unreachable
    }

    this.clearSession();
    return null;
  }

  /**
   * Sign out and revoke active local session.
   */
  public async logout(): Promise<void> {
    if (this.activeToken) {
      try {
        await fetch(`${API_BASE}/auth/logout`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${this.activeToken}`,
          },
        });
      } catch {
        // Continue clearing local state even if backend is offline
      }
    }
    this.clearSession();
  }

  private setSession(token: string, user: UserProfile) {
    this.activeToken = token;
    this.currentUser = user;
    try {
      sessionStorage.setItem(SESSION_STORAGE_KEY, token);
    } catch {
      // Non-blocking
    }
  }

  private clearSession() {
    this.activeToken = null;
    this.currentUser = null;
    try {
      sessionStorage.removeItem(SESSION_STORAGE_KEY);
    } catch {
      // Non-blocking
    }
  }
}

export const authService = new AuthService();
