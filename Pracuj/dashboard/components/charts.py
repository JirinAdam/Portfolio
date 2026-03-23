"""Znovupoužitelné Plotly Express chart funkce pro dashboard."""

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
    fig.update_traces(
        marker_color="#22D3EE",
        text=top.values,
        texttemplate="%{text:,}",
        textposition="outside",
    )
    fig.update_layout(
        yaxis_title=None,
        xaxis_title="Count",
        height=max(400, top_n * 28),
        margin=dict(l=10, r=10, t=40, b=10),
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
            marker_color="#FD35D7",
            text=sorted_df["median_salary"],
            texttemplate="%{text:,.0f}",
            textposition="outside",
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
        barmode="group",
        xaxis_title="Monthly Max Salary (PLN)",
        yaxis_title=None,
        xaxis=dict(
            tickformat=",",
            separatethousands=True,
        ),
        height=max(400, len(sorted_df) * 32),
        margin=dict(l=10, r=10, t=40, b=10),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        font=dict(family="Space Grotesk, sans-serif"),
    )

    # Mezera jako oddělovač tisíců (Plotly používá locale separator přes "," format)
    fig.update_xaxes(tickprefix="", ticksuffix=" PLN")

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
    fig.update_traces(
        marker_color="#22D3EE",
        text=sorted_df[x_col],
        texttemplate="%{text:,}",
        textposition="outside",
        hovertemplate="<b>%{y}</b><br>Jobs: %{x}<extra></extra>",
    )
    fig.update_layout(
        yaxis_title=None,
        xaxis_title="Number of Job Postings",
        height=max(400, len(sorted_df) * 32),
        margin=dict(l=10, r=10, t=40, b=10),
        font=dict(family="Space Grotesk, sans-serif"),
    )
    return fig
