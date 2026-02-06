from __future__ import annotations

import streamlit as st
from typing import Any, Dict


def render_summary_metrics(ui_summary: Dict[str, Any]):
    c1, c2, c3, c4, c5 = st.columns(5)

    with c1:
        st.markdown(f'''
        <div class="metric-card">
            <div class="metric-value" style="color: #1F4E79;">{ui_summary.get('total', 0)}</div>
            <div class="metric-label">Total</div>
        </div>
        ''', unsafe_allow_html=True)

    with c2:
        st.markdown(f'''
        <div class="metric-card">
            <div class="metric-value" style="color: #FD7E14;">{ui_summary.get('high_count', 0)}</div>
            <div class="metric-label">High</div>
        </div>
        ''', unsafe_allow_html=True)

    with c3:
        st.markdown(f'''
        <div class="metric-card">
            <div class="metric-value" style="color: #FFC107;">{ui_summary.get('medium_count', 0)}</div>
            <div class="metric-label">Medium</div>
        </div>
        ''', unsafe_allow_html=True)

    with c4:
        st.markdown(f'''
        <div class="metric-card">
            <div class="metric-value" style="color: #28A745;">{ui_summary.get('low_count', 0)}</div>
            <div class="metric-label">Low</div>
        </div>
        ''', unsafe_allow_html=True)

    with c5:
        st.markdown(f'''
        <div class="metric-card">
            <div class="metric-value" style="color: #856404;">{ui_summary.get('flagged_for_review_count', 0)}</div>
            <div class="metric-label">⚠️ Review</div>
        </div>
        ''', unsafe_allow_html=True)
