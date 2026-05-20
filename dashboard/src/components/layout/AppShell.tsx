import React, { useState } from 'react';
import { Outlet } from 'react-router-dom';
import Sidebar from './Sidebar';
import TopBar from './TopBar';
import ShadowModeBanner from './ShadowModeBanner';
import { ToastContainer } from '../common/ToastContainer';
import type { Toast } from '../common/ToastContainer';
import { useWebSocket } from '../../hooks/useWebSocket';

export const AppShell: React.FC = () => {
  const [toasts, setToasts] = useState<Toast[]>([]);

  // Function to spawn new Toast alert
  const triggerToast = (
    title: string,
    message: string,
    type: 'info' | 'success' | 'warning' | 'error' = 'info'
  ) => {
    const id = Math.random().toString(36).substring(2, 9);
    setToasts((prev) => [...prev, { id, title, message, type }]);

    // Auto dismiss toast after 6 seconds
    setTimeout(() => {
      removeToast(id);
    }, 6000);
  };

  const removeToast = (id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  };

  // Setup live connection and receive events
  const { isConnected, isPipelineRunning } = useWebSocket(triggerToast);

  return (
    <div className="flex flex-col h-screen overflow-hidden bg-slate-950 text-slate-100 font-sans">
      {/* 1. Shadow Mode Banner (Non-hideable if active in DB) */}
      <ShadowModeBanner />

      {/* 2. Main Dashboard Split View */}
      <div className="flex flex-1 overflow-hidden">
        {/* Sidebar */}
        <Sidebar wsConnected={isConnected} />

        {/* Workspace content area */}
        <div className="flex-1 flex flex-col overflow-hidden">
          {/* Top Bar */}
          <TopBar isPipelineRunning={isPipelineRunning} onToast={triggerToast} />

          {/* Subpage Viewport */}
          <main className="flex-1 overflow-y-auto bg-slate-950 p-8">
            <Outlet context={{ triggerToast }} />
          </main>
        </div>
      </div>

      {/* Toast Alert popups */}
      <ToastContainer toasts={toasts} removeToast={removeToast} />
    </div>
  );
};

export default AppShell;
