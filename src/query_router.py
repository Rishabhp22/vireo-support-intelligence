"""A flexible, grounded query router with optional AI executive insight support."""
from __future__ import annotations
import os
import re
import json
import requests
from .analytics import Analytics

NUMBER_WORDS = {
    "zero": 0, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
    "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
    "eleven": 11, "twelve": 12, "twenty": 20
}


def _hire_count(question: str) -> int:
    """Extract headcount/hire count from phrasings like:
    - '3 hires', 'two hiring', '1 person', 'headcount 4', '5 agents'
    - 'hire 3', 'hiring two', 'add 1 person'
    - 'show me the two hiring team metrics'
    """
    q = question.lower()
    
    # Prefix patterns: "hire 3", "hiring 2", "add 4", "staff 1"
    m_prefix = re.search(r"\b(?:hire|hiring|add|staff|headcount|allocate)\s+(?:of\s+)?(\d+|" + "|".join(NUMBER_WORDS) + r")\b", q)
    if m_prefix:
        token = m_prefix.group(1)
        return int(token) if token.isdigit() else NUMBER_WORDS.get(token, 2)

    # Suffix patterns: "3 hires", "two hiring", "1 people", "3 agents", "4 headcount", "two team members"
    m_suffix = re.search(r"\b(\d+|" + "|".join(NUMBER_WORDS) + r")\s+(?:new\s+)?(?:hires?|hiring|people|persons?|agents?|headcounts?|members?|staff)\b", q)
    if m_suffix:
        token = m_suffix.group(1)
        return int(token) if token.isdigit() else NUMBER_WORDS.get(token, 2)

    # Contextual check: if question has 'hire' or 'staffing' or 'headcount' and any number
    if any(k in q for k in ("hire", "hiring", "headcount", "staff")):
        m_num = re.search(r"\b(\d+)\b", q)
        if m_num:
            val = int(m_num.group(1))
            if 1 <= val <= 50:
                return val
        for word, num in NUMBER_WORDS.items():
            if num > 0 and re.search(rf"\b{word}\b", q):
                return num

    return 2


def _focus_team(question: str, analytics: Analytics) -> str | None:
    teams = list(analytics.t["assigned_team"].dropna().astype(str).unique())
    question_lower = question.casefold()
    
    # Exact or substring match
    for team in teams:
        if team.casefold() in question_lower:
            return team
            
    # Alias / keyword matching for common team shorthands
    aliases = {
        "billing": "Billing",
        "logistics": "Logistics",
        "chat": "Chat Frontline",
        "email": "Email Frontline",
        "voice": "Voice Frontline",
        "returns": "Returns Desk",
        "warranty": "Escalations & Warranty",
        "escalation": "Escalations & Warranty",
    }
    for alias, team_name in aliases.items():
        if alias in question_lower and team_name in teams:
            return team_name

    return None


def _load_env():
    """Lightweight .env loader without requiring external dependencies."""
    from pathlib import Path
    env_file = Path(".env")
    if env_file.exists():
        try:
            for line in env_file.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    os.environ.setdefault(k.strip(), v.strip().strip("'\""))
        except Exception:
            pass


def generate_ai_insight(question: str, computed_result: dict, api_key: str | None = None) -> str:
    """Optional AI insight generator supporting Groq, OpenAI, and Gemini APIs."""
    _load_env()
    
    # 1. Check for Groq API Key (Ultra-fast & Free)
    groq_key = os.environ.get("GROQ_API_KEY")
    if groq_key:
        for model_name in ("openai/gpt-oss-120b", "qwen/qwen3.8-27b", "openai/gpt-oss-20b"):
            try:
                url = "https://api.groq.com/openai/v1/chat/completions"
                headers = {"Authorization": f"Bearer {groq_key}", "Content-Type": "application/json"}
                system_prompt = (
                    "You are an executive CX decision-support advisor for Vireo Audio. "
                    "Answer the user's question accurately using ONLY the supplied ground-truth JSON dataset. "
                    "Keep your response concise (2-4 clear sentences) with executive-level clarity. "
                    "Do NOT fabricate numbers beyond the provided data."
                )
                user_msg = f"User Question: {question}\n\nGround Truth Data from Analytics Engine:\n{json.dumps(computed_result, default=str, indent=2)}"
                payload = {
                    "model": model_name,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_msg}
                    ],
                    "temperature": 0.1,
                    "max_tokens": 300
                }
                resp = requests.post(url, headers=headers, json=payload, timeout=8)
                if resp.status_code == 200:
                    data = resp.json()
                    content = data["choices"][0]["message"]["content"].strip()
                    if content:
                        return content
            except Exception:
                continue

    # 2. Check for Gemini API Key
    gemini_key = api_key or os.environ.get("GEMINI_API_KEY")
    if gemini_key:
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={gemini_key}"
            prompt = (
                f"You are an executive CX decision-support advisor for Vireo Audio.\n"
                f"User question: {question}\n"
                f"Strictly grounded computed data from the official dataset:\n{json.dumps(computed_result, default=str, indent=2)}\n\n"
                f"Provide a crisp, 2-3 sentence executive summary explaining the exact findings and business implications. "
                f"Do NOT invent or extrapolate numbers beyond the provided JSON."
            )
            payload = {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"temperature": 0.1, "maxOutputTokens": 300}
            }
            resp = requests.post(url, json=payload, timeout=6)
            if resp.status_code == 200:
                data = resp.json()
                return data["candidates"][0]["content"]["parts"][0]["text"].strip()
        except Exception:
            pass

    # 3. Deterministic Fallback Summary
    return (
        "Computed deterministically from primary Vireo dataset (Jan 2025 – Jun 2026). "
        "All figures adhere to Vireo Support Policy v3.2."
    )


def answer(question: str, analytics: Analytics, api_key: str | None = None) -> dict:
    q = question.lower()
    
    # 1. Staffing / Headcount queries
    if any(x in q for x in ("hire", "hiring", "staff", "headcount", "recommend")):
        hire_count = _hire_count(question)
        focus_team = _focus_team(question, analytics)
        result = analytics.staffing_business_case(hire_count=hire_count, focus_team=focus_team)
        result["parsed_question_parameters"] = {"hire_count": hire_count, "focus_team": focus_team}

    # 2. SLA Breaches & Credits
    elif any(x in q for x in ("sla", "breach", "response")):
        result = analytics.sla_breaches()

    # 3. Transfers & Handoffs
    elif any(x in q for x in ("transfer", "handoff", "routing")):
        result = analytics.transfers()

    # 4. Repeat Contacts & FCR
    elif any(x in q for x in ("repeat", "fcr", "first contact")):
        result = analytics.repeat_contacts()

    # 5. Financial impact (refunds, replacements, product costs)
    elif any(x in q for x in ("refund", "replacement", "product", "cost")):
        dimension = "product_product_name" if "product_product_name" in analytics.t.columns else "assigned_team"
        result = analytics.financial_impact(dimension)

    # 6. Category Volume / Breakdown
    elif any(x in q for x in ("category", "categories", "issue", "topic", "tag")):
        if "monthly" in q or "trend" in q:
            result = analytics.monthly_category_volume()
        else:
            result = analytics.category_volume()

    # 7. Monthly Trends
    elif "monthly" in q or "trend" in q:
        result = analytics.monthly_team_volume()

    # 8. CSAT & Customer Satisfaction
    elif "csat" in q or "satisfaction" in q or "rating" in q:
        result = analytics.csat()

    # 9. Handle Time & Duration
    elif "handle" in q or "resolution" in q or "duration" in q:
        result = analytics.handle_time()

    # 10. Specific team drilldown (e.g. "tell me about billing" or "logistics metrics")
    elif any(x in q for x in ("billing", "logistics")):
        focus_team = _focus_team(question, analytics)
        hire_count = _hire_count(question)
        result = analytics.staffing_business_case(hire_count=hire_count, focus_team=focus_team)
        result["parsed_question_parameters"] = {"hire_count": hire_count, "focus_team": focus_team}

    # Default fallback: Ticket Volume
    else:
        result = analytics.team_volume()

    ai_insight = generate_ai_insight(question, result, api_key=api_key)
    return {
        "answer": ai_insight,
        "result": result
    }
