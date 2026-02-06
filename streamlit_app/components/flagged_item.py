from __future__ import annotations

import streamlit as st
from typing import Any, Dict

from utils.i18n import t, t_severity


def render_flagged_item(flagged_data: Dict[str, Any], lang: str = "en"):
    v = flagged_data.get("violation", {}) or {}
    laws = flagged_data.get("laws", []) or []

    flag_reason = flagged_data.get("flag_reason", "Requires manual review")
    assumption_note = flagged_data.get("assumption_note", "")

    vtype = v.get("violation_type", "Unknown")
    display_name = vtype.replace("_", " ").title()
    desc = v.get("description", "")
    sev = (v.get("severity") or "medium").lower()

    why_label = t("why_flagged", lang)

    note_html = ""
    if assumption_note:
        note_html = f'<div style="font-size:0.78rem; color:#795548; margin-top:0.25rem; font-style:italic;">{assumption_note}</div>'

    st.markdown(
        f"""<div class="flagged-item">
  <div style="display:flex; align-items:center; margin-bottom:0.5rem; gap:0.4rem;">
    <span class="flagged-icon">⚠️</span>
    <strong style="color:#E65100; font-size:0.95rem;">{display_name}</strong>
    <span style="margin-left:auto; font-size:0.75rem; color:#5D4037; opacity:0.7;">{t_severity(sev, lang)}</span>
  </div>
  <p style="margin:0.25rem 0; font-size:0.88rem; color:#5D4037;">{desc}</p>
  <div style="font-size:0.82rem; color:#BF360C; margin-top:0.4rem;"><strong>{why_label}:</strong> {flag_reason}</div>
  {note_html}
</div>""",
        unsafe_allow_html=True,
    )

    if laws:
        with st.expander("Conditional laws (if confirmed)"):
            for law in laws:
                st.markdown(f"- **{law.get('citation', '')}**: {law.get('interpretation', '')}")
