import React from 'react';

export const CardSkeleton: React.FC = () => {
  return (
    <div className="bg-slate-900 border border-slate-800 rounded-lg p-4 mb-3 animate-shimmer">
      <div className="flex justify-between items-start mb-3">
        <div className="flex space-x-2">
          <div className="h-5 w-24 bg-slate-850 rounded" />
          <div className="h-5 w-16 bg-slate-850 rounded" />
        </div>
        <div className="h-5 w-16 bg-slate-850 rounded" />
      </div>
      <div className="h-4 w-3/4 bg-slate-850 rounded mb-2" />
      <div className="h-3 w-1/2 bg-slate-850 rounded mb-4" />
      <div className="flex justify-between items-center border-t border-slate-800 pt-3">
        <div className="h-4 w-20 bg-slate-850 rounded" />
        <div className="h-6 w-24 bg-slate-850 rounded" />
      </div>
    </div>
  );
};

export const DetailSkeleton: React.FC = () => {
  return (
    <div className="p-6 space-y-6 animate-shimmer">
      {/* Header */}
      <div className="space-y-3">
        <div className="flex space-x-3">
          <div className="h-6 w-28 bg-slate-850 rounded" />
          <div className="h-6 w-20 bg-slate-850 rounded" />
        </div>
        <div className="h-8 w-2/3 bg-slate-850 rounded" />
        <div className="h-4 w-1/3 bg-slate-850 rounded" />
      </div>

      <hr className="border-slate-850" />

      {/* Grid Summary */}
      <div className="grid grid-cols-3 gap-4">
        {[1, 2, 3].map((i) => (
          <div key={i} className="bg-slate-900/50 p-3 rounded-lg border border-slate-850 space-y-2">
            <div className="h-3 w-16 bg-slate-850 rounded" />
            <div className="h-5 w-24 bg-slate-850 rounded" />
          </div>
        ))}
      </div>

      {/* Main Details block */}
      <div className="space-y-4">
        <div className="h-5 w-32 bg-slate-850 rounded" />
        <div className="bg-slate-900 border border-slate-850 rounded-lg p-4 space-y-3">
          {[1, 2, 3].map((i) => (
            <div key={i} className="flex justify-between py-1">
              <div className="h-4 w-24 bg-slate-850 rounded" />
              <div className="h-4 w-40 bg-slate-850 rounded" />
            </div>
          ))}
        </div>
      </div>

      {/* Evidence */}
      <div className="space-y-4">
        <div className="h-5 w-40 bg-slate-850 rounded" />
        <div className="grid grid-cols-2 gap-4">
          {[1, 2].map((i) => (
            <div key={i} className="bg-slate-900 border border-slate-850 p-3 rounded-lg space-y-2">
              <div className="h-3.5 w-20 bg-slate-850 rounded" />
              <div className="h-4 w-32 bg-slate-850 rounded" />
            </div>
          ))}
        </div>
      </div>

      {/* Action buttons */}
      <div className="flex space-x-3 pt-6">
        <div className="h-10 flex-1 bg-slate-850 rounded" />
        <div className="h-10 flex-1 bg-slate-850 rounded" />
      </div>
    </div>
  );
};

export const TableRowSkeleton: React.FC = () => {
  return (
    <tr className="border-b border-slate-900/60 animate-shimmer">
      {[1, 2, 3, 4, 5, 6].map((i) => (
        <td key={i} className="px-6 py-4">
          <div className="h-4 bg-slate-850 rounded w-full" />
        </td>
      ))}
    </tr>
  );
};

export const ChartSkeleton: React.FC = () => {
  return (
    <div className="h-64 bg-slate-900/40 border border-slate-800 rounded-xl p-4 flex flex-col justify-between animate-shimmer">
      <div className="flex justify-between items-center mb-4">
        <div className="h-5 w-32 bg-slate-850 rounded" />
        <div className="flex space-x-2">
          <div className="h-4 w-12 bg-slate-850 rounded" />
          <div className="h-4 w-12 bg-slate-850 rounded" />
        </div>
      </div>
      <div className="flex items-end justify-between flex-1 space-x-4 px-2">
        {[40, 80, 60, 90, 50, 70, 85].map((h, i) => (
          <div key={i} className="bg-slate-850 rounded-t w-full" style={{ height: `${h}%` }} />
        ))}
      </div>
      <div className="flex justify-between mt-2 pt-2 border-t border-slate-850">
        {[1, 2, 3, 4, 5, 6, 7].map((i) => (
          <div key={i} className="h-3 w-8 bg-slate-850 rounded" />
        ))}
      </div>
    </div>
  );
};
