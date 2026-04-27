"""Generate a plain-English portfolio narrative using a local or cloud LLM."""

import logging
import re

from pipeline.metrics import PortfolioMetrics

_THINK_RE = re.compile(r"<think>.*?</think>", re.DOTALL)

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = (
    "You are a senior portfolio analyst writing a concise narrative for an institutional "
    "investor report. Be factual, professional, and precise. No marketing language. No disclaimers."
)

_USER_PROMPT_TEMPLATE = """/no_think Write one paragraph (150-200 words) for an institutional investor report \
on a French equity portfolio (CAC 40 universe, 1-year period).

Portfolio data:
- Annualised return: {return:.2%} vs CAC 40 benchmark: {benchmark:.2%} (alpha: {alpha:+.2%})
- Volatility: {vol:.2%} | Sharpe: {sharpe:.2f} | Beta: {beta:.2f}
- Max Drawdown: {mdd:.2%} | Calmar: {calmar:.2f}
- VaR (95%, 1-day): {var:.2%} | CVaR: {cvar:.2%}
- Tracking Error: {te:.2%} | Information Ratio: {ir:.2f}
- HHI concentration: {hhi:.4f} ({hhi_label})
- ESG: {esg_score:.1f}/10 ({esg_grade}) vs CAC 40 benchmark 5.8 ({esg_delta:+.1f})
- Top performing sleeve: {top_sleeve} at {top_sleeve_return:.2%} annualised

Cover: alpha generation, key risk metrics, ESG position vs benchmark, concentration.
Output only the paragraph. No headers, no bullets, no preamble."""


def _build_prompt(metrics: PortfolioMetrics) -> str:
    alpha = metrics.annualised_return - metrics.benchmark_annualised_return
    top_sleeve = max(metrics.sleeve_returns, key=metrics.sleeve_returns.get) if metrics.sleeve_returns else "N/A"
    top_sleeve_return = metrics.sleeve_returns.get(top_sleeve, 0.0)
    return _USER_PROMPT_TEMPLATE.format(
        **{
            "return": metrics.annualised_return,
            "benchmark": metrics.benchmark_annualised_return,
            "alpha": alpha,
            "vol": metrics.annualised_volatility,
            "sharpe": metrics.sharpe_ratio,
            "beta": metrics.beta,
            "mdd": metrics.max_drawdown,
            "calmar": metrics.calmar_ratio,
            "var": metrics.var_pct,
            "cvar": metrics.cvar_pct,
            "te": metrics.tracking_error,
            "ir": metrics.information_ratio,
            "hhi": metrics.hhi,
            "hhi_label": metrics.hhi_label,
            "esg_score": metrics.portfolio_esg_score,
            "esg_grade": metrics.portfolio_esg_grade,
            "esg_delta": metrics.esg_vs_benchmark,
            "top_sleeve": top_sleeve,
            "top_sleeve_return": top_sleeve_return,
        }
    )


def _call_local(user_prompt: str) -> str:
    """Call LM Studio at 192.168.1.101:1234 via the openai-compatible API."""
    import openai

    client = openai.OpenAI(base_url="http://192.168.1.101:1234/v1", api_key="lm-studio")

    model = "qwen3.6-27B"
    try:
        models_response = client.models.list()
        if models_response.data:
            model = models_response.data[0].id
            logger.info("LM Studio model discovered: %s", model)
    except Exception:
        logger.warning("Could not discover LM Studio model; using fallback: %s", model)

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.3,
        max_tokens=300,
    )
    raw = response.choices[0].message.content
    return _THINK_RE.sub("", raw).strip()


def _call_claude(user_prompt: str) -> str:
    """Call Claude via the Anthropic API."""
    import anthropic

    client = anthropic.Anthropic()
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=300,
        system=_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_prompt}],
    )
    return response.content[0].text.strip()


def generate_summary(metrics: PortfolioMetrics, backend: str = "local") -> str:
    """Generate a plain-English portfolio narrative using a local or cloud LLM.

    Args:
        metrics: Fully computed PortfolioMetrics dataclass.
        backend: "local" for LM Studio (192.168.1.101:1234) or "claude" for Anthropic API.

    Returns:
        A 150-200 word narrative string, or empty string if backend unreachable.
    """
    user_prompt = _build_prompt(metrics)
    try:
        if backend == "local":
            return _call_local(user_prompt)
        return _call_claude(user_prompt)
    except Exception as exc:
        logger.warning("AI narrative generation failed (%s backend): %s", backend, exc)
        return ""
