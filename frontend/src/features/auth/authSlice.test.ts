import { describe, it, expect, beforeEach, vi } from 'vitest';
import authReducer, {
  setApiKey,
  clearAuth,
  loadCachedAuth,
  setLoginStatus,
} from './authSlice';
import type { AuthState } from '@/types';
import * as storage from '@/utils/storage';

// Mock storage functions
vi.mock('@/utils/storage', () => ({
  saveApiKey: vi.fn(),
  getApiKey: vi.fn(),
  getApiKeyExpiry: vi.fn(),
  clearApiKey: vi.fn(),
}));

describe('authSlice', () => {
  const initialState: AuthState = {
    apiKey: null,
    apiKeyExpiry: null,
    isAuthenticated: false,
    loginStatus: 'idle',
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('setApiKey', () => {
    it('should set apiKey and authenticate user', () => {
      const mockExpiry = Date.now() + 1000000;
      vi.mocked(storage.getApiKeyExpiry).mockReturnValue(mockExpiry);

      const state = authReducer(initialState, setApiKey('uk_test123'));

      expect(state.apiKey).toBe('uk_test123');
      expect(state.apiKeyExpiry).toBe(mockExpiry);
      expect(state.isAuthenticated).toBe(true);
      expect(state.loginStatus).toBe('succeeded');
      expect(storage.saveApiKey).toHaveBeenCalledWith('uk_test123');
    });
  });

  describe('clearAuth', () => {
    it('should clear all auth state', () => {
      const authenticatedState: AuthState = {
        apiKey: 'uk_test',
        apiKeyExpiry: Date.now() + 1000000,
        isAuthenticated: true,
        loginStatus: 'succeeded',
      };

      const state = authReducer(authenticatedState, clearAuth());

      expect(state.apiKey).toBeNull();
      expect(state.apiKeyExpiry).toBeNull();
      expect(state.isAuthenticated).toBe(false);
      expect(state.loginStatus).toBe('idle');
      expect(storage.clearApiKey).toHaveBeenCalled();
    });
  });

  describe('loadCachedAuth', () => {
    it('should load valid cached auth', () => {
      const mockExpiry = Date.now() + 1000000;
      vi.mocked(storage.getApiKey).mockReturnValue('uk_cached');
      vi.mocked(storage.getApiKeyExpiry).mockReturnValue(mockExpiry);

      const state = authReducer(initialState, loadCachedAuth());

      expect(state.apiKey).toBe('uk_cached');
      expect(state.apiKeyExpiry).toBe(mockExpiry);
      expect(state.isAuthenticated).toBe(true);
      expect(state.loginStatus).toBe('succeeded');
    });

    it('should clear expired cached auth', () => {
      const expiredExpiry = Date.now() - 1000;
      vi.mocked(storage.getApiKey).mockReturnValue('uk_expired');
      vi.mocked(storage.getApiKeyExpiry).mockReturnValue(expiredExpiry);

      const state = authReducer(initialState, loadCachedAuth());

      expect(state.apiKey).toBeNull();
      expect(state.isAuthenticated).toBe(false);
      expect(storage.clearApiKey).toHaveBeenCalled();
    });

    it('should handle no cached auth', () => {
      vi.mocked(storage.getApiKey).mockReturnValue(null);
      vi.mocked(storage.getApiKeyExpiry).mockReturnValue(null);

      const state = authReducer(initialState, loadCachedAuth());

      expect(state.apiKey).toBeNull();
      expect(state.isAuthenticated).toBe(false);
    });
  });

  describe('setLoginStatus', () => {
    it('should update login status', () => {
      const state = authReducer(initialState, setLoginStatus('loading'));
      expect(state.loginStatus).toBe('loading');
    });
  });
});
