import React from 'react';
import { AlertCircle, CheckCircle, Info, X, AlertTriangle } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

export interface Toast {
  id: string;
  title: string;
  message: string;
  type: 'info' | 'success' | 'warning' | 'error';
}

interface ToastContainerProps {
  toasts: Toast[];
  removeToast: (id: string) => void;
}

const toastStyles = {
  info:    { bg: 'rgba(37,99,235,0.12)',  border: 'rgba(59,130,246,0.25)',  color: '#60a5fa',  icon: <Info size={16} color="#60a5fa" /> },
  success: { bg: 'rgba(16,185,129,0.12)', border: 'rgba(16,185,129,0.25)', color: '#34d399',  icon: <CheckCircle size={16} color="#34d399" /> },
  warning: { bg: 'rgba(245,158,11,0.12)', border: 'rgba(245,158,11,0.25)', color: '#fbbf24',  icon: <AlertTriangle size={16} color="#fbbf24" /> },
  error:   { bg: 'rgba(244,63,94,0.12)',  border: 'rgba(244,63,94,0.25)',  color: '#fb7185',  icon: <AlertCircle size={16} color="#fb7185" /> },
};

export const ToastContainer: React.FC<ToastContainerProps> = ({ toasts, removeToast }) => {
  return (
    <div style={{ position: 'fixed', bottom: '20px', right: '20px', zIndex: 9999, display: 'flex', flexDirection: 'column', gap: '8px', maxWidth: '360px', width: '100%' }}>
      <AnimatePresence>
        {toasts.map((toast) => {
          const s = toastStyles[toast.type];
          return (
            <motion.div
              key={toast.id}
              initial={{ opacity: 0, x: 40, scale: 0.95 }}
              animate={{ opacity: 1, x: 0, scale: 1 }}
              exit={{ opacity: 0, x: 40, scale: 0.92 }}
              transition={{ type: 'spring', stiffness: 400, damping: 30 }}
              style={{
                display: 'flex', alignItems: 'flex-start', gap: '12px',
                padding: '14px 16px',
                borderRadius: '12px',
                background: 'rgba(13,17,23,0.92)',
                backdropFilter: 'blur(24px)',
                border: `1px solid ${s.border}`,
                boxShadow: `0 8px 32px rgba(0,0,0,0.5), 0 0 0 1px ${s.border}`,
              }}
            >
              <div style={{ flexShrink: 0, marginTop: '1px' }}>{s.icon}</div>
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ fontSize: '13px', fontWeight: 700, color: '#f1f5f9', marginBottom: '3px' }}>{toast.title}</div>
                <div style={{ fontSize: '12px', color: '#64748b', lineHeight: '1.45' }}>{toast.message}</div>
              </div>
              <button
                onClick={() => removeToast(toast.id)}
                style={{
                  flexShrink: 0, background: 'none', border: 'none', cursor: 'pointer',
                  color: '#475569', padding: '2px', borderRadius: '4px', lineHeight: 1,
                  transition: 'color 0.15s',
                }}
                onMouseEnter={(e) => ((e.currentTarget as HTMLElement).style.color = '#94a3b8')}
                onMouseLeave={(e) => ((e.currentTarget as HTMLElement).style.color = '#475569')}
              >
                <X size={14} />
              </button>
            </motion.div>
          );
        })}
      </AnimatePresence>
    </div>
  );
};
