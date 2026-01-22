import { describe, it, expect, beforeEach } from 'vitest';
import {
  saveApiKey,
  getApiKey,
  getApiKeyExpiry,
  clearApiKey,
  getRemainingDays,
} from './storage';

describe('storage utils', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  describe('saveApiKey', () => {
    it('saves apiKey to localStorage', () => {
      saveApiKey('uk_test');
      expect(localStorage.getItem('userApiKey')).toBe('uk_test');
    });

    it('saves expiry date (30 days from now)', () => {
      const before = Date.now();
      saveApiKey('uk_test');
      const after = Date.now();

      const expiry = Number(localStorage.getItem('userApiKeyExpiry'));
      const thirtyDays = 30 * 24 * 60 * 60 * 1000;

      expect(expiry).toBeGreaterThanOrEqual(before + thirtyDays);
      expect(expiry).toBeLessThanOrEqual(after + thirtyDays);
    });
  });

  describe('getApiKey', () => {
    it('returns apiKey if not expired', () => {
      const futureExpiry = Date.now() + 1000000;
      localStorage.setItem('userApiKey', 'uk_valid');
      localStorage.setItem('userApiKeyExpiry', String(futureExpiry));

      expect(getApiKey()).toBe('uk_valid');
    });

    it('returns null if expired', () => {
      const pastExpiry = Date.now() - 1000;
      localStorage.setItem('userApiKey', 'uk_expired');
      localStorage.setItem('userApiKeyExpiry', String(pastExpiry));

      expect(getApiKey()).toBeNull();
    });

    it('clears storage if expired', () => {
      const pastExpiry = Date.now() - 1000;
      localStorage.setItem('userApiKey', 'uk_expired');
      localStorage.setItem('userApiKeyExpiry', String(pastExpiry));

      getApiKey();

      expect(localStorage.getItem('userApiKey')).toBeNull();
      expect(localStorage.getItem('userApiKeyExpiry')).toBeNull();
    });

    it('returns null if no apiKey stored', () => {
      expect(getApiKey()).toBeNull();
    });
  });

  describe('getApiKeyExpiry', () => {
    it('returns expiry timestamp', () => {
      const expiry = Date.now() + 1000000;
      localStorage.setItem('userApiKeyExpiry', String(expiry));

      expect(getApiKeyExpiry()).toBe(expiry);
    });

    it('returns null if no expiry stored', () => {
      expect(getApiKeyExpiry()).toBeNull();
    });
  });

  describe('clearApiKey', () => {
    it('removes apiKey from localStorage', () => {
      localStorage.setItem('userApiKey', 'uk_test');
      localStorage.setItem('userApiKeyExpiry', '123');

      clearApiKey();

      expect(localStorage.getItem('userApiKey')).toBeNull();
      expect(localStorage.getItem('userApiKeyExpiry')).toBeNull();
    });
  });

  describe('getRemainingDays', () => {
    it('returns correct remaining days', () => {
      const tenDaysLater = Date.now() + 10 * 24 * 60 * 60 * 1000;
      localStorage.setItem('userApiKeyExpiry', String(tenDaysLater));

      expect(getRemainingDays()).toBe(10);
    });

    it('returns 0 if expired', () => {
      const pastExpiry = Date.now() - 1000;
      localStorage.setItem('userApiKeyExpiry', String(pastExpiry));

      expect(getRemainingDays()).toBe(0);
    });

    it('returns 0 if no expiry stored', () => {
      expect(getRemainingDays()).toBe(0);
    });
  });
});
