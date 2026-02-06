from __future__ import annotations

import streamlit as st
from typing import Any, Dict


def render_flagged_item(flagged_data: Dict[str, Any]):
    v = flagged_data.get("violation", {}) or {}
    laws = flagged_data.get("laws", []) or []

    flag_reason = flagged_data.get("flag_reason", "Requires manual review")
    assumption_note = flagged_data.get("assumption_note", "")

    st.markdown(
        f'''
        <div class="flagged-item">
            <div style="display:flex; align-items:center; margin-bottom:0.5rem;">
                <span class="flagged-icon">⚠️</span>
                <strong style="color:#856404;">{v.get("violation_type","Unknown")}</strong>
            </div>
            <p style="margin:0.25rem 0;">{v.get("description","")}</p>
            <div style="font-size:0.85rem; color:#856404;"><strong>Why flagged:</strong> {flag_reason}</div>
            <div style="font-size:0.8rem; color:#666; margin-top:0.25rem;">{assumption_note}</div>
        </div>
        ''',
        unsafe_allow_html=True,
    )

    if laws:
        with st.expander("📚 Conditional laws (if confirmed)"):
            for law in laws:
                st.markdown(f"- **{law.get('citation','')}**: {law.get('interpretation','')}")
