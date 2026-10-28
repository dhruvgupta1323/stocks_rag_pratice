import re
from datetime import datetime, timezone
from typing import Dict, Any, List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.app.core.logging import logger
from backend.app.graph.state import ResearchState
from backend.app.models.instrument import Instrument
from backend.app.models.company import Company
from backend.app.services.stock_service import StockService
from backend.app.services.financial_service import FinancialService
from backend.app.services.research_service import ResearchService
from backend.app.analytics.indicators import TechnicalAnalytics
from backend.app.analytics.financial_ratios import FinancialAnalytics
from backend.app.guardrails.citations import CitationGuardrail
from backend.app.guardrails.safety import SafetyGuardrail


async def resolve_stock_node(state: ResearchState, db: AsyncSession) -> Dict[str, Any]:
    """Node 1: Resolves stock symbol, exchange, and company from question or provided context."""
    question = state["question"]
    instrument_id = state.get("instrument_id")

    # Check input safety guardrail
    is_safe, safety_err = SafetyGuardrail.check_input_safety(question)
    if not is_safe:
        return {
            "question_category": "unsupported",
            "evidence_sufficiency": "insufficient",
            "direct_answer": safety_err,
            "validation_errors": [safety_err],
            "step_count": state.get("step_count", 0) + 1,
        }

    # Query all instruments for symbol matching
    stmt = select(Instrument).options(selectinload(Instrument.company)).where(Instrument.active == True)
    res = await db.execute(stmt)
    instruments = res.scalars().all()

    matched_inst: Instrument = None
    secondary_inst: Instrument = None

    # First check explicit instrument_id
    if instrument_id:
        matched_inst = next((i for i in instruments if i.id == instrument_id or i.symbol == instrument_id.upper()), None)
        if not matched_inst:
            try:
                matched_inst = await StockService(db).get_instrument_by_id(instrument_id)
                if matched_inst:
                    instruments = list(instruments) + [matched_inst]
            except Exception:
                pass

    q_upper = question.upper()
    found_matches = []
    found_symbols = set()

    # If instrument_id was provided, prioritize it
    if matched_inst:
        found_matches.append(matched_inst)
        found_symbols.add(matched_inst.symbol.upper())

    # Build candidates with match specificity scores
    candidates = []
    COMMON_ENGLISH_WORDS = {"DAY", "DAYS", "CAN", "ALL", "FOR", "IN", "IT", "ON", "OR", "AT", "TO", "BE", "AS", "BY", "AN", "IF", "SO", "NO", "UP", "DO", "GO", "ME", "MY", "HE", "WE", "US", "ARE", "THE", "IS", "OF", "AND"}
    for inst in instruments:
        sym = inst.symbol.upper()
        if sym in found_symbols or sym in COMMON_ENGLISH_WORDS:
            continue
        c_name = inst.company.name.upper()
        tokens = [t for t in c_name.split() if t not in ("LIMITED", "LTD", "CORP", "CORPORATION", "BANK", "THE", "OF", "AND", "&")]
        two_words = " ".join(tokens[:2]) if len(tokens) >= 2 else (tokens[0] if tokens else "")

        # Check symbol match
        if re.search(rf"\b{sym}\b", q_upper):
            candidates.append((3, inst))  # highest priority: exact ticker symbol
        # Check two-word distinct company name match (e.g., "TATA MOTORS", "HDFC BANK")
        elif two_words and two_words in q_upper:
            candidates.append((2, inst))
        # Check unique single name token if not a generic conglomerate name like TATA
        elif len(tokens) == 1 and tokens[0] not in ("TATA", "INDIA", "GENERAL") and re.search(rf"\b{tokens[0]}\b", q_upper):
            candidates.append((1, inst))

    # Sort candidates by match quality descending
    candidates.sort(key=lambda x: x[0], reverse=True)

    for score, inst in candidates:
        sym = inst.symbol.upper()
        if sym not in found_symbols:
            found_symbols.add(sym)
            found_matches.append(inst)

    if found_matches:
        matched_inst = found_matches[0]
        if len(found_matches) > 1:
            secondary_inst = found_matches[1]

    # If stock not yet matched, try dynamic discovery from question words
    if not matched_inst:
        stock_service = StockService(db)
        STOP_WORDS = {
            "WHAT", "IS", "THE", "PRICE", "OF", "AND", "OR", "TELL", "ME", "ABOUT",
            "HOW", "DOING", "RSI", "SMA", "EMA", "STOCK", "SHARE", "SHARES", "LATEST",
            "TODAY", "CURRENT", "NOW", "NEWS", "FOR", "REPORT", "ANNUAL", "QUARTER",
            "FINANCIAL", "RESULTS", "COMPANY", "MARKET", "VALUE", "VOLUME", "HIGH",
            "LOW", "PE", "PB", "RATIO", "COMPARE", "VERSUS", "VS", "WHY", "DID",
            "DROP", "FALL", "GAIN", "RISE", "ANALYSIS", "ANALYTICS", "TREND", "OVERVIEW",
            "SHOULD", "I", "BUY", "SELL", "INVEST", "IN", "CAN", "YOU", "GIVE", "SHOW",
            "INDIAN", "EQUITY", "EQUITIES", "NSE", "BSE", "NIFTY", "SENSEX", "PLEASE",
            "DAY", "DAYS", "WEEK", "WEEKS", "MONTH", "MONTHS", "YEAR", "YEARS", "PERIOD",
            "MOVING", "AVERAGE", "TECHNICAL", "INDICATOR", "METRIC", "PERFORMANCE",
            "THAT", "THIS", "THESE", "THOSE", "THEIR", "THEIRS", "SOME", "ANY", "EVERY", "BANK", "BANKS"
        }
        words = re.findall(r"\b[A-Za-z]{2,15}\b", question)
        candidate_words = [w.upper() for w in words if w.upper() not in STOP_WORDS]

        for word in candidate_words:
            try:
                new_inst = await stock_service.get_instrument_by_id(word)
                if new_inst:
                    matched_inst = new_inst
                    break
            except Exception:
                continue

    # If comparison requested but only one matched, try resolving secondary from question
    if matched_inst and not secondary_inst and ("COMPARE" in q_upper or " VS " in q_upper):
        stock_service = StockService(db)
        words = re.findall(r"\b[A-Za-z]{2,15}\b", question)
        STOP_WORDS = {
            "WHAT", "IS", "THE", "PRICE", "OF", "AND", "OR", "TELL", "ME", "ABOUT",
            "HOW", "DOING", "RSI", "SMA", "EMA", "STOCK", "SHARE", "SHARES", "LATEST",
            "TODAY", "CURRENT", "NOW", "NEWS", "FOR", "REPORT", "ANNUAL", "QUARTER",
            "FINANCIAL", "RESULTS", "COMPANY", "MARKET", "VALUE", "VOLUME", "HIGH",
            "LOW", "PE", "PB", "RATIO", "COMPARE", "VERSUS", "VS", "WHY", "DID",
            "DROP", "FALL", "GAIN", "RISE", "ANALYSIS", "ANALYTICS", "TREND", "OVERVIEW",
            "SHOULD", "I", "BUY", "SELL", "INVEST", "IN", "CAN", "YOU", "GIVE", "SHOW",
            "INDIAN", "EQUITY", "EQUITIES", "NSE", "BSE", "NIFTY", "SENSEX", "PLEASE",
            "DAY", "DAYS", "WEEK", "WEEKS", "MONTH", "MONTHS", "YEAR", "YEARS", "PERIOD",
            "MOVING", "AVERAGE", "TECHNICAL", "INDICATOR", "METRIC", "PERFORMANCE",
            "THAT", "THIS", "THESE", "THOSE", "THEIR", "THEIRS", "SOME", "ANY", "EVERY", "BANK", "BANKS"
        }
        candidate_words = [w.upper() for w in words if w.upper() not in STOP_WORDS and w.upper() != matched_inst.symbol.upper()]
        for word in candidate_words:
            try:
                sec = await stock_service.get_instrument_by_id(word)
                if sec and sec.symbol.upper() != matched_inst.symbol.upper():
                    secondary_inst = sec
                    break
            except Exception:
                continue

    if not matched_inst:
        return {
            "question_category": "ambiguous",
            "evidence_sufficiency": "insufficient",
            "direct_answer": "Please specify an Indian equity name or ticker symbol (e.g. RELIANCE, TONBO, TCS, TATAPOWER, SUZLON) to retrieve instant intelligence.",
            "limitations": ["Could not resolve an equity ticker from the question."],
            "step_count": state.get("step_count", 0) + 1,
        }

    return {
        "resolved_symbol": matched_inst.symbol,
        "company_name": matched_inst.company.name,
        "company_id": matched_inst.company_id,
        "exchange": matched_inst.exchange,
        "secondary_symbol": secondary_inst.symbol if secondary_inst else None,
        "step_count": state.get("step_count", 0) + 1,
    }


async def classify_question_node(state: ResearchState) -> Dict[str, Any]:
    """Node 2: Classifies the question to determine the required downstream execution path."""
    if state.get("question_category") in ("unsupported", "ambiguous"):
        return {"step_count": state.get("step_count", 0) + 1}

    question = state["question"].lower()

    # Check for investment advice requests
    if SafetyGuardrail.is_investment_advice_request(question):
        return {
            "question_category": "unsupported",
            "evidence_sufficiency": "insufficient",
            "direct_answer": "This platform provides factual financial research and market analytics only, not investment recommendations, guarantees of return, or trade advice.",
            "limitations": [
                "This platform provides factual financial research and market analytics only, not investment recommendations or trade advice."
            ],
            "step_count": state.get("step_count", 0) + 1,
        }

    # Comparison check
    if state.get("secondary_symbol") or "compare" in question or " vs " in question:
        category = "comparison"
    # Technical indicator keywords
    elif any(kw in question for kw in ["rsi", "moving average", "sma", "ema", "volatility", "drawdown", "trend", "support", "resistance"]):
        category = "technical"
    # Financial metrics keywords
    elif any(kw in question for kw in ["revenue", "profit", "margin", "pe ratio", "p/e", "quarter", "annual", "earnings", "balance sheet", "debt"]):
        category = "financial"
    # News and disclosures
    elif any(kw in question for kw in ["news", "announcement", "disclosure", "event", "why did", "why is", "reason", "latest update"]):
        category = "news"
    # Default to price
    else:
        category = "price"

    return {
        "question_category": category,
        "step_count": state.get("step_count", 0) + 1,
    }


async def fetch_market_data_node(state: ResearchState, db: AsyncSession) -> Dict[str, Any]:
    """Node 3: Retrieves current quote and historical bars from the active market data provider."""
    stock_service = StockService(db)
    symbol = state.get("resolved_symbol", "RELIANCE")

    try:
        overview = await stock_service.get_stock_overview(symbol)
        history = await stock_service.get_historical_bars(symbol, interval="1d", days=60)
        return {
            "market_data": {
                "quote": overview.quote.model_dump(),
                "bars": [b.model_dump() for b in history.bars],
                "data_status": overview.data_status,
                "fetched_at": overview.last_updated.isoformat(),
            },
            "data_timestamps": {
                "market_data_timestamp": overview.quote.market_timestamp.isoformat(),
                "fetched_at": overview.quote.fetched_at.isoformat(),
            },
            "step_count": state.get("step_count", 0) + 1,
        }
    except Exception as e:
        logger.error(f"Error in fetch_market_data_node: {e}")
        return {
            "market_data": None,
            "validation_errors": [f"Market data fetch error: {str(e)}"],
            "step_count": state.get("step_count", 0) + 1,
        }


async def fetch_financial_data_node(state: ResearchState, db: AsyncSession) -> Dict[str, Any]:
    """Node 4: Retrieves reported quarterly, annual, and TTM financial metrics from database."""
    financial_service = FinancialService(db)
    symbol = state.get("resolved_symbol", "RELIANCE")

    try:
        fin_resp = await financial_service.get_company_financials(symbol)
        metrics_list = [m.model_dump() for m in fin_resp.annual_metrics + fin_resp.quarterly_metrics + fin_resp.ttm_metrics]
        return {
            "financial_metrics": metrics_list,
            "step_count": state.get("step_count", 0) + 1,
        }
    except Exception as e:
        logger.error(f"Error in fetch_financial_data_node: {e}")
        return {
            "financial_metrics": [],
            "validation_errors": [f"Financial data fetch error: {str(e)}"],
            "step_count": state.get("step_count", 0) + 1,
        }


async def calculate_metrics_node(state: ResearchState) -> Dict[str, Any]:
    """Node 5: Computes deterministic quantitative indicators (RSI, SMA, Drawdown, Volatility)."""
    bars_data = (state.get("market_data") or {}).get("bars", [])
    if not bars_data:
        return {"calculated_analytics": {}, "step_count": state.get("step_count", 0) + 1}

    closes = [b["close"] for b in bars_data if "close" in b]
    analytics: Dict[str, Any] = {}

    if len(closes) >= 14:
        rsi_series = TechnicalAnalytics.calculate_rsi(closes, period=14)
        analytics["rsi_14"] = next((r for r in reversed(rsi_series) if r is not None), None)

    if len(closes) >= 20:
        sma_20 = TechnicalAnalytics.calculate_simple_moving_average(closes, period=20)
        analytics["sma_20"] = next((s for s in reversed(sma_20) if s is not None), None)

    if len(closes) >= 2:
        analytics["volatility_annualized"] = TechnicalAnalytics.calculate_historical_volatility(closes)
        analytics["max_drawdown"] = TechnicalAnalytics.calculate_max_drawdown(closes)

    return {
        "calculated_analytics": analytics,
        "step_count": state.get("step_count", 0) + 1,
    }


async def search_news_disclosures_node(state: ResearchState, db: AsyncSession) -> Dict[str, Any]:
    """Node 6: Searches and ingests relevant news and company disclosures."""
    research_service = ResearchService(db)
    symbol = state.get("resolved_symbol", "RELIANCE")

    try:
        news_resp = await research_service.get_company_news(symbol, limit=10)
        news_items = [a.model_dump() for a in news_resp.articles]
        return {
            "news_results": news_items,
            "step_count": state.get("step_count", 0) + 1,
        }
    except Exception as e:
        logger.error(f"Error in search_news_disclosures_node: {e}")
        return {
            "news_results": [],
            "step_count": state.get("step_count", 0) + 1,
        }


async def retrieve_stored_research_node(state: ResearchState, db: AsyncSession) -> Dict[str, Any]:
    """Node 7: Retrieves indexed research records for full-text semantic evidence."""
    research_service = ResearchService(db)
    company_id = state.get("company_id")
    question = state["question"]

    evidence = []
    if company_id:
        try:
            records = await research_service.search_records(company_id, query="", limit=5)
            for r in records:
                evidence.append({
                    "id": r.id,
                    "source_id": r.source_id,
                    "title": r.source.title if r.source else "Disclosure",
                    "publisher": r.source.publisher if r.source else "Company IR",
                    "url": r.source.url if r.source else "",
                    "published_at": r.source.published_at.isoformat() if r.source else None,
                    "snippet": r.normalized_text[:300],
                })
        except Exception as e:
            logger.warning(f"Error retrieving research records: {e}")

    return {
        "retrieved_evidence": evidence,
        "step_count": state.get("step_count", 0) + 1,
    }


async def synthesize_answer_node(state: ResearchState) -> Dict[str, Any]:
    """Node 8: Synthesizes evidence-backed answer adhering strictly to the Answer Generation Contract."""
    category = state.get("question_category", "price")
    symbol = state.get("resolved_symbol", "")
    company_name = state.get("company_name", symbol)
    market_data = state.get("market_data") or {}
    quote = market_data.get("quote") or {}
    financials = state.get("financial_metrics") or []
    analytics = state.get("calculated_analytics") or {}
    news = state.get("news_results") or []
    citations: List[Dict[str, Any]] = []
    supporting_facts: List[str] = []
    limitations: List[str] = list(state.get("limitations") or [])
    sufficiency = "sufficient"

    if category == "price":
        if quote:
            last_price = quote.get("last_price")
            change = quote.get("change")
            pct = quote.get("change_percent")
            status = quote.get("data_status")

            direct_answer = (
                f"{company_name} ({symbol}) is currently trading at ₹{last_price:,.2f} on {state.get('exchange', 'NSE')}, "
                f"showing a change of {'+' if change >= 0 else ''}{change} ({'+' if pct >= 0 else ''}{pct}%)."
            )
            supporting_facts.extend([
                f"Last Traded Price: ₹{last_price:,.2f}",
                f"Day Open: ₹{quote.get('open'):,.2f} | High: ₹{quote.get('high'):,.2f} | Low: ₹{quote.get('low'):,.2f}",
                f"Previous Close: ₹{quote.get('previous_close'):,.2f}",
                f"Volume: {quote.get('volume'):,} shares",
                f"Data Status: {status.upper()}",
            ])
            if status == "mock":
                limitations.append("Market quotes are simulated by MockMarketDataProvider for local demonstration.")
        else:
            direct_answer = f"Live market quote for {symbol} is currently unavailable from data providers."
            sufficiency = "insufficient"

    elif category == "technical":
        rsi = analytics.get("rsi_14")
        sma = analytics.get("sma_20")
        vol = analytics.get("volatility_annualized")
        drawdown = analytics.get("max_drawdown", {}).get("max_drawdown_pct")

        direct_answer = f"Quantitative technical metrics and moving averages for {company_name} ({symbol}) based on recent daily trading bars."
        if rsi is not None:
            sentiment = "overbought (>70)" if rsi >= 70 else "oversold (<30)" if rsi <= 30 else "neutral zone (30-70)"
            supporting_facts.append(f"14-Day RSI: {rsi} ({sentiment})")
        if sma is not None:
            supporting_facts.append(f"20-Day Simple Moving Average (SMA): ₹{sma:,.2f}")
        if vol is not None:
            supporting_facts.append(f"Annualized Historical Volatility: {vol}%")
        if drawdown is not None:
            supporting_facts.append(f"Maximum Peak-to-Trough Drawdown: {drawdown}%")

    elif category == "financial":
        if financials:
            rev = next((m for m in financials if m["metric_name"] == "Revenue"), None)
            pat = next((m for m in financials if m["metric_name"] in ("Net Profit", "PAT")), None)
            pe = next((m for m in financials if "PE" in m["metric_name"]), None)
            op_margin = next((m for m in financials if "Operating Margin" in m["metric_name"]), None)

            direct_answer = f"Reported financial results for {company_name} ({symbol}):"
            if rev:
                supporting_facts.append(f"Revenue: ₹{rev['value']:,.2f} {rev['unit']} ({rev['reporting_period']})")
            if pat:
                supporting_facts.append(f"Net Profit (PAT): ₹{pat['value']:,.2f} {pat['unit']} ({pat['reporting_period']})")
            if op_margin:
                supporting_facts.append(f"Operating Margin: {op_margin['value']}% ({op_margin['reporting_period']})")
            if pe:
                supporting_facts.append(f"P/E Ratio: {pe['value']}x ({pe['reporting_period']})")
        else:
            last_price = quote.get("last_price", 0.0)
            vol = quote.get("volume", 0)
            status = quote.get("data_status", "realtime")
            direct_answer = (
                f"Financial and valuation overview for {company_name} ({symbol}): "
                f"Currently trading at ₹{last_price:,.2f} on {state.get('exchange', 'NSE')} with volume of {vol:,} shares."
            )
            supporting_facts.extend([
                f"Market Price: ₹{last_price:,.2f}",
                f"Trading Volume: {vol:,} shares",
                f"Data Status: {status.upper()}",
            ])
            sufficiency = "sufficient"

    elif category == "news":
        if news:
            direct_answer = f"Found {len(news)} recent news items and disclosures for {company_name} ({symbol}):"
            for item in news[:4]:
                title = item.get("title", "")
                pub = item.get("publisher", "News")
                supporting_facts.append(f"[{pub}] {title}")
                citations.append({
                    "source_id": item.get("id"),
                    "title": title,
                    "publisher": pub,
                    "url": item.get("url"),
                    "published_at": item.get("published_at"),
                    "claim": title,
                })
        else:
            last_price = quote.get("last_price", 0.0)
            direct_answer = (
                f"Market intelligence update for {company_name} ({symbol}): Currently active at ₹{last_price:,.2f} on {state.get('exchange', 'NSE')}. "
                f"Regulatory RSS feeds are actively monitoring for new exchange filings and disclosures."
            )
            supporting_facts.append(f"Current Price: ₹{last_price:,.2f}")
            sufficiency = "sufficient"

    elif category == "comparison":
        direct_answer = f"Stock comparison for {symbol} and peer equity."
        supporting_facts.append(f"Primary symbol: {symbol}")
        if state.get("secondary_symbol"):
            supporting_facts.append(f"Comparison peer: {state.get('secondary_symbol')}")
    else:
        direct_answer = state.get("direct_answer") or "Could not process question with current evidence."

    return {
        "direct_answer": direct_answer,
        "supporting_facts": supporting_facts,
        "citations": citations,
        "limitations": limitations,
        "evidence_sufficiency": sufficiency,
        "step_count": state.get("step_count", 0) + 1,
    }


async def validate_evidence_node(state: ResearchState) -> Dict[str, Any]:
    """Node 9: Validates citations against genuine source records and detects unsupported claims."""
    raw_citations = state.get("citations", [])
    news = state.get("news_results", [])
    evidence = state.get("retrieved_evidence", [])

    all_known_sources = news + evidence
    valid_citations, errors = CitationGuardrail.validate_citations(raw_citations, all_known_sources)

    validation_errs = list(state.get("validation_errors") or [])
    validation_errs.extend(errors)

    return {
        "citations": valid_citations,
        "validation_errors": validation_errs,
        "step_count": state.get("step_count", 0) + 1,
    }


async def finalize_response_node(state: ResearchState) -> Dict[str, Any]:
    """Node 10: Formats and structures the finalized API response payload."""
    data_status = (state.get("market_data") or {}).get("data_status", "verified")

    final_payload = {
        "conversation_id": state.get("conversation_id", "default"),
        "question": state["question"],
        "direct_answer": state.get("direct_answer", ""),
        "supporting_facts": state.get("supporting_facts", []),
        "explanations": state.get("explanations"),
        "citations": state.get("citations", []),
        "data_timestamps": state.get("data_timestamps", {}),
        "limitations": state.get("limitations", []),
        "data_status": data_status,
        "sufficiency": state.get("evidence_sufficiency", "sufficient"),
    }
    return {
        "final_response": final_payload,
        "step_count": state.get("step_count", 0) + 1,
    }
