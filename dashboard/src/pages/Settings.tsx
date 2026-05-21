import React, { useState, useEffect } from 'react';
import { useOutletContext } from 'react-router-dom';
import { 
  Settings as SettingsIcon, 
  Eye, 
  ShieldCheck, 
  AlertTriangle,
  Save,
  RotateCcw
} from 'lucide-react';
import { useSettings } from '../hooks/useSettings';
import { Card } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { motion } from 'framer-motion';

export const Settings: React.FC = () => {
  const { triggerToast } = useOutletContext<{ triggerToast: any }>();
  const { settings, isLoading, updateSettings, isUpdating } = useSettings();

  // Local Form state
  const [shadowMode, setShadowMode] = useState(false);
  const [fraudThreshold, setFraudThreshold] = useState(70);
  const [poLimit, setPoLimit] = useState(1000.0);
  const [pricingLimit, setPricingLimit] = useState(10.0);
  const [reviewsThreshold, setReviewsThreshold] = useState(3);

  // Sync state when database settings load
  useEffect(() => {
    if (settings) {
      setShadowMode(settings.shadow_mode);
      setFraudThreshold(settings.fraud_threshold);
      setPoLimit(settings.po_limit);
      setPricingLimit(settings.pricing_limit);
      setReviewsThreshold(settings.reviews_rating_threshold);
    }
  }, [settings]);

  if (isLoading || !settings) {
    return (
      <div className="space-y-6 animate-pulse select-none">
        <div className="h-8 w-48 bg-slate-800/50 rounded-lg" />
        <Card className="h-64 bg-slate-900/30" />
      </div>
    );
  }

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await updateSettings({
        shadow_mode: shadowMode,
        fraud_threshold: fraudThreshold,
        po_limit: poLimit,
        pricing_limit: pricingLimit,
        reviews_rating_threshold: reviewsThreshold,
      });
      triggerToast('Settings Saved', 'System configurations and safety thresholds have been saved.', 'success');
    } catch (err) {
      console.error(err);
      triggerToast('Error', 'Failed to update safety configurations.', 'error');
    }
  };

  const handleReset = () => {
    if (settings) {
      setShadowMode(settings.shadow_mode);
      setFraudThreshold(settings.fraud_threshold);
      setPoLimit(settings.po_limit);
      setPricingLimit(settings.pricing_limit);
      setReviewsThreshold(settings.reviews_rating_threshold);
      triggerToast('Form Reset', 'Reverted unsaved edits back to system state.', 'info');
    }
  };

  return (
    <div className="max-w-3xl space-y-6">
      {/* Page Header */}
      <div className="select-none">
        <h1 className="text-2xl font-black text-slate-100 flex items-center tracking-tight">
          <SettingsIcon className="w-6 h-6 mr-3 text-blue-500" />
          Safety Config & Thresholds
        </h1>
        <p className="text-xs text-slate-400 mt-1">
          Adjust risk evaluation parameters and autonomous safety controls for e-commerce agents.
        </p>
      </div>

      <form onSubmit={handleSave} className="space-y-6">
        {/* 1. Shadow Mode Control Banner */}
        <Card className="bg-slate-900/40 border-white/5 p-6 space-y-4">
          <div className="flex items-start justify-between">
            <div className="space-y-1">
              <h3 className="text-sm font-bold text-slate-200 flex items-center">
                <Eye className="w-4 h-4 mr-2 text-amber-500" />
                Pipeline Shadow Simulation Mode
              </h3>
              <p className="text-xs text-slate-400 leading-relaxed max-w-lg">
                When enabled, approved decisions are logged as successful simulations instead of executing mutations against the live Shopify store. Excellent for dry runs or staging testing.
              </p>
            </div>

            {/* Toggle Switch */}
            <button
              type="button"
              onClick={() => setShadowMode(!shadowMode)}
              className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors duration-200 focus:outline-none focus:ring-1 focus:ring-amber-500/40 ${
                shadowMode ? 'bg-amber-600' : 'bg-slate-800'
              }`}
            >
              <motion.span
                layout
                transition={{ type: "spring", stiffness: 700, damping: 30 }}
                className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                  shadowMode ? 'translate-x-6' : 'translate-x-1'
                }`}
              />
            </button>
          </div>

          <hr className="border-white/5" />

          <div className={`p-4 rounded-xl border text-xs leading-relaxed flex items-start space-x-3 select-none transition-colors duration-300 ${
            shadowMode 
              ? 'bg-amber-500/10 border-amber-500/20 text-amber-300' 
              : 'bg-emerald-500/10 border-emerald-500/20 text-emerald-300'
          }`}>
            <AlertTriangle className="w-4 h-4 flex-shrink-0 mt-0.5" />
            <div>
              <span className="font-bold block uppercase tracking-wider mb-1">
                {shadowMode ? 'Simulation Active' : 'Live Mode Active'}
              </span>
              <span>
                {shadowMode 
                  ? 'All agents will run in isolation. Database changes are logged without calling external APIs.' 
                  : 'Safety parameters are active. Approved decisions will write directly to Shopify and Stripe integrations.'}
              </span>
            </div>
          </div>
        </Card>

        {/* 2. Threshold Controls */}
        <Card className="bg-slate-900/40 border-white/5 p-6 space-y-6">
          <h3 className="text-sm font-bold text-slate-200 flex items-center select-none">
            <ShieldCheck className="w-4 h-4 mr-2 text-blue-500" />
            Agent Interception Thresholds
          </h3>
          
          <hr className="border-white/5" />

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Fraud threshold */}
            <div className="space-y-2">
              <label className="text-xs font-bold text-slate-300 block">
                Fraud Score Intervention Threshold (Stripe)
              </label>
              <p className="text-[11px] text-slate-500">
                Intercept decisions and request approval if transaction risk score is greater than or equal to this limit.
              </p>
              <div className="flex items-center space-x-3">
                <input
                  type="range"
                  min="0"
                  max="100"
                  value={fraudThreshold}
                  onChange={(e) => setFraudThreshold(parseInt(e.target.value))}
                  className="flex-1 h-1 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-blue-500"
                />
                <span className="w-12 text-center text-xs font-bold font-mono bg-slate-950 border border-white/10 px-2 py-1.5 rounded-lg text-slate-350 select-none">
                  {fraudThreshold}%
                </span>
              </div>
            </div>

            {/* Purchase order limit */}
            <div className="space-y-2">
              <label className="text-xs font-bold text-slate-300 block">
                Purchase Order Authorization Limit (USD)
              </label>
              <p className="text-[11px] text-slate-500">
                Automatically halt and queue any Inventory restocking orders whose total value exceeds this limit.
              </p>
              <div className="relative">
                <span className="absolute left-3 top-2.5 text-xs text-slate-500 select-none">$</span>
                <input
                  type="number"
                  min="0"
                  step="100"
                  value={poLimit}
                  onChange={(e) => setPoLimit(parseFloat(e.target.value) || 0)}
                  className="w-full bg-slate-950/80 border border-white/10 rounded-lg pl-8 pr-4 py-2 text-xs font-mono text-slate-100 focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500 transition-all"
                />
              </div>
            </div>

            {/* Pricing Deviation */}
            <div className="space-y-2">
              <label className="text-xs font-bold text-slate-300 block">
                Pricing Discrepancy Limit (%)
              </label>
              <p className="text-[11px] text-slate-500">
                Require human confirmation if any competitor adjustment markup or markdown deviation exceeds this scale.
              </p>
              <div className="relative">
                <input
                  type="number"
                  min="0"
                  max="100"
                  step="0.5"
                  value={pricingLimit}
                  onChange={(e) => setPricingLimit(parseFloat(e.target.value) || 0)}
                  className="w-full bg-slate-950/80 border border-white/10 rounded-lg px-3 py-2 text-xs font-mono text-slate-100 focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500 transition-all"
                />
                <span className="absolute right-3 top-2.5 text-xs text-slate-500 select-none">%</span>
              </div>
            </div>

            {/* Reviews threshold */}
            <div className="space-y-2">
              <label className="text-xs font-bold text-slate-300 block">
                Review Rating Intercept Threshold
              </label>
              <p className="text-[11px] text-slate-500">
                Trigger human approval queue for review responses on reviews with a star rating less than or equal to this.
              </p>
              <select
                value={reviewsThreshold}
                onChange={(e) => setReviewsThreshold(parseInt(e.target.value))}
                className="w-full bg-slate-950/80 border border-white/10 rounded-lg px-3 py-2 text-xs text-slate-300 focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500 transition-all"
              >
                <option value="1">1 Star or less</option>
                <option value="2">2 Stars or less</option>
                <option value="3">3 Stars or less</option>
                <option value="4">4 Stars or less</option>
                <option value="5">All review responses (5 Stars or less)</option>
              </select>
            </div>
          </div>
        </Card>

        {/* 3. Submit Buttons */}
        <div className="flex justify-end space-x-3 select-none">
          <Button
            type="button"
            variant="outline"
            onClick={handleReset}
            disabled={isUpdating}
            className="flex items-center text-xs"
          >
            <RotateCcw className="w-3.5 h-3.5 mr-1.5" />
            Reset Edits
          </Button>
          <Button
            type="submit"
            disabled={isUpdating}
            className="flex items-center text-xs"
          >
            <Save className="w-3.5 h-3.5 mr-1.5" />
            {isUpdating ? 'Saving Changes...' : 'Save Thresholds'}
          </Button>
        </div>
      </form>
    </div>
  );
};

export default Settings;
