"""
Price Optimization Agent - AI Employee #3
Dynamic pricing, competitor analysis, profit maximization
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from shared.llm_client import LLMClient, CircuitBreaker

logger = logging.getLogger("pricing_agent")


class Config:
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    MODEL_NAME = os.getenv("MODEL_NAME", "gemini-2.0-flash")
    TEMPERATURE = float(os.getenv("TEMPERATURE", "0.3"))
    MAX_TOKENS = int(os.getenv("MAX_TOKENS", "1024"))


class Product(BaseModel):
    sku: str
    name: str
    category: str
    current_price: float
    unit: float
    competitor_price: Optional[float] = None
    daily_sales: Optional[float] = None
    weekly_sales: Optional[float] = None
    monthly_sales: Optional[float] = None
    stock_level: Optional[int] = None
    demand_score: Optional[float] = None
    seasonality: Optional[str] = None
    product_age_days: Optional[int] = None
    reviews_rating: Optional[float] = None
    competitor_names: Optional[List[str]] = None
    price_history_30d: Optional[List[float]] = None
    is_bundle: bool = False
    is_subscription: bool = False
    cost_plus_minimum: Optional[float] = None


class PriceRecommendation(BaseModel):
    sku: str
    product_name: str
    current_price: float
    recommended_price: float
    price_change_percent: float
    profit_impact_monthly: float
    revenue_impact_monthly: float
    confidence: float
    requires_approval: bool
    reasoning: str
    strategy: str
    competitor_price: Optional[float] = None
    competitor_advantage: Optional[str] = None
    optimal_min_price: Optional[float] = None
    optimal_max_price: Optional[float] = None
    risk_level: str


class BulkPriceRequest(BaseModel):
    products: List[Product]
    global_price_change_limit_percent: float = 10.0


class BulkPriceResponse(BaseModel):
    recommendations: List[PriceRecommendation]
    summary: Dict[str, Any]


SYSTEM_PROMPT = """You are an expert Pricing Optimization AI for ecommerce businesses.

YOUR ROLE:
- Analyze market conditions and competitor pricing
- Recommend optimal prices to maximize profit
- Balance competitiveness with margin requirements
- Prevent pricing wars while staying competitive

PRICING STRATEGIES:
1. COMPETITIVE - Match or slightly undercut competitors
2. PREMIUM - Price higher due to quality, brand, or features
3. DISCOUNT - Lower price to drive volume or clear inventory
4. CLEARANCE - Aggressive discount to liquidate stock
5. DYNAMIC - Adjust based on demand, time, and inventory

CONSTRAINTS:
- Never exceed 10% price change without approval
- Never price below cost + minimum margin
- Consider price elasticity of demand
- Account for MAP (Minimum Advertised Price) agreements
- Consider psychological pricing ($19.99 vs $20)
- Seasonality and demand fluctuations
- Bundle vs individual pricing

DECISION FRAMEWORK:
- If competitor_price < current_price AND margin > 20%: suggest matching
- If competitor_price > current_price AND demand is high: suggest premium
- If stock > 90 days: suggest clearance discount
- If demand_score > 0.8 AND stock < 30 days: suggest price increase
- If demand_score < 0.3 AND stock > 60 days: suggest discount

OUTPUT FORMAT (JSON):
{
    "recommended_price": 49.99,
    "strategy": "competitive",
    "profit_impact_monthly": 1250.00,
    "revenue_impact_monthly": -500.00,
    "confidence": 0.85,
    "requires_approval": true,
    "reasoning": "Detailed explanation of pricing decision",
    "competitor_advantage": "we_are_costlier",
    "optimal_min_price": 44.99,
    "optimal_max_price": 54.99,
    "risk_level": "medium"
}
"""


class PriceOptimizationAgent:
    """AI Price Optimization Agent"""

    def __init__(self):
        self.config = Config()
        self.llm = LLMClient(
            system_prompt=SYSTEM_PROMPT,
            temperature=self.config.TEMPERATURE,
            max_tokens=self.config.MAX_TOKENS,
            circuit_breaker=CircuitBreaker(threshold=5, recovery_timeout=60),
        )

    async def close(self):
        await self.llm.close()

    async def analyze(self, product: Product) -> PriceRecommendation:
        margin = ((product.current_price - product.unit) / product.current_price * 100) if product.current_price > 0 else 0
        competitor_price = product.competitor_price
        has_competitor = competitor_price is not None

        context = f"""
Analyze pricing for this product:

SKU: {product.sku}
Product: {product.name}
Category: {product.category}
Current Price: ${product.current_price:.2f}
Cost: ${product.unit:.2f}
Margin: {margin:.1f}%
Competitor Price: {'$' + str(competitor_price) if has_competitor else 'Not available'}
Monthly Sales: {product.monthly_sales or 'Unknown'}
Stock Level: {product.stock_level or 'Unknown'}
Demand Score: {product.demand_score or 'Unknown'}
Seasonality: {product.seasonality or 'normal'}
Rating: {product.reviews_rating or 'Unknown'}
Product Age: {product.product_age_days or 'Unknown'} days

Provide pricing recommendation as JSON.
"""
        logger.info("analyze=start sku=%s product=%s current_price=%.2f", product.sku, product.name, product.current_price)
        try:
            result = await self.llm.call(context)
            data = json.loads(result.text) if result.text else {}

            rec = PriceRecommendation(
                sku=product.sku,
                product_name=product.name,
                current_price=product.current_price,
                recommended_price=float(data.get("recommended_price", product.current_price)),
                price_change_percent=round(
                    (float(data.get("recommended_price", product.current_price)) - product.current_price) / product.current_price * 100, 1
                ),
                profit_impact_monthly=float(data.get("profit_impact_monthly", 0)),
                revenue_impact_monthly=float(data.get("revenue_impact_monthly", 0)),
                confidence=float(data.get("confidence", 0.7)),
                requires_approval=data.get("requires_approval", True),
                reasoning=data.get("reasoning", "Analysis completed"),
                strategy=data.get("strategy", "competitive"),
                competitor_price=competitor_price,
                competitor_advantage=data.get("competitor_advantage"),
                optimal_min_price=data.get("optimal_min_price"),
                optimal_max_price=data.get("optimal_max_price"),
                risk_level=data.get("risk_level", "medium"),
            )
            logger.info("analyze=complete sku=%s strategy=%s new_price=%.2f change=%.1f%%", product.sku, rec.strategy, rec.recommended_price, rec.price_change_percent)
            return rec

        except Exception:
            logger.warning("analyze=fallback sku=%s", product.sku)
            return self._rule_based_fallback(product)

    async def analyze_bulk(self, request: BulkPriceRequest) -> BulkPriceResponse:
        results = []
        total_profit_impact = 0.0
        total_revenue_impact = 0.0
        changes_count = 0

        for product in request.products:
            result = await self.analyze(product)
            results.append(result)
            total_profit_impact += result.profit_impact_monthly
            total_revenue_impact += result.revenue_impact_monthly
            if result.price_change_percent != 0:
                changes_count += 1

        return BulkPriceResponse(
            recommendations=results,
            summary={
                "total_products": len(request.products),
                "products_with_changes": changes_count,
                "products_needing_approval": sum(1 for r in results if r.requires_approval),
                "total_monthly_profit_impact": round(total_profit_impact, 2),
                "total_monthly_revenue_impact": round(total_revenue_impact, 2),
                "strategies_used": list(set(r.strategy for r in results)),
                "analysis_time": datetime.now().isoformat(),
            },
        )

    async def get_competitor_insight(self, product: Product) -> Dict:
        context = f"""
Analyze competitor landscape for {product.name} (SKU: {product.sku}):

Current Price: ${product.current_price:.2f}
Competitor Price: {'$' + str(product.competitor_price) if product.competitor_price else 'N/A'}
Competitor Names: {product.competitor_names or ['Unknown']}

Provide competitor analysis:
- market_position: premium/mainstream/budget
- price_advantage: how much we differ from market average
- recommendation: what to do about pricing
- price_elasticity: high/medium/low
"""
        try:
            result = await self.llm.call(context)
            return json.loads(result.text) if result.text else {}
        except Exception:
            return {
                "market_position": "unknown",
                "price_advantage": 0,
                "recommendation": "Maintain current pricing",
                "price_elasticity": "medium",
            }

    def _rule_based_fallback(self, product: Product) -> PriceRecommendation:
        margin = ((product.current_price - product.unit) / product.current_price * 100) if product.current_price > 0 else 0

        competitor_price = product.competitor_price
        floor = product.current_price * 0.95
        ceiling = product.current_price * 1.05

        if competitor_price and competitor_price < product.current_price:
            new_price = max(competitor_price, product.unit * 1.2, floor)
            strategy = "competitive"
            if product.stock_level and product.stock_level > 90:
                new_price = competitor_price * 0.95
                strategy = "clearance"
            change_pct = (new_price - product.current_price) / product.current_price * 100
            requires_approval = abs(change_pct) > 5
            risk = "medium" if abs(change_pct) > 5 else "low"
            reasoning = f"Competitor at ${competitor_price:.2f}. Adjusting to ${new_price:.2f} ({change_pct:+.1f}%)."
        elif competitor_price and competitor_price > product.current_price:
            if product.demand_score and product.demand_score > 0.7:
                new_price = min(competitor_price * 0.95, ceiling)
                strategy = "premium"
                change_pct = (new_price - product.current_price) / product.current_price * 100
                requires_approval = abs(change_pct) > 5
                risk = "low"
                reasoning = f"High demand and competitor above us. Raising to ${new_price:.2f}."
            else:
                new_price = product.current_price
                strategy = "competitive"
                change_pct = 0
                requires_approval = False
                risk = "low"
                reasoning = "Price is competitive. No change needed."
        else:
            if product.stock_level and product.stock_level > 90:
                new_price = product.current_price * 0.85
                strategy = "clearance"
                change_pct = -15.0
                requires_approval = True
                risk = "medium"
                reasoning = f"Overstocked ({product.stock_level}). Recommend 15% clearance discount."
            elif product.stock_level and product.stock_level < 30 and product.demand_score and product.demand_score > 0.7:
                new_price = product.current_price * 1.05
                strategy = "premium"
                change_pct = 5.0
                requires_approval = True
                risk = "low"
                reasoning = "Low stock, high demand. Small price increase to maximize profit."
            else:
                new_price = product.current_price
                strategy = "dynamic"
                change_pct = 0
                requires_approval = False
                risk = "low"
                reasoning = "Price is optimal for current conditions."

        monthly_profit_impact = (new_price - product.current_price) * (product.monthly_sales or 100)
        monthly_revenue_impact = (new_price - product.current_price) * (product.monthly_sales or 100)

        return PriceRecommendation(
            sku=product.sku,
            product_name=product.name,
            current_price=product.current_price,
            recommended_price=round(new_price, 2),
            price_change_percent=round(change_pct, 1),
            profit_impact_monthly=round(monthly_profit_impact, 2),
            revenue_impact_monthly=round(monthly_revenue_impact, 2),
            confidence=0.75,
            requires_approval=requires_approval or abs(change_pct) > 5,
            reasoning=reasoning,
            strategy=strategy,
            optimal_min_price=round(product.current_price * 0.9, 2),
            optimal_max_price=round(product.current_price * 1.1, 2),
            risk_level=risk,
        )


agent = PriceOptimizationAgent()
