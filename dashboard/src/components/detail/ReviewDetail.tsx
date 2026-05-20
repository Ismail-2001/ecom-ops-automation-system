import React, { useState, useEffect } from 'react';
import { MessageSquare, Star, Smile, Meh, Frown, Edit3 } from 'lucide-react';
import type { ReviewPayload } from '../../types/action';

interface ReviewDetailProps {
  payload: ReviewPayload;
  onChangeDraft: (draft: string) => void;
}

export const ReviewDetail: React.FC<ReviewDetailProps> = ({ payload, onChangeDraft }) => {
  const [draftReply, setDraftReply] = useState(payload.draft_response);

  // Sync draft value if payload updates
  useEffect(() => {
    setDraftReply(payload.draft_response);
  }, [payload.draft_response]);

  const handleReplyChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const val = e.target.value;
    setDraftReply(val);
    onChangeDraft(val);
  };

  const getSentimentIcon = (sentiment: string) => {
    const norm = (sentiment || '').toLowerCase();
    if (norm === 'positive') return <Smile className="w-4 h-4 text-emerald-400 mr-1.5" />;
    if (norm === 'negative') return <Frown className="w-4 h-4 text-red-400 mr-1.5" />;
    return <Meh className="w-4 h-4 text-amber-400 mr-1.5" />;
  };

  const ratingStars = Array.from({ length: 5 }, (_, i) => (
    <Star
      key={i}
      className={`w-4 h-4 ${
        i < payload.rating ? 'text-yellow-400 fill-current' : 'text-slate-700'
      }`}
    />
  ));

  return (
    <div className="space-y-6 select-none">
      {/* Customer Review Details */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-4">
        {/* Header: Customer Name and Rating */}
        <div className="flex items-center justify-between">
          <div>
            <h4 className="text-sm font-bold text-slate-200">{payload.customer_name}</h4>
            <span className="text-[10px] text-slate-500 font-medium">Customer Verified Purchase</span>
          </div>
          <div className="flex items-center space-x-1">{ratingStars}</div>
        </div>

        <hr className="border-slate-850" />

        {/* Sentiment & Issues Row */}
        <div className="flex flex-wrap items-center gap-2 text-xs">
          <span className="inline-flex items-center px-2 py-0.5 rounded border bg-slate-950 border-slate-850 text-slate-300 font-medium">
            {getSentimentIcon(payload.sentiment)}
            {payload.sentiment} Sentiment
          </span>

          {payload.key_issues && payload.key_issues.map((theme, i) => (
            <span key={i} className="px-2 py-0.5 rounded border bg-red-500/10 border-red-500/20 text-red-400 font-semibold uppercase text-[9px] tracking-wider">
              {theme}
            </span>
          ))}
        </div>

        {/* Review body */}
        <div className="bg-slate-950 p-4 rounded-lg border border-slate-850/80">
          <p className="text-xs text-slate-300 leading-relaxed italic">
            "{payload.review_text || 'No review text provided.'}"
          </p>
        </div>
      </div>

      {/* Editable Response Draft */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <h4 className="text-xs font-bold text-slate-300 uppercase tracking-wider flex items-center">
            <MessageSquare className="w-4 h-4 mr-2 text-slate-400" />
            Proposed Response Draft
          </h4>
          <span className="text-[10px] text-blue-400 font-medium flex items-center">
            <Edit3 className="w-3.5 h-3.5 mr-1" />
            Editable Response
          </span>
        </div>

        <textarea
          value={draftReply}
          onChange={handleReplyChange}
          className="w-full min-h-[160px] bg-slate-900 border border-slate-800 focus:border-blue-500 focus:ring-1 focus:ring-blue-500/20 rounded-xl p-4 text-xs text-slate-100 placeholder-slate-500 leading-relaxed focus:outline-none"
          placeholder="Write your custom review reply draft..."
        />
        <p className="text-[10px] text-slate-500">
          Review response drafts will be posted to the live Shopify storefront immediately upon approval.
        </p>
      </div>
    </div>
  );
};

export default ReviewDetail;
