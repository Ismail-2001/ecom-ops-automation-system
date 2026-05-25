import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

import AppShell from './components/layout/AppShell';
import Dashboard from './pages/Dashboard';
import AuditLog from './pages/AuditLog';
import Analytics from './pages/Analytics';
import Settings from './pages/Settings';

// Initialize TanStack React Query Client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false, // Prevent aggressive refetches on focus
      retry: 1, // Limit retries to 1 to fail fast during errors
    },
  },
});

export const App: React.FC = () => {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<AppShell />}>
            <Route index element={<Dashboard />} />
            <Route path="audit" element={<AuditLog />} />
            <Route path="analytics" element={<Analytics />} />
            <Route path="settings" element={<Settings />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  );
};

export default App;
