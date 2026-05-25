import React, { useState, useEffect } from 'react';
import { MessageSquare, Star, Smile, Meh, Frown, Edit3 } from 'lucide-react';
import type { ReviewPayload } from '../../types/action';
import { Card } from '../ui/Card';
import { Badge } from '../ui/Badge';

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
    if (norm === 'positive') return <Smile className="w-4 h-4 mr-1.5 flex-shrink-0" />;
    if (norm === 'negative') return <Frown className="w-4 h-4 mr-1.5 flex-shrink-0" />;
    return <Meh className="w-4 h-4 mr-1.5 flex-shrink-0" />;
  };

  const ratingStars = Array.from({ length: 5 }, (_, i) => (
    <Star
      key={i}
      className={`w-4 h-4 transition-all duration-300 ${
        i < payload.rating 
          ? 'text-amber-400 fill-amber-400 filter drop-shadow-[0_0_4px_rgba(251,191,36,0.5)]' 
          : 'text-slate-700'
      }`}
    />
  ));

  return (
    <div className="space-y-6 select-none animate-fadeIn">
      {/* Customer Review Details */}
      <Card className="bg-slate-900/40 p-6 space-y-4">
        {/* Header: Customer Name and Rating */}
        <div className="flex items-center justify-between">
          <div>
            <h4 className="text-sm font-bold text-slate-200">{payload.customer_name}</h4>
            <span className="text-[10px] text-slate-500 font-medium">Customer Verified Purchase</span>
          </div>
          <div className="flex items-center space-x-1">{ratingStars}</div>
        </div>

        <hr className="border-white/5" />

        {/* Sentiment & Issues Row */}
        <div className="flex flex-wrap items-center gap-2">
          <Badge 
            variant={
              payload.sentiment?.toLowerCase() === 'positive' 
                ? 'success' 
                : payload.sentiment?.toLowerCase() === 'negative' 
                  ? 'destructive' 
                  : 'warning'
            }
            className="capitalize"
          >
            {getSentimentIcon(payload.sentiment)}
            {payload.sentiment} Sentiment
          </Badge>

          {payload.key_issues && payload.key_issues.map((theme, i) => (
            <Badge key={i} variant="destructive" className="uppercase text-[9px] tracking-wider font-semibold">
              {theme}
            </Badge>
          ))}
        </div>

        {/* Review body */}
        <div className="bg-slate-950/60 p-4 rounded-xl border border-white/5 relative overflow-hidden">
          <div className="absolute -right-2 -bottom-6 text-white/5 text-7xl font-serif select-none pointer-events-none">
            ”
          </div>
          <p className="text-xs text-slate-300 leading-relaxed italic relative z-10">
            "{payload.review_text || 'No review text provided.'}"
          </p>
        </div>
      </Card>

      {/* Editable Response Draft */}
      <div className="space-y-3">
        <div className="flex items-center justify-between px-1">
          <h4 className="text-xs font-bold text-slate-300 uppercase tracking-wider flex items-center">
            <MessageSquare className="w-4 h-4 mr-2 text-slate-400" />
            Proposed Response Draft
          </h4>
          <span className="text-[10px] text-blue-400 font-medium flex items-center bg-blue-500/10 border border-blue-500/20 px-2 py-0.5 rounded-full">
            <Edit3 className="w-3 h-3 mr-1" />
            Editable Response
          </span>
        </div>

        <textarea
          value={draftReply}
          onChange={handleReplyChange}
          className="w-full min-h-[160px] bg-slate-900/40 border border-white/5 focus:border-blue-500/80 focus:ring-1 focus:ring-blue-500/20 rounded-xl p-4 text-xs text-slate-100 placeholder-slate-500 leading-relaxed focus:outline-none transition-all duration-200 resize-none shadow-inner"
          placeholder="Write your custom review reply draft..."
        />
        <p className="text-[10px] text-slate-500 px-1">
          Review response drafts will be posted to the live Shopify storefront immediately upon approval.
        </p>
      </div>
    </div>
  );
};

export default ReviewDetail;
