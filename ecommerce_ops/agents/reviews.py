from typing import Dict, Any, List
from ecommerce_ops.agents._base import BaseAgent
from ecommerce_ops.config import settings

class ReviewsAgent(BaseAgent):
    def __init__(self):
        super().__init__("ReviewsAgent")

    async def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Classifies reviews and drafts responses.
        """
        reviews = state.get("reviews_data", [])
        decisions = []

        for review in reviews:
            content = review.get("content", "")
            rating = review.get("rating", 0)
            
            # Use DeepSeek for sentiment and draft
            analysis = await self._analyze_review(content, rating)
            
            requires_approval = rating < 4 or analysis.get("contains_refund_offer", False)
            
            decision = self.create_decision(
                action_type="POST_REVIEW_RESPONSE",
                reasoning=f"Review rating {rating}. Sentiment: {analysis.get('sentiment')}. Drafted response in store voice.",
                data={
                    "review_id": review.get("id"),
                    "response_content": analysis.get("response"),
                    "sentiment": analysis.get("sentiment"),
                    "themes": analysis.get("themes")
                },
                confidence=analysis.get("confidence", 0.5),
                requires_approval=requires_approval
            )
            decisions.append(decision)
            self.log_audit(decision)

        state["decisions"] = state.get("decisions", []) + decisions
        return state

    async def _analyze_review(self, content: str, rating: int) -> Dict[str, Any]:
        """Call DeepSeek to analyze and draft."""
        prompt = f"""
        Analyze this customer review: "{content}" (Rating: {rating}/5)
        
        Task:
        1. Determine sentiment (Positive, Neutral, Negative).
        2. Extract themes (Shipping, Quality, Sizing, Support).
        3. Draft a response in a professional yet friendly "store voice".
        4. Output JSON with keys: sentiment, themes, response, contains_refund_offer, confidence.
        """
        # In a real run, this uses self.llm.invoke()
        # Mocking the output for now
        return {
            "sentiment": "Positive" if rating >= 4 else "Negative",
            "themes": ["Quality"],
            "response": f"Thank you for your {rating}-star review! We are glad you liked it.",
            "contains_refund_offer": False,
            "confidence": 0.95
        }
