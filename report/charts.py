"""
Plotly chart builders for the portfolio report.

Plotly 6 compatibility notes:
- Use go.Heatmap directly (px.imshow with aspect="equal" collapses)
- Pass z as plain Python nested list of floats (numpy arrays render as scatter)
- Use go.Treemap with explicit root node (px.treemap flat lists break)
- Convert pandas index to str list for go.Scatter x-axis
"""

from typing import Dict, Any

import plotly.graph_objects as go

from config import CAC40_ESG_BENCHMARK, COMPANY_NAMES, ESG_GRADE_COLOURS, ESG_SCORES, STRESS_PERIODS

SLEEVE_COLOURS: Dict[str, str] = {
    "Growth": "#0055b3",
    "Defensive": "#00b894",
    "Financial & Energy": "#e17055",
    "High Conviction": "#6c5ce7",
}

SECTOR_PALETTE = [
    "#4e79a7", "#f28e2b", "#e15759", "#76b7b2", "#59a14f",
    "#edc948", "#b07aa1", "#ff9da7", "#9c755f", "#bab0ac",
]


def build_cumulative_return_chart(portfolio_returns, benchmark_returns) -> str:
    """Render cumulative return of portfolio vs CAC 40 benchmark."""
    port_cum = ((1 + portfolio_returns).cumprod() - 1) * 100
    bm_cum = ((1 + benchmark_returns).cumprod() - 1) * 100

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=port_cum.index.astype(str).tolist(),
        y=port_cum.round(2).tolist(),
        mode="lines",
        name="Portfolio",
        line=dict(color="#0055b3", width=2),
    ))
    fig.add_trace(go.Scatter(
        x=bm_cum.index.astype(str).tolist(),
        y=bm_cum.round(2).tolist(),
        mode="lines",
        name="CAC 40 (^FCHI)",
        line=dict(color="#636e72", width=1.5, dash="dash"),
    ))
    fig.add_hline(y=0, line_width=1, line_color="#b2bec3")
    fig.update_layout(
        yaxis_title="Cumulative Return (%)",
        xaxis_title="Date",
        legend=dict(orientation="h", y=-0.15),
        margin=dict(l=60, r=20, t=20, b=60),
        height=350,
        yaxis=dict(tickformat=".1f"),
    )
    return fig.to_html(full_html=False, include_plotlyjs=False)


def build_sleeve_cumulative_chart(sleeve_cum, benchmark_returns) -> str:
    """Render cumulative return per sleeve + CAC 40 benchmark, all indexed to 100."""
    bm_cum = (1 + benchmark_returns).cumprod() * 100

    fig = go.Figure()
    for sleeve in sleeve_cum.columns:
        fig.add_trace(go.Scatter(
            x=sleeve_cum.index.astype(str).tolist(),
            y=sleeve_cum[sleeve].round(2).tolist(),
            mode="lines",
            name=sleeve,
            line=dict(width=2, color=SLEEVE_COLOURS.get(sleeve, "#888888")),
        ))
    fig.add_trace(go.Scatter(
        x=bm_cum.index.astype(str).tolist(),
        y=bm_cum.round(2).tolist(),
        mode="lines",
        name="CAC 40 (^FCHI)",
        line=dict(color="#636e72", width=1.5, dash="dash"),
    ))
    fig.add_hline(y=100, line_width=1, line_color="#b2bec3")
    fig.update_layout(
        yaxis_title="Indexed Return (100 = start)",
        xaxis_title="Date",
        legend=dict(orientation="h", y=-0.15),
        margin=dict(l=60, r=20, t=20, b=60),
        height=350,
    )
    return fig.to_html(full_html=False, include_plotlyjs=False)


def build_beta_chart(rolling_beta) -> str:
    """Render 30-day rolling beta vs CAC 40 with a β=1 reference line."""
    fig = go.Figure(
        go.Scatter(
            x=rolling_beta.index.astype(str).tolist(),
            y=rolling_beta.round(3).tolist(),
            mode="lines",
            line=dict(color="#0055b3", width=2),
            name="Rolling Beta",
        )
    )
    fig.add_hline(y=1.0, line_dash="dash", line_color="#636e72", line_width=1,
                  annotation_text="β = 1", annotation_position="right")
    fig.update_layout(
        yaxis_title="Beta (vs ^FCHI)",
        xaxis_title="Date",
        margin=dict(l=60, r=60, t=20, b=60),
        height=280,
        yaxis=dict(tickformat=".2f"),
    )
    return fig.to_html(full_html=False, include_plotlyjs=False)


def build_drawdown_chart(drawdown_series) -> str:
    """Render portfolio drawdown time series as a filled area chart."""
    fig = go.Figure(
        go.Scatter(
            x=drawdown_series.index.astype(str).tolist(),
            y=drawdown_series.round(2).tolist(),
            mode="lines",
            fill="tozeroy",
            fillcolor="rgba(214, 48, 49, 0.15)",
            line=dict(color="#d63031", width=1.5),
            name="Drawdown",
        )
    )
    fig.update_layout(
        yaxis_title="Drawdown (%)",
        xaxis_title="Date",
        margin=dict(l=60, r=20, t=20, b=60),
        height=280,
        yaxis=dict(tickformat=".1f"),
    )
    return fig.to_html(full_html=False, include_plotlyjs=False)


def build_rolling_vol_chart(rolling_vol) -> str:
    """Render rolling 30-day annualised volatility line chart per sleeve."""
    fig = go.Figure()
    for sleeve in rolling_vol.columns:
        fig.add_trace(
            go.Scatter(
                x=rolling_vol.index.astype(str).tolist(),
                y=(rolling_vol[sleeve] * 100).round(2).tolist(),
                mode="lines",
                name=sleeve,
                line=dict(width=2, color=SLEEVE_COLOURS.get(sleeve, "#888888")),
            )
        )
    for period in STRESS_PERIODS:
        fig.add_vrect(
            x0=period["start"], x1=period["end"],
            fillcolor="rgba(214, 48, 49, 0.08)",
            line_width=0,
            annotation_text=period["label"],
            annotation_position="top left",
            annotation_font_size=10,
            annotation_font_color="#d63031",
        )
    fig.update_layout(
        yaxis_title="Volatility (%)",
        xaxis_title="Date",
        legend=dict(orientation="h", y=-0.15),
        margin=dict(l=50, r=20, t=30, b=60),
        height=350,
    )
    return fig.to_html(full_html=False, include_plotlyjs=False)


def build_sector_chart(sector_over_under) -> str:
    """Render diverging horizontal bar chart of sector over/underweight vs CAC 40."""
    sectors = list(sector_over_under.keys())
    values = [v * 100 for v in sector_over_under.values()]
    colours = ["#0055b3" if v >= 0 else "#e17055" for v in values]

    fig = go.Figure(
        go.Bar(x=values, y=sectors, orientation="h", marker_color=colours)
    )
    fig.add_vline(x=0, line_width=1, line_color="black")
    fig.update_layout(
        xaxis_title="Over/Underweight (%)",
        margin=dict(l=160, r=20, t=20, b=40),
        height=520,
    )
    return fig.to_html(full_html=False, include_plotlyjs=False)


def build_corr_heatmap(corr_matrix) -> str:
    """Render annotated pairwise correlation heatmap for all holdings."""
    labels = corr_matrix.columns.tolist()
    z = [[round(float(v), 2) for v in row] for row in corr_matrix.values]
    text = [[f"{v:.2f}" for v in row] for row in z]

    fig = go.Figure(
        go.Heatmap(
            z=z,
            x=labels,
            y=labels,
            colorscale="RdBu_r",
            zmin=-1,
            zmax=1,
            text=text,
            texttemplate="%{text}",
            textfont=dict(size=10),
            colorbar=dict(title="ρ", thickness=14),
        )
    )
    fig.update_layout(
        margin=dict(l=90, r=40, t=20, b=110),
        height=520,
        xaxis=dict(tickangle=-45, tickfont=dict(size=11), side="bottom"),
        yaxis=dict(tickfont=dict(size=11), autorange="reversed"),
    )
    return fig.to_html(full_html=False, include_plotlyjs=False)


def build_esg_chart(net_weights: Dict[str, float]) -> str:
    """Render horizontal bar chart of ESG scores by issuer vs CAC 40 benchmark."""
    sorted_tickers = sorted(
        [t for t in net_weights if t in ESG_SCORES],
        key=lambda t: net_weights[t],
        reverse=True,
    )

    scores = [ESG_SCORES[t]["score"] for t in sorted_tickers]
    grades = [ESG_SCORES[t]["grade"] for t in sorted_tickers]
    colours = [ESG_GRADE_COLOURS.get(g, "#888888") for g in grades]

    fig = go.Figure(
        go.Bar(
            x=scores,
            y=sorted_tickers,
            orientation="h",
            marker_color=colours,
            text=[f"{g} ({s})" for g, s in zip(grades, scores)],
            textposition="outside",
        )
    )
    fig.add_vline(
        x=CAC40_ESG_BENCHMARK,
        line_dash="dash",
        line_color="#d63031",
        line_width=1.5,
        annotation_text="CAC 40 avg",
        annotation_position="top",
        annotation_font_color="#d63031",
    )
    fig.update_layout(
        title=dict(
            text="ESG Score by Issuer (MSCI) — Portfolio vs CAC 40 Benchmark",
            font=dict(size=13),
            x=0,
        ),
        xaxis=dict(range=[0, 10], title="MSCI ESG Score"),
        yaxis=dict(autorange="reversed"),
        margin=dict(l=90, r=100, t=50, b=40),
        height=420,
    )
    return fig.to_html(full_html=False, include_plotlyjs=False)


def build_treemap(net_weights: Dict[str, float], sector_map: Dict[str, str]) -> str:
    """Render portfolio weight treemap: Portfolio → Sector → Ticker hierarchy."""
    tickers = list(net_weights.keys())
    weights = [net_weights[t] * 100 for t in tickers]
    sectors = [sector_map.get(t, "Other") for t in tickers]
    unique_sectors = sorted(set(sectors))

    sector_colours = dict(zip(unique_sectors, SECTOR_PALETTE))

    ids, labels, parents, vals, colours = [], [], [], [], []

    ids.append("Portfolio")
    labels.append("Portfolio")
    parents.append("")
    vals.append(sum(weights))
    colours.append("#ffffff")

    for sec in unique_sectors:
        sec_w = sum(w for t, w, s in zip(tickers, weights, sectors) if s == sec)
        ids.append(sec)
        labels.append(sec)
        parents.append("Portfolio")
        vals.append(sec_w)
        colours.append(sector_colours[sec])

    customdata = []
    for t, w, sec in zip(tickers, weights, sectors):
        ids.append(t)
        labels.append(f"{t}<br>{w:.1f}%")
        parents.append(sec)
        vals.append(w)
        colours.append(sector_colours[sec])
        customdata.append(COMPANY_NAMES.get(t, t))

    fig = go.Figure(
        go.Treemap(
            ids=ids,
            labels=labels,
            parents=parents,
            values=vals,
            marker=dict(colors=colours),
            textfont=dict(size=13),
            branchvalues="total",
            customdata=[""] * (len(ids) - len(tickers)) + customdata,
            hovertemplate="<b>%{label}</b><br>%{customdata}<br>Weight: %{value:.1f}%<extra></extra>",
        )
    )
    fig.update_layout(margin=dict(l=10, r=10, t=10, b=10), height=480)
    return fig.to_html(full_html=False, include_plotlyjs=False)
