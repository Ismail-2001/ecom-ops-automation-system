import { useState, useCallback, useEffect } from 'react';
import { apiClient } from '../api/client';

const STORAGE_KEY = 'opsiq_api_key';
const OPERATOR_KEY = 'opsiq_operator';

export interface AuthState {
  isAuthenticated: boolean;
  apiKey: string | null;
  operatorId: string | null;
  login: (apiKey: string, operatorId?: string) => Promise<void>;
  logout: () => void;
}

export const useAuth = (): AuthState => {
  const [apiKey, setApiKey] = useState<string | null>(() => localStorage.getItem(STORAGE_KEY));
  const [operatorId, setOperatorId] = useState<string | null>(() => localStorage.getItem(OPERATOR_KEY));

  useEffect(() => {
    if (apiKey) {
      apiClient.defaults.headers.common['Authorization'] = `Bearer ${apiKey}`;
    }
    if (operatorId) {
      apiClient.defaults.headers.common['X-Operator-Id'] = operatorId;
    }
  }, [apiKey, operatorId]);

  const login = useCallback(async (key: string, opId?: string) => {
    const operator = opId || 'dashboard-operator';
    const resp = await apiClient.post('/api/auth/login', {
      api_key: key,
      operator_id: operator,
    });
    if (resp.status !== 200) {
      throw new Error('Invalid API key');
    }
    localStorage.setItem(STORAGE_KEY, key);
    localStorage.setItem(OPERATOR_KEY, operator);
    apiClient.defaults.headers.common['Authorization'] = `Bearer ${key}`;
    apiClient.defaults.headers.common['X-Operator-Id'] = operator;
    setApiKey(key);
    setOperatorId(operator);
  }, []);

  const logout = useCallback(() => {
    localStorage.removeItem(STORAGE_KEY);
    localStorage.removeItem(OPERATOR_KEY);
    delete apiClient.defaults.headers.common['Authorization'];
    delete apiClient.defaults.headers.common['X-Operator-Id'];
    setApiKey(null);
    setOperatorId(null);
  }, []);

  return {
    isAuthenticated: !!apiKey,
    apiKey,
    operatorId,
    login,
    logout,
  };
};
