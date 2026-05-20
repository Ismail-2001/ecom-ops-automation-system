import React from 'react';
import { AlertCircle, CheckCircle, Info, X, AlertTriangle } from 'lucide-react';

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

export const ToastContainer: React.FC<ToastContainerProps> = ({ toasts, removeToast }) => {
  return (
    <div className="fixed bottom-4 right-4 z-50 flex flex-col space-y-2 max-w-sm w-full">
      {toasts.map((toast) => {
        let bg = 'bg-slate-900 border-slate-850';
        let icon = <Info className="w-5 h-5 text-blue-400" />;
        
        if (toast.type === 'success') {
          bg = 'bg-emerald-950/90 border-emerald-500/20 text-emerald-100';
          icon = <CheckCircle className="w-5 h-5 text-emerald-400" />;
        } else if (toast.type === 'error') {
          bg = 'bg-red-950/90 border-red-500/20 text-red-100';
          icon = <AlertCircle className="w-5 h-5 text-red-400" />;
        } else if (toast.type === 'warning') {
          bg = 'bg-amber-950/90 border-amber-500/20 text-amber-100';
          icon = <AlertTriangle className="w-5 h-5 text-amber-400" />;
        }

        return (
          <div
            key={toast.id}
            className={`flex items-start p-4 rounded-lg border shadow-lg backdrop-blur-sm transition-all duration-300 transform translate-y-0 ${bg}`}
          >
            <div className="flex-shrink-0 mr-3 mt-0.5">{icon}</div>
            <div className="flex-grow mr-2">
              <h4 className="text-sm font-semibold">{toast.title}</h4>
              <p className="text-xs text-slate-300 mt-1">{toast.message}</p>
            </div>
            <button
              onClick={() => removeToast(toast.id)}
              className="flex-shrink-0 text-slate-400 hover:text-slate-200 transition-colors"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        );
      })}
    </div>
  );
};
