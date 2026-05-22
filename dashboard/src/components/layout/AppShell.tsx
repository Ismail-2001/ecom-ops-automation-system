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

  const triggerToast = (
    title: string,
    message: string,
    type: 'info' | 'success' | 'warning' | 'error' = 'info'
  ) => {
    const id = Math.random().toString(36).substring(2, 9);
    setToasts((prev) => [...prev, { id, title, message, type }]);
    setTimeout(() => removeToast(id), 6000);
  };

  const removeToast = (id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  };

  const { isConnected, isPipelineRunning } = useWebSocket(triggerToast);

  return (
    <div
      className="flex flex-col h-screen overflow-hidden font-sans relative"
      style={{ background: '#02030a', color: '#f1f5f9' }}
    >
      {/* ── Ambient background mesh ── */}
      <div
        className="pointer-events-none absolute inset-0 z-0"
        style={{
          background: `
            radial-gradient(ellipse 60% 40% at 10% 0%, rgba(37,99,235,0.10) 0%, transparent 70%),
            radial-gradient(ellipse 50% 40% at 90% 100%, rgba(124,58,237,0.08) 0%, transparent 70%),
            radial-gradient(ellipse 40% 30% at 50% 50%, rgba(16,185,129,0.03) 0%, transparent 70%)
          `,
        }}
      />

      {/* Subtle grid overlay */}
      <div
        className="pointer-events-none absolute inset-0 z-0 opacity-20"
        style={{
          backgroundImage: `linear-gradient(rgba(148,163,184,0.03) 1px, transparent 1px),
                            linear-gradient(90deg, rgba(148,163,184,0.03) 1px, transparent 1px)`,
          backgroundSize: '40px 40px',
        }}
      />

      {/* 1. Shadow Mode Banner */}
      <ShadowModeBanner />

      {/* 2. Main Split */}
      <div className="flex flex-1 overflow-hidden relative z-10">
        <Sidebar wsConnected={isConnected} />

        <div className="flex-1 flex flex-col overflow-hidden">
          <TopBar isPipelineRunning={isPipelineRunning} onToast={triggerToast} />

          <main className="flex-1 overflow-y-auto p-8">
            <Outlet context={{ triggerToast }} />
          </main>
        </div>
      </div>

      <ToastContainer toasts={toasts} removeToast={removeToast} />
    </div>
  );
};

export default AppShell;
