import React from 'react';
import { Eye, ShieldAlert } from 'lucide-react';
import { useSettings } from '../../hooks/useSettings';

export const ShadowModeBanner: React.FC = () => {
  const { settings, isLoading } = useSettings();

  if (isLoading || !settings || !settings.shadow_mode) {
    return null;
  }

  return (
    <div className="bg-amber-600/90 text-amber-950 px-4 py-2 border-b border-amber-500/30 flex items-center justify-between text-xs font-semibold shadow-md backdrop-blur-sm sticky top-0 z-50 select-none">
      <div className="flex items-center space-x-2 mx-auto">
        <div className="relative flex h-2 w-2">
          <span className="animate-pulse-ring absolute inline-flex h-full w-full rounded-full bg-amber-950 opacity-75"></span>
          <span className="relative inline-flex rounded-full h-2 w-2 bg-amber-950"></span>
        </div>
        <ShieldAlert className="w-4 h-4 text-amber-950" />
        <span>SHADOW MODE ACTIVE: ALL COMPLETED APPROVALS ARE LOGGED AS SIMULATIONS AND WILL NOT MUTATE LIVE SHOPIFY STORE DATA</span>
      </div>
      <div className="flex items-center space-x-1 text-[10px] bg-amber-950/10 px-2 py-0.5 rounded border border-amber-950/20">
        <Eye className="w-3.5 h-3.5" />
        <span>MONITOR MODE</span>
      </div>
    </div>
  );
};

export default ShadowModeBanner;
