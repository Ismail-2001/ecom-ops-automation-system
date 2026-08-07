"""
Cart Recovery Agent - AI Employee #5
Abandoned cart detection, recovery strategies, discount code generation
"""

import os
import json
import re
import logging
import secrets
import string
import hashlib
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Any, Tuple
from pydantic import BaseModel, Field
from shared.llm_client import LLMClient, CircuitBreaker

try:
    from ecommerce_ops.safety.guardrails import guardrail_manager
except ImportError:
    guardrail_manager = None

logger = logging.getLogger("cart_recovery_agent")


class Config:
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    MODEL_NAME = os.getenv("MODEL_NAME", "gemini-2.0-flash")
    TEMPERATURE = float(os.getenv("TEMPERATURE", "0.3"))
    MAX_TOKENS = int(os.getenv("MAX_TOKENS", "1024"))


class CartStatus(str, Enum):
    ABANDONED = "abandoned"
    RECOVERY_PENDING = "recovery_pending"
    RECOVERY_SENT = "recovery_sent"
    RECOVERED = "recovered"
    EXPIRED = "expired"
    LOST = "lost"


class RecoveryStrategy(str, Enum):
    DISCOUNT_PERCENT = "discount_percent"
    DISCOUNT_FIXED = "discount_fixed"
    FREE_SHIPPING = "free_shipping"
    URGENCY = "urgency"
    SOCIAL_PROOF = "social_proof"
    PERSONAL_OUTREACH = "personal_outreach"


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class CartItem(BaseModel):
    product_id: str
    title: str
    quantity: int = 1
    price: float = 0.0
    total: float = 0.0
    sku: Optional[str] = None
    image_url: Optional[str] = None
    product_type: Optional[str] = None
    vendor: Optional[str] = None


class CustomerProfile(BaseModel):
    email: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    total_orders: int = 0
    total_spent: float = 0.0
    average_order_value: float = 0.0
    is_repeat_customer: bool = False
    segment: str = "new"

    @property
    def lifetime_value_tier(self) -> str:
        if self.total_spent > 500:
            return "vip"
        elif self.total_spent > 200:
            return "high"
        elif self.total_spent > 50:
            return "medium"
        return "low"


class AbandonedCart(BaseModel):
    cart_id: str
    customer: Optional[CustomerProfile] = None
    items: List[CartItem] = Field(default_factory=list)
    total_value: float = 0.0
    currency: str = "USD"
    items_count: int = 0
    status: CartStatus = CartStatus.ABANDONED
    checkout_url: Optional[str] = None
    abandoned_hours: Optional[float] = None
    shop_domain: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @property
    def is_recoverable(self) -> bool:
        return self.status in (CartStatus.ABANDONED, CartStatus.RECOVERY_PENDING, CartStatus.RECOVERY_SENT)

    @property
    def recovery_probability(self) -> float:
        score = 0.0
        if self.total_value > 100:
            score += 0.3
        elif self.total_value > 50:
            score += 0.2
        elif self.total_value > 20:
            score += 0.1
        if self.customer:
            if self.customer.is_repeat_customer:
                score += 0.25
            if self.customer.total_orders > 5:
                score += 0.15
        if self.items_count > 3:
            score += 0.1
        elif self.items_count > 1:
            score += 0.05
        if self.abandoned_hours and self.abandoned_hours < 1:
            score += 0.2
        elif self.abandoned_hours and self.abandoned_hours < 24:
            score += 0.1
        elif self.abandoned_hours and self.abandoned_hours > 72:
            score -= 0.1
        return min(max(score, 0.0), 1.0)


class CartAnalysis(BaseModel):
    cart_id: str
    total_value: float
    items_count: int
    customer_email: Optional[str] = None
    customer_name: Optional[str] = None
    risk_level: RiskLevel
    recommended_strategy: RecoveryStrategy
    discount_code: Optional[str] = None
    discount_value: float = 0.0
    recovery_probability: float
    estimated_revenue: float
    is_recoverable: bool
    needs_human_approval: bool
    reasoning: List[str]
    email_subject: Optional[str] = None
    email_body: Optional[str] = None


class BulkCartResponse(BaseModel):
    results: List[CartAnalysis]
    summary: Dict[str, Any]


SYSTEM_PROMPT = """You are an expert Cart Recovery AI for ecommerce businesses.

YOUR ROLE:
- Analyze abandoned carts and determine optimal recovery strategy
- Generate compelling email copy to recover lost sales
- Calculate discount effectiveness and revenue impact

STRATEGIES:
- DISCOUNT_PERCENT: Percentage off for high-value carts (>$200)
- DISCOUNT_FIXED: Fixed amount off for medium carts ($50-$150)
- FREE_SHIPPING: Free shipping for moderate carts
- URGENCY: Scarcity-based (low stock, limited time)
- SOCIAL_PROOF: Social proof for low-value carts
- PERSONAL_OUTREACH: Personal email for VIP customers

Provide analysis as JSON with reasoning.
"""


class RecoveryStrategyEngine:
    """Selects optimal recovery strategy."""

    DISCOUNT_TIERS = {
        "low": {"min": 0, "max": 50, "percent": 5, "fixed": 2.0},
        "medium": {"min": 50, "max": 150, "percent": 10, "fixed": 5.0},
        "high": {"min": 150, "max": 500, "percent": 15, "fixed": 15.0},
        "vip": {"min": 500, "max": float("inf"), "percent": 20, "fixed": 50.0},
    }

    def assess_risk(self, cart: AbandonedCart) -> RiskLevel:
        hours = cart.abandoned_hours or 0
        value = cart.total_value
        if hours < 2 and value < 50:
            return RiskLevel.LOW
        elif hours < 24 and value < 150:
            return RiskLevel.MEDIUM
        elif hours < 72 or value >= 150:
            return RiskLevel.HIGH
        else:
            return RiskLevel.CRITICAL

    def select_strategy(self, cart: AbandonedCart) -> RecoveryStrategy:
        if cart.total_value < 10:
            return RecoveryStrategy.SOCIAL_PROOF
        if cart.customer:
            if cart.customer.is_repeat_customer and cart.customer.total_orders > 10:
                return RecoveryStrategy.PERSONAL_OUTREACH
            if cart.customer.lifetime_value_tier == "vip":
                return RecoveryStrategy.DISCOUNT_PERCENT
        if cart.total_value > 200:
            return RecoveryStrategy.DISCOUNT_PERCENT
        elif cart.total_value > 100:
            return RecoveryStrategy.FREE_SHIPPING
        elif cart.total_value > 50:
            return RecoveryStrategy.DISCOUNT_FIXED
        else:
            return RecoveryStrategy.DISCOUNT_PERCENT

    def calculate_discount(self, cart: AbandonedCart, strategy: RecoveryStrategy) -> Tuple[float, str]:
        value = cart.total_value
        tier = "low"
        for t_name, t in self.DISCOUNT_TIERS.items():
            if t["min"] <= value < t["max"]:
                tier = t_name
                break
        if cart.customer and cart.customer.is_repeat_customer:
            tiers = ["low", "medium", "high", "vip"]
            idx = tiers.index(tier) if tier in tiers else 0
            tier = tiers[min(idx + 1, len(tiers) - 1)]
        if cart.customer and cart.customer.lifetime_value_tier == "vip":
            tier = "vip"
        dc = self.DISCOUNT_TIERS[tier]
        if strategy == RecoveryStrategy.DISCOUNT_PERCENT:
            return dc["percent"], f"{dc['percent']}OFF"
        elif strategy == RecoveryStrategy.DISCOUNT_FIXED:
            return dc["fixed"], f"${dc['fixed']:.0f}OFF"
        elif strategy == RecoveryStrategy.FREE_SHIPPING:
            return 0.0, "FREESHIP"
        return 0.0, "RECOVER"


class DiscountGenerator:
    """Generates unique discount codes."""

    CHARS = string.ascii_uppercase + string.digits

    def generate(self, cart: AbandonedCart, strategy: RecoveryStrategy, discount_value: float) -> str:
        cart_hash = hashlib.md5(cart.cart_id.encode()).hexdigest()[:6]
        strategy_map = {
            RecoveryStrategy.DISCOUNT_PERCENT: "PCT",
            RecoveryStrategy.DISCOUNT_FIXED: "FIX",
            RecoveryStrategy.FREE_SHIPPING: "SHIP",
            RecoveryStrategy.URGENCY: "URG",
            RecoveryStrategy.SOCIAL_PROOF: "SOC",
            RecoveryStrategy.PERSONAL_OUTREACH: "VIP",
        }
        strategy_code = strategy_map.get(strategy, "REC")
        suffix = "".join(secrets.choice(self.CHARS) for _ in range(4))
        code = f"REC-{strategy_code}{cart_hash[:4]}-{suffix}"
        return code

    def email_context(self, cart: AbandonedCart, code: str, strategy: RecoveryStrategy, discount_value: float) -> Dict[str, str]:
        name = cart.customer.first_name if cart.customer and cart.customer.first_name else "there"

        names = ", ".join(f"{i.title} (x{i.quantity})" for i in cart.items[:3])
        if len(cart.items) > 3:
            names += f" and {len(cart.items) - 3} more"

        strategy_texts = {
            RecoveryStrategy.DISCOUNT_PERCENT: (f"{discount_value:.0f}% OFF", f"Get {discount_value:.0f}% Off Now"),
            RecoveryStrategy.DISCOUNT_FIXED: (f"${discount_value:.2f} OFF", f"Save ${discount_value:.2f} Today"),
            RecoveryStrategy.FREE_SHIPPING: ("FREE SHIPPING", "Claim Free Shipping"),
            RecoveryStrategy.SOCIAL_PROOF: ("Don't Miss Out!", "Complete Your Order"),
            RecoveryStrategy.URGENCY: ("Limited Time Offer", "Buy Before It's Gone"),
            RecoveryStrategy.PERSONAL_OUTREACH: ("Personal Offer For You", "Let's Complete Your Order"),
        }
        dt, cta = strategy_texts.get(strategy, ("Complete Your Order", "Complete Purchase"))

        return {
            "customer_name": name,
            "cart_items": names,
            "cart_value": f"${cart.total_value:.2f}",
            "discount_code": code,
            "discount_text": dt,
            "cta_text": cta,
            "checkout_url": cart.checkout_url or "",
        }


def _sanitize_for_llm(value: str, max_len: int = 200) -> str:
    """Sanitize user-controlled input before LLM prompt interpolation.

    Strips control characters, truncates, and wraps in brackets to signal
    literal data — reducing prompt injection risk.
    """
    if not value:
        return ""
    cleaned = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', value)
    cleaned = cleaned.replace('{', '(').replace('}', ')')
    cleaned = cleaned.replace('<', '(').replace('>', ')')
    if len(cleaned) > max_len:
        cleaned = cleaned[:max_len] + "..."
    return cleaned


class CartRecoveryAgent:
    """AI Cart Recovery Agent"""

    def __init__(self):
        self.config = Config()
        self.llm = LLMClient(
            system_prompt=SYSTEM_PROMPT,
            temperature=self.config.TEMPERATURE,
            max_tokens=self.config.MAX_TOKENS,
            circuit_breaker=CircuitBreaker(threshold=5, recovery_timeout=60),
        )
        self.strategy_engine = RecoveryStrategyEngine()
        self.discount_generator = DiscountGenerator()

    async def close(self):
        await self.llm.close()

    async def analyze(self, cart: AbandonedCart) -> CartAnalysis:
        if guardrail_manager is not None:
            cart_text = f"{cart.customer.first_name or ''} {cart.customer.email or ''} " + " ".join(
                i.title for i in cart.items
            )
            input_check = guardrail_manager.check_input(cart_text)
            if not input_check.passed:
                logger.warning("Prompt injection detected in cart data: %s", input_check.violations)
                return CartAnalysis(
                    cart_id=cart.cart_id,
                    total_value=cart.total_value,
                    items_count=cart.items_count,
                    risk_level=RiskLevel.CRITICAL,
                    recommended_strategy=RecoveryStrategy.SOCIAL_PROOF,
                    recovery_probability=0,
                    estimated_revenue=0,
                    is_recoverable=False,
                    needs_human_approval=True,
                    reasoning=["Blocked: prompt injection detected in cart data"],
                )

        if not cart.is_recoverable:
            return CartAnalysis(
                cart_id=cart.cart_id,
                total_value=cart.total_value,
                items_count=cart.items_count,
                risk_level=RiskLevel.LOW,
                recommended_strategy=RecoveryStrategy.SOCIAL_PROOF,
                recovery_probability=0,
                estimated_revenue=0,
                is_recoverable=False,
                needs_human_approval=False,
                reasoning=["Cart is not recoverable"],
            )

        logger.info("analyze=start cart_id=%s value=%.2f items=%d", cart.cart_id, cart.total_value, cart.items_count)
        risk = self.strategy_engine.assess_risk(cart)
        strategy = self.strategy_engine.select_strategy(cart)
        discount_value, _ = self.strategy_engine.calculate_discount(cart, strategy)
        code = self.discount_generator.generate(cart, strategy, discount_value)
        prob = cart.recovery_probability
        estimated_revenue = cart.total_value * prob
        needs_approval = cart.total_value > 200 or discount_value > 20 or prob < 0.3

        email_ctx = self.discount_generator.email_context(cart, code, strategy, discount_value)

        reasoning = [
            f"Cart value: ${cart.total_value:.2f} ({cart.items_count} items)",
            f"Abandoned: {cart.abandoned_hours:.1f}h ago" if cart.abandoned_hours else "Abandoned time unknown",
            f"Risk: {risk.value}, Strategy: {strategy.value}",
            f"Discount: {email_ctx['discount_text']}",
            f"Recovery probability: {prob:.0%}, Est. revenue: ${estimated_revenue:.2f}",
        ]

        email_subject, email_body = await self._generate_email(cart, email_ctx, strategy, discount_value)

        return CartAnalysis(
            cart_id=cart.cart_id,
            total_value=cart.total_value,
            items_count=cart.items_count,
            customer_email=cart.customer.email if cart.customer else None,
            customer_name=email_ctx["customer_name"],
            risk_level=risk,
            recommended_strategy=strategy,
            discount_code=code,
            discount_value=discount_value,
            recovery_probability=prob,
            estimated_revenue=round(estimated_revenue, 2),
            is_recoverable=True,
            needs_human_approval=needs_approval,
            reasoning=reasoning,
            email_subject=email_subject,
            email_body=email_body,
        )
        logger.info("analyze=complete cart_id=%s strategy=%s risk=%s prob=%.0f%%", cart.cart_id, strategy.value, risk.value, prob * 100)

    async def analyze_bulk(self, carts: List[AbandonedCart]) -> BulkCartResponse:
        results = []
        strategy_counts = {}
        total_potential = 0.0
        risk_dist = {"low": 0, "medium": 0, "high": 0, "critical": 0}

        for cart in carts:
            result = await self.analyze(cart)
            results.append(result)
            s = result.recommended_strategy.value
            strategy_counts[s] = strategy_counts.get(s, 0) + 1
            total_potential += result.estimated_revenue
            risk_dist[result.risk_level.value] = risk_dist.get(result.risk_level.value, 0) + 1

        return BulkCartResponse(
            results=results,
            summary={
                "total_carts": len(carts),
                "recoverable_carts": sum(1 for r in results if r.is_recoverable),
                "needs_approval": sum(1 for r in results if r.needs_human_approval),
                "total_potential_revenue": round(total_potential, 2),
                "average_recovery_probability": round(sum(r.recovery_probability for r in results) / len(results), 2) if results else 0,
                "risk_distribution": risk_dist,
                "strategy_breakdown": strategy_counts,
                "estimated_recoverable_value": round(sum(r.estimated_revenue for r in results if r.is_recoverable), 2),
                "analysis_time": datetime.now().isoformat(),
            },
        )

    async def _generate_email(self, cart: AbandonedCart, ctx: Dict, strategy: RecoveryStrategy, discount_value: float) -> Tuple[str, str]:
        safe_name = _sanitize_for_llm(ctx['customer_name'])
        safe_items = _sanitize_for_llm(ctx['cart_items'])
        safe_value = _sanitize_for_llm(ctx['cart_value'])
        safe_discount = _sanitize_for_llm(ctx['discount_text'])
        safe_code = _sanitize_for_llm(ctx['discount_code'])

        prompt = f"""
Generate a cart recovery email for an abandoned cart.

Customer: [{safe_name}]
Items: [{safe_items}]
Cart Value: [{safe_value}]
Strategy: {strategy.value}
Discount: [{safe_discount}]
Code: [{safe_code}]

Provide:
- subject: Catchy email subject line
- body: Professional email body (2-3 paragraphs)

JSON output.
"""
        try:
            result = await self.llm.call(prompt)
            d = json.loads(result.text) if result.text else {}
            return d.get("subject", self._default_subject(ctx)), d.get("body", self._default_body(ctx))
        except Exception:
            return self._default_subject(ctx), self._default_body(ctx)

    def _default_subject(self, ctx: Dict) -> str:
        name = ctx["customer_name"]
        discount = ctx["discount_text"]
        return f"Don't forget your items, {name}! 🛒"

    def _default_body(self, ctx: Dict) -> str:
        return (
            f"Hi {ctx['customer_name']},\n\n"
            f"You left some items in your cart: {ctx['cart_items']} (Total: {ctx['cart_value']}).\n\n"
            f"As a special offer, here's {ctx['discount_text']} — use code: {ctx['discount_code']}\n\n"
            f"👉 {ctx['cta_text']}: {ctx['checkout_url'] or 'Complete your purchase'}\n\n"
            f"Offer expires in 24 hours. Don't miss out!\n\n"
            f"- The Team"
        )


agent = CartRecoveryAgent()
