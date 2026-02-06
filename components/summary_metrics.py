from __future__ import annotations

import streamlit as st
from typing import Any, Dict

from utils.i18n import t


def render_summary_metrics(ui_summary: Dict[str, Any], lang: str = "en"):
    """Render colorful, compact KPI cards for analysis summary."""

    total = ui_summary.get("total", 0)
    # Compute total from parts if not provided
    if total == 0:
        total = (
            ui_summary.get("critical_count", 0)
            + ui_summary.get("high_count", 0)
            + ui_summary.get("medium_count", 0)
            + ui_summary.get("low_count", 0)
        )

    high_count = ui_summary.get("critical_count", 0) + ui_summary.get("high_count", 0)
    medium_count = ui_summary.get("medium_count", 0)
    low_count = ui_summary.get("low_count", 0)
    flagged_count = ui_summary.get("flagged_for_review_count", 0)

    st.markdown(
        f"""
        <div class="metrics-row">
            <div class="metric-card metric-total">
                <div class="metric-icon">📊</div>
                <div class="metric-value" style="color: #1565C0;">{total}</div>
                <div class="metric-label">{t('total', lang)}</div>
            </div>
            <div class="metric-card metric-high">
                <div class="metric-icon">🔴</div>
                <div class="metric-value" style="color: #EF6C00;">{high_count}</div>
                <div class="metric-label">{t('high', lang)}</div>
            </div>
            <div class="metric-card metric-medium">
                <div class="metric-icon">🟡</div>
                <div class="metric-value" style="color: #F9A825;">{medium_count}</div>
                <div class="metric-label">{t('medium', lang)}</div>
            </div>
            <div class="metric-card metric-low">
                <div class="metric-icon">🟢</div>
                <div class="metric-value" style="color: #2E7D32;">{low_count}</div>
                <div class="metric-label">{t('low', lang)}</div>
            </div>
            <div class="metric-card metric-review">
                <div class="metric-icon">⚠️</div>
                <div class="metric-value" style="color: #7B1FA2;">{flagged_count}</div>
                <div class="metric-label">{t('review', lang)}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
