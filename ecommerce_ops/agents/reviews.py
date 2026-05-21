from typing import Dict, Any, List
from ecommerce_ops.agents._base import BaseAgent
from ecommerce_ops.config import settings
from pydantic import BaseModel, Field
import structlog

logger = structlog.get_logger(__name__)

class ReviewAnalysisOutput(BaseModel):
    sentiment: str = Field(description="The sentiment of the review: Positive, Neutral, or Negative.")
    themes: List[str] = Field(description="Key themes extracted from the review, e.g., Shipping, Quality, Sizing, Support.")
    response: str = Field(description="A drafted response to the customer in a professional yet friendly store voice.")
    contains_refund_offer: bool = Field(description="True if the response offers a refund, False otherwise.")
    confidence: float = Field(description="Confidence score of the analysis between 0.0 and 1.0.")

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
        """Call DeepSeek to analyze and draft via LangChain structured output."""
        prompt = (
            f"Analyze this customer review: \"{content}\" (Rating: {rating}/5)\n\n"
            "Task:\n"
            "1. Determine sentiment (Positive, Neutral, Negative).\n"
            "2. Extract themes (Shipping, Quality, Sizing, Support).\n"
            "3. Draft a response in a professional yet friendly 'store voice'.\n"
            "4. Determine if a refund is offered.\n"
            "5. Provide a confidence score.\n"
        )
        
        try:
            structured_llm = self.llm.with_structured_output(ReviewAnalysisOutput)
            result = await structured_llm.ainvoke(prompt)
            
            logger.info(f"LLM analyzed review with sentiment {result.sentiment}")
            return result.model_dump()
            
        except Exception as e:
            logger.error(f"LLM analysis failed for review: {e}")
            # Fallback mock response
            return {
                "sentiment": "Positive" if rating >= 4 else "Negative",
                "themes": ["Unknown"],
                "response": f"Thank you for your {rating}-star review! We appreciate your feedback.",
                "contains_refund_offer": False,
                "confidence": 0.5
            }

