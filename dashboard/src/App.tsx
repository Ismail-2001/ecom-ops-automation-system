import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

import { AuthGuard } from './components/common/AuthGuard';
import { Login } from './pages/Login';
import { useAuth, AuthState } from './hooks/useAuth';

import AppShell from './components/layout/AppShell';
import Dashboard from './pages/Dashboard';
import AuditLog from './pages/AuditLog';
import Analytics from './pages/Analytics';
import Settings from './pages/Settings';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
});

const AuthContext = React.createContext<AuthState | null>(null);

export const useAuthContext = () => {
  const ctx = React.useContext(AuthContext);
  if (!ctx) throw new Error('useAuthContext must be used within App');
  return ctx;
};

const AppInner: React.FC = () => {
  const auth = useAuth();

  return (
    <AuthContext.Provider value={auth}>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route element={<AuthGuard />}>
            <Route path="/" element={<AppShell />}>
              <Route index element={<Dashboard />} />
              <Route path="audit" element={<AuditLog />} />
              <Route path="analytics" element={<Analytics />} />
              <Route path="settings" element={<Settings />} />
            </Route>
          </Route>
        </Routes>
      </BrowserRouter>
    </AuthContext.Provider>
  );
};

export const App: React.FC = () => {
  return (
    <QueryClientProvider client={queryClient}>
      <AppInner />
    </QueryClientProvider>
  );
};

export default App;
