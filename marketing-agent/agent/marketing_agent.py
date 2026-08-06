"""
Marketing Automation Agent - AI Employee #7
Campaign creation, audience segmentation, content optimization, A/B testing
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from shared.llm_client import LLMClient, CircuitBreaker

logger = logging.getLogger("marketing_agent")


class Config:
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    MODEL_NAME = os.getenv("MODEL_NAME", "gemini-2.0-flash")
    TEMPERATURE = float(os.getenv("TEMPERATURE", "0.7"))
    MAX_TOKENS = int(os.getenv("MAX_TOKENS", "2048"))


class CustomerProfile(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    segment: str = "all"
    total_spent: float = 0.0
    total_orders: int = 0
    avg_order_value: float = 0.0
    last_purchase_date: Optional[str] = None
    days_since_last_purchase: Optional[int] = None
    preferred_channel: str = "email"
    tags: List[str] = Field(default_factory=list)


class CampaignRequest(BaseModel):
    trigger: str = "manual"
    customer: Optional[CustomerProfile] = None
    product: Optional[Dict[str, Any]] = None
    cart_value: Optional[float] = None
    budget: Optional[float] = None
    goal: Optional[str] = None
    brand_voice: Optional[str] = None
    campaign_type: Optional[str] = None


class CampaignContent(BaseModel):
    subject: str
    preview_text: str
    body: str
    cta_text: str
    cta_link: Optional[str] = None


class ABTestVariant(BaseModel):
    name: str
    subject: str
    body: str
    cta_text: str
    expected_improvement: str


class Campaign(BaseModel):
    campaign_id: str
    campaign_name: str
    campaign_type: str
    trigger: str
    target_segment: str
    estimated_reach: int
    estimated_ctr: float
    estimated_conversion_rate: float
    estimated_revenue: float
    campaign_cost: float
    roi: float
    content: CampaignContent
    ab_test_variants: List[ABTestVariant]
    reasoning: str
    next_best_action: Optional[str] = None


class BulkCampaignRequest(BaseModel):
    campaigns: List[CampaignRequest]


class BulkCampaignResponse(BaseModel):
    results: List[Campaign]
    summary: Dict[str, Any]


SYSTEM_PROMPT = """You are an expert Marketing Automation AI for ecommerce businesses.

YOUR ROLE:
- Create high-performing marketing campaigns that drive revenue
- Segment audiences effectively for maximum relevance
- Write compelling content that converts
- Design A/B tests to continuously improve
- Optimize budget allocation across channels

CAMPAIGN TYPES:
1. EMAIL - Personalized email sequences (Welcome, Abandoned Cart, Post-Purchase, Re-engagement)
2. SMS - Short, urgent text messages for time-sensitive offers
3. PUSH - Push notifications for mobile app users
4. SOCIAL - Social media content calendar and ad copy
5. DISCOUNT - Promotional campaigns with codes and offers
6. RETARGETING - Re-engage visitors who didn't convert

AUDIENCE SEGMENTS:
- VIP: Top 10% spenders, highest LTV, exclusive offers
- HIGH_VALUE: Regular purchasers, 5+ orders
- AT_RISK: No purchase in 30-60 days, declining engagement
- NEW: First 30 days, onboarding sequence
- LAPSED: 60+ days no purchase, win-back offers
- CART_ABANDONER: Left items in cart, recovery sequence
- PRODUCT_INTEREST: Behavior-based product targeting

CONTENT BEST PRACTICES:
- Personalize: Use customer name, recent purchases, browsing history
- Urgency: Limited-time offers, low stock alerts (authentic only)
- Clarity: One main message, one CTA (Call to Action)
- Mobile-First: Short paragraphs, clear buttons, responsive
- Value-First: What's in it for them? Lead with benefit
- Social Proof: "Join 10,000+ happy customers"
- Scarcity: "Only 5 left in stock" (must be real)

OUTPUT FORMAT (JSON):
{
    "campaign_name": "VIP Exclusive Spring Collection",
    "estimated_reach": 2500,
    "estimated_ctr": 0.045,
    "estimated_conversion_rate": 0.035,
    "estimated_revenue": 8750.00,
    "campaign_cost": 500.00,
    "roi": 16.5,
    "content": {
        "subject": "Your exclusive preview is waiting",
        "preview_text": "VIP members get first access to our Spring Collection",
        "body": "Full email body here...",
        "cta_text": "Shop the Collection"
    },
    "ab_test_variants": [...],
    "reasoning": "Detailed rationale for campaign decisions",
    "next_best_action": "Set up automation in email platform"
}

IMPORTANT:
- Always provide A/B test variants for optimization
- Estimate realistic metrics (CTR: 0.02-0.06, Conversion: 0.02-0.05)
- Campaign cost should be based on channel (email: ~$50, social: ~$500)
- All content must be CAN-SPAM and GDPR compliant
- Never use misleading subject lines or false urgency
"""


class MarketingAutomationAgent:
    """AI Marketing Automation Agent"""

    def __init__(self):
        self.config = Config()
        self.llm = LLMClient(
            system_prompt=SYSTEM_PROMPT,
            temperature=self.config.TEMPERATURE,
            max_tokens=self.config.MAX_TOKENS,
            circuit_breaker=CircuitBreaker(threshold=5, recovery_timeout=60),
        )
        self._campaign_counter = 0

    async def close(self):
        await self.llm.close()

    async def create_campaign(self, request: CampaignRequest) -> Campaign:
        self._campaign_counter += 1
        campaign_id = f"CAMP-{datetime.now().strftime('%Y%m%d')}-{self._campaign_counter:04d}"

        context = self._build_context(request)

        try:
            result = await self.llm.call(context)
            data = json.loads(result.text) if result.text else {}

            reach = int(data.get("estimated_reach", self._default_reach(request.customer.segment if request.customer else "all")))
            ctr = float(data.get("estimated_ctr", 0.03))
            conv = float(data.get("estimated_conversion_rate", 0.025))
            revenue = float(data.get("estimated_revenue", reach * ctr * conv * 50))
            cost = float(data.get("campaign_cost", self._default_cost(request.trigger)))

            ab_variants = []
            for v in data.get("ab_test_variants", []):
                ab_variants.append(ABTestVariant(
                    name=v.get("name", "Variant B"),
                    subject=v.get("subject", "Default subject"),
                    body=v.get("body", "Default body"),
                    cta_text=v.get("cta_text", "Shop Now"),
                    expected_improvement=v.get("expected_improvement", "+10%"),
                ))

            content_data = data.get("content", {})
            content = CampaignContent(
                subject=content_data.get("subject", "Check out our latest offers!"),
                preview_text=content_data.get("preview_text", "Exclusive deals inside"),
                body=content_data.get("body", "Thank you for being a valued customer."),
                cta_text=content_data.get("cta_text", "Shop Now"),
            )

            return Campaign(
                campaign_id=campaign_id,
                campaign_name=data.get("campaign_name", f"{request.trigger.title()} Campaign"),
                campaign_type=request.campaign_type or data.get("campaign_type", "email"),
                trigger=request.trigger,
                target_segment=request.customer.segment if request.customer else "all",
                estimated_reach=reach,
                estimated_ctr=ctr,
                estimated_conversion_rate=conv,
                estimated_revenue=round(revenue, 2),
                campaign_cost=round(cost, 2),
                roi=round((revenue - cost) / cost, 1) if cost > 0 else 0,
                content=content,
                ab_test_variants=ab_variants,
                reasoning=data.get("reasoning", "Campaign created based on trigger and customer data"),
                next_best_action=data.get("next_best_action", "Review and launch campaign"),
            )

        except Exception:
            return self._rule_based_campaign(request, campaign_id)

    async def create_bulk(self, request: BulkCampaignRequest) -> BulkCampaignResponse:
        results = []
        total_revenue = 0.0
        total_cost = 0.0
        type_counts = {}

        for req in request.campaigns:
            result = await self.create_campaign(req)
            results.append(result)
            total_revenue += result.estimated_revenue
            total_cost += result.campaign_cost
            t = result.campaign_type
            type_counts[t] = type_counts.get(t, 0) + 1

        return BulkCampaignResponse(
            results=results,
            summary={
                "total_campaigns": len(request.campaigns),
                "total_estimated_revenue": round(total_revenue, 2),
                "total_campaign_cost": round(total_cost, 2),
                "average_roi": round((total_revenue - total_cost) / total_cost, 1) if total_cost > 0 else 0,
                "campaign_type_breakdown": type_counts,
                "total_reach": sum(r.estimated_reach for r in results),
                "average_ctr": round(sum(r.estimated_ctr for r in results) / len(results), 3) if results else 0,
                "analysis_time": datetime.now().isoformat(),
            },
        )

    def _build_context(self, request: CampaignRequest) -> str:
        seg = request.customer.segment if request.customer else "all"
        name = request.customer.name if request.customer else "Customer"
        email = request.customer.email if request.customer else "unknown"
        spent = request.customer.total_spent if request.customer else 0
        orders = request.customer.total_orders if request.customer else 0

        return f"""
Create a marketing campaign based on this context:

Trigger: {request.trigger}
Goal: {request.goal or 'Not specified'}
Brand Voice: {request.brand_voice or 'Professional & friendly'}
Preferred Channel: {request.campaign_type or 'Not specified'}
Budget: {'$' + str(request.budget) if request.budget else 'Not specified'}

Customer:
  Segment: {seg}
  Name: {name}
  Email: {email}
  Total Spent: ${spent:.2f}
  Total Orders: {orders}
  Last Purchase: {request.customer.last_purchase_date if request.customer else 'Unknown'}

Product Info: {request.product or 'Not specified'}
Cart Value: ${request.cart_value or 0:.2f}

Provide campaign details as JSON.
"""

    def _rule_based_campaign(self, request: CampaignRequest, campaign_id: str) -> Campaign:
        seg = request.customer.segment if request.customer else "all"
        name = request.customer.name if request.customer else "there"

        if request.trigger == "cart_abandonment":
            return Campaign(
                campaign_id=campaign_id,
                campaign_name="Cart Recovery Campaign",
                campaign_type="email",
                trigger="cart_abandonment",
                target_segment=seg,
                estimated_reach=500,
                estimated_ctr=0.05,
                estimated_conversion_rate=0.03,
                estimated_revenue=2000.00,
                campaign_cost=150.00,
                roi=12.3,
                content=CampaignContent(
                    subject=f"Hey {name}, your cart is waiting!",
                    preview_text="You left items worth $200 in your cart",
                    body=f"Hi {name},\n\nYou left some items in your cart. Complete your purchase today and get 10% off with code SAVE10.\n\nYour cart is waiting for you!",
                    cta_text="Complete Your Order",
                ),
                ab_test_variants=[
                    ABTestVariant(name="Free Shipping", subject=f"{name}, free shipping inside!", body=f"Hi {name},\n\nGet free shipping on your cart items!", cta_text="Claim Free Shipping", expected_improvement="+15%"),
                ],
                reasoning="Cart abandonment recovery with 10% discount",
                next_best_action="Send email within 1 hour",
            )
        elif request.trigger == "post_purchase":
            return Campaign(
                campaign_id=campaign_id,
                campaign_name="Post-Purchase Follow-up",
                campaign_type="email",
                trigger="post_purchase",
                target_segment=seg,
                estimated_reach=1000,
                estimated_ctr=0.04,
                estimated_conversion_rate=0.02,
                estimated_revenue=1500.00,
                campaign_cost=100.00,
                roi=14.0,
                content=CampaignContent(
                    subject=f"Thanks for your order, {name}!",
                    preview_text="Here's what's next",
                    body=f"Hi {name},\n\nThanks for your purchase! We hope you love it. Here are some tips to get the most out of your product.",
                    cta_text="View Order Status",
                ),
                ab_test_variants=[
                    ABTestVariant(name="Cross-sell", subject=f"{name}, complete your look!", body=f"Hi {name},\n\nCustomers who bought this also loved...", cta_text="Shop Now", expected_improvement="+20%"),
                ],
                reasoning="Post-purchase engagement and cross-sell opportunity",
                next_best_action="Send 3 days after delivery",
            )
        elif request.trigger == "re_engagement":
            return Campaign(
                campaign_id=campaign_id,
                campaign_name="We Miss You Campaign",
                campaign_type="email",
                trigger="re_engagement",
                target_segment=seg,
                estimated_reach=5000,
                estimated_ctr=0.015,
                estimated_conversion_rate=0.01,
                estimated_revenue=5000.00,
                campaign_cost=200.00,
                roi=24.0,
                content=CampaignContent(
                    subject=f"Come back, {name}! Here's 20% off",
                    preview_text="We've been thinking about you",
                    body=f"Hi {name},\n\nIt's been a while! We'd love to welcome you back with 20% off your next order. No minimum purchase required.",
                    cta_text="Claim Your 20% Off",
                ),
                ab_test_variants=[
                    ABTestVariant(name="Free Gift", subject=f"A gift for you, {name}!", body=f"Hi {name},\n\nCome back and get a free gift with your next order!", cta_text="See Your Gift", expected_improvement="+25%"),
                ],
                reasoning="Win-back lapsed customers with 20% discount",
                next_best_action="Offer expires in 7 days",
            )
        else:
            return Campaign(
                campaign_id=campaign_id,
                campaign_name=f"Engagement Campaign - {seg.title()}",
                campaign_type="email",
                trigger=request.trigger,
                target_segment=seg,
                estimated_reach=2000,
                estimated_ctr=0.025,
                estimated_conversion_rate=0.02,
                estimated_revenue=3000.00,
                campaign_cost=150.00,
                roi=19.0,
                content=CampaignContent(
                    subject=f"Hey {name}, check out what's new!",
                    preview_text="New arrivals you might love",
                    body=f"Hi {name},\n\nWe've added new products that match your interests. Take a look!",
                    cta_text="Explore New Arrivals",
                ),
                ab_test_variants=[
                    ABTestVariant(name="Personalized", subject=f"Handpicked for you, {name}", body=f"Hi {name},\n\nBased on your previous purchases, we think you'll love these:", cta_text="Shop Your Picks", expected_improvement="+18%"),
                ],
                reasoning=f"Segment-specific engagement campaign for {seg} customers",
                next_best_action="Schedule for optimal delivery time",
            )

    def _default_reach(self, segment: str) -> int:
        reach_map = {"vip": 500, "high": 2000, "at_risk": 3000, "new": 1000, "lapsed": 5000, "cart_abandoner": 500, "all": 10000}
        return reach_map.get(segment, 1000)

    def _default_cost(self, trigger: str) -> float:
        return 200.0 if trigger in ("social", "product_launch") else 150.0


agent = MarketingAutomationAgent()
