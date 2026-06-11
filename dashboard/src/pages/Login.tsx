import React, { useState } from 'react';
import { Shield, Eye, KeyRound } from 'lucide-react';
import { motion } from 'framer-motion';
import { useAuth } from '../hooks/useAuth';
import { Button } from '../components/ui/Button';

export const Login: React.FC = () => {
  const { login } = useAuth();
  const [apiKey, setApiKey] = useState('');
  const [operatorId, setOperatorId] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      await login(apiKey, operatorId || undefined);
    } catch {
      setError('Invalid API key. Check your credentials and try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center relative overflow-hidden"
      style={{ background: '#02030a' }}>
      <div className="pointer-events-none absolute inset-0 z-0"
        style={{
          background: `
            radial-gradient(ellipse 60% 40% at 50% 0%, rgba(37,99,235,0.12) 0%, transparent 70%),
            radial-gradient(ellipse 50% 40% at 50% 100%, rgba(124,58,237,0.08) 0%, transparent 70%)
          `,
        }}
      />
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="relative z-10 w-full max-w-md mx-4"
      >
        <div className="bg-slate-900/80 border border-white/10 rounded-2xl p-8 shadow-2xl backdrop-blur-xl">
          <div className="text-center mb-8">
            <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-blue-600/20 border border-blue-500/20 mb-4">
              <Shield className="w-8 h-8 text-blue-500" />
            </div>
            <h1 className="text-2xl font-black text-slate-100 tracking-tight">OpsIQ</h1>
            <p className="text-sm text-slate-400 mt-1">Autonomous Commerce Engine</p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-5">
            <div className="space-y-2">
              <label className="text-xs font-bold text-slate-300 uppercase tracking-wider flex items-center">
                <KeyRound className="w-3.5 h-3.5 mr-1.5 text-blue-400" />
                API Key
              </label>
              <input
                type="password"
                value={apiKey}
                onChange={(e) => setApiKey(e.target.value)}
                placeholder="Enter your API key"
                required
                className="w-full bg-slate-950/80 border border-white/10 rounded-xl px-4 py-3 text-sm text-slate-100 placeholder-slate-600 focus:outline-none focus:ring-2 focus:ring-blue-500/30 focus:border-blue-500/50 transition-all font-mono"
              />
            </div>

            <div className="space-y-2">
              <label className="text-xs font-bold text-slate-300 uppercase tracking-wider flex items-center">
                <Eye className="w-3.5 h-3.5 mr-1.5 text-blue-400" />
                Operator ID (optional)
              </label>
              <input
                type="text"
                value={operatorId}
                onChange={(e) => setOperatorId(e.target.value)}
                placeholder="your-name"
                className="w-full bg-slate-950/80 border border-white/10 rounded-xl px-4 py-3 text-sm text-slate-100 placeholder-slate-600 focus:outline-none focus:ring-2 focus:ring-blue-500/30 focus:border-blue-500/50 transition-all font-mono"
              />
            </div>

            {error && (
              <div className="p-3 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 text-xs text-center">
                {error}
              </div>
            )}

            <Button
              type="submit"
              disabled={loading || !apiKey}
              className="w-full py-3 text-sm font-bold"
            >
              {loading ? 'Authenticating...' : 'Sign In'}
            </Button>
          </form>

          <p className="mt-6 text-center text-[11px] text-slate-600">
            Authorized operators only. All actions are logged.
          </p>
        </div>
      </motion.div>
    </div>
  );
};

export default Login;
