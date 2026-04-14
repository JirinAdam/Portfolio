"""Znovupoužitelné Plotly Express chart funkce pro dashboard."""

from typing import Optional

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


def make_skills_bar(
    skills_series: pd.Series, top_n: int = 20, title: str = ""
) -> go.Figure:
    """Horizontální bar chart — Top N skills podle počtu výskytů."""
    top = skills_series.head(top_n).sort_values(ascending=True)

    fig = px.bar(
        x=top.values,
        y=top.index,
        orientation="h",
        title=title,
        labels={"x": "Count", "y": "Skill"},
    )
    total = top.values.sum()
    pct = top.values / total * 100

    fig.update_traces(
        marker_color="#22D3EE",
        text=pct,
        texttemplate="%{text:.1f}%",
        textposition="outside",
        textfont=dict(size=16),
    )
    fig.update_layout(
        yaxis_title=None,
        xaxis_title="Count",
        yaxis=dict(tickfont=dict(size=16), automargin=True, ticklabelposition="outside left"),
        xaxis=dict(range=[0, top.values.max() * 1.15]),
        title_font_size=16,
        height=max(400, top_n * 28),
        margin=dict(l=5, r=5, t=30, b=10),
        font=dict(family="Space Grotesk, sans-serif"),
    )
    return fig


def make_salary_bar(
    df: pd.DataFrame,
    x_col: str,
    title: str = "",
    show_median: bool = True,
    show_mean: bool = True,
) -> go.Figure:
    """Horizontální grouped bar chart — Median / Mean salary."""
    sorted_df = df.sort_values("median_salary", ascending=True)

    fig = go.Figure()

    if show_median:
        fig.add_trace(go.Bar(
            x=sorted_df["median_salary"],
            y=sorted_df[x_col],
            name="Median",
            orientation="h",
            marker_color="#22D3EE",
            text=sorted_df["median_salary"],
            texttemplate="%{text:,.0f}",
            textposition="outside",
            textfont=dict(size=16),
            customdata=sorted_df["count"] if "count" in sorted_df.columns else None,
            hovertemplate=(
                "<b>%{y}</b><br>"
                "Median: %{x:,.0f} PLN<br>"
                + ("Count: %{customdata}<br>" if "count" in sorted_df.columns else "")
                + "<extra></extra>"
            ),
        ))

    if show_mean:
        fig.add_trace(go.Bar(
            x=sorted_df["mean_salary"],
            y=sorted_df[x_col],
            name="Mean",
            orientation="h",
            marker_color="#F43F5E",
            text=sorted_df["mean_salary"],
            texttemplate="%{text:,.0f}",
            textposition="outside",
            textfont=dict(size=16),
            customdata=sorted_df["count"] if "count" in sorted_df.columns else None,
            hovertemplate=(
                "<b>%{y}</b><br>"
                "Mean: %{x:,.0f} PLN<br>"
                + ("Count: %{customdata}<br>" if "count" in sorted_df.columns else "")
                + "<extra></extra>"
            ),
        ))

    fig.update_layout(
        title=title,
        title_font_size=16,
        barmode="group",
        xaxis_title="Monthly Max Salary (PLN)",
        yaxis_title=None,
        yaxis=dict(tickfont=dict(size=16), automargin=True, ticklabelposition="outside left"),
        xaxis=dict(
            tickformat=",",
            separatethousands=True,
        ),
        height=max(400, len(sorted_df) * 45),
        margin=dict(l=5, r=5, t=30, b=10),
        legend=dict(orientation="h", yanchor="bottom", y=1.005, xanchor="right", x=1, font=dict(size=18)),
        uniformtext=dict(minsize=16, mode="show"),
        font=dict(family="Space Grotesk, sans-serif"),
    )

    # Mezera jako oddělovač tisíců (Plotly používá locale separator přes "," format)
    fig.update_xaxes(tickprefix="", ticksuffix=" PLN")

    # X-axis padding pro textposition="outside"
    max_val = sorted_df[["median_salary", "mean_salary"]].max().max()
    fig.update_xaxes(range=[0, max_val * 1.15])

    return fig


def make_trend_line(
    df: pd.DataFrame,
    date_col: str = "date",
    value_col: str = "job_count",
    category_col: Optional[str] = None,
    title: str = "",
) -> go.Figure:
    """Plotly line chart pro historické trendové data."""
    if category_col:
        fig = px.line(
            df,
            x=date_col,
            y=value_col,
            color=category_col,
            title=title,
            markers=True,
        )
    else:
        fig = px.line(
            df,
            x=date_col,
            y=value_col,
            title=title,
            markers=True,
        )
        fig.update_traces(line_color="#22D3EE")

    fig.update_layout(
        title_font_size=16,
        xaxis_title="Date",
        yaxis_title="Job Count",
        xaxis=dict(tickformat="%Y-%m"),
        yaxis=dict(tickfont=dict(size=14)),
        height=500,
        margin=dict(l=5, r=5, t=30, b=10),
        hovermode="x unified",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.005,
            xanchor="right",
            x=1,
            font=dict(size=14),
        ),
        font=dict(family="Space Grotesk, sans-serif"),
    )
    return fig


def make_jobs_bar(
    df: pd.DataFrame,
    x_col: str = "job_count",
    y_col: str = "region",
    title: str = "",
) -> go.Figure:
    """Horizontální bar chart — počet jobů per region."""
    sorted_df = df.sort_values(x_col, ascending=True)

    fig = px.bar(
        sorted_df,
        x=x_col,
        y=y_col,
        orientation="h",
        title=title,
    )
    total = sorted_df[x_col].sum()
    pct = sorted_df[x_col] / total * 100

    fig.update_traces(
        marker_color="#22D3EE",
        text=pct,
        texttemplate="%{text:.1f}%",
        textposition="outside",
        textfont=dict(size=16),
        hovertemplate="<b>%{y}</b><br>Jobs: %{x}<extra></extra>",
    )
    fig.update_layout(
        yaxis_title=None,
        xaxis_title="Number of Job Postings",
        yaxis=dict(tickfont=dict(size=16), automargin=True, ticklabelposition="outside left"),
        xaxis=dict(range=[0, sorted_df[x_col].max() * 1.15]),
        title_font_size=16,
        height=max(400, len(sorted_df) * 32),
        margin=dict(l=5, r=5, t=30, b=10),
        font=dict(family="Space Grotesk, sans-serif"),
    )
    return fig
