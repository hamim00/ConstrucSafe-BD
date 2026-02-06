from __future__ import annotations

import streamlit as st
from typing import Any, Dict

_SEV_COLORS = {
    "critical": "#DC3545",
    "high": "#FD7E14",
    "medium": "#FFC107",
    "low": "#28A745",
}

def _sev_badge(sev: str) -> str:
    color = _SEV_COLORS.get(sev, "#2E75B6")
    return f'<span class="severity-badge" style="background:{color};">{sev.upper()}</span>'

def _conf_badge(conf: str) -> str:
    return f'<span class="confidence-badge">{conf.upper()}</span>'


def render_violation_card(violation_data: Dict[str, Any]):
    v = violation_data.get("violation", {}) or {}
    laws = violation_data.get("laws", []) or []
    penalties = violation_data.get("penalties", []) or []
    actions = violation_data.get("recommended_actions", []) or []

    vtype = v.get("violation_type", "Unknown")
    desc = v.get("description", "")
    sev = (v.get("severity") or "medium").lower()
    conf = (v.get("confidence") or "medium").lower()
    loc = v.get("location", "")
    parties = v.get("affected_parties", [])

    st.markdown(
        f'''
        <div class="violation-card">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <h4 style="margin:0; color:#1F4E79;">{vtype}</h4>
                <div>{_sev_badge(sev)} {_conf_badge(conf)}</div>
            </div>
            <p style="margin:0.75rem 0 0.5rem 0;">{desc}</p>
            <div style="font-size:0.85rem; color:#666;">
                <div><strong>Location:</strong> {loc or "N/A"}</div>
                <div><strong>Affected:</strong> {", ".join(parties) if parties else "N/A"}</div>
            </div>
        </div>
        ''',
        unsafe_allow_html=True,
    )

    if laws:
        with st.expander("📚 Legal references"):
            for law in laws:
                st.markdown(
                    f'''
                    <div class="law-reference">
                        <div class="law-citation">{law.get("source_id","")} • {law.get("citation","")}</div>
                        <div style="font-size:0.9rem;">{law.get("interpretation","")}</div>
                        <div style="font-size:0.8rem; color:#666; margin-top:0.25rem;">Confidence: {law.get("confidence","")}</div>
                    </div>
                    ''',
                    unsafe_allow_html=True,
                )

    if penalties:
        with st.expander("💰 Penalties (profiles)"):
            for p in penalties:
                law_name = p.get("law_name", "")
                section = p.get("section", "")
                summary = p.get("summary", "")
                fine_max = p.get("fine_max_bdt")
                fine_min = p.get("fine_min_bdt")
                imp_months = p.get("imprisonment_max_months")
                imp_years = p.get("imprisonment_max_years")

                parts = []
                if fine_min is not None or fine_max is not None:
                    if fine_min is not None and fine_max is not None:
                        parts.append(f"Fine: ৳{fine_min:,}–৳{fine_max:,}")
                    elif fine_max is not None:
                        parts.append(f"Fine up to: ৳{fine_max:,}")
                    elif fine_min is not None:
                        parts.append(f"Fine from: ৳{fine_min:,}")
                if imp_months is not None:
                    parts.append(f"Imprisonment up to: {imp_months} months")
                if imp_years is not None:
                    parts.append(f"Imprisonment up to: {imp_years} years")

                st.markdown(
                    f'''
                    <div class="penalty-box">
                        <div><strong>{law_name}</strong> ({section})</div>
                        <div style="margin-top:0.25rem; color:#666;">{summary}</div>
                        <div class="penalty-amount" style="margin-top:0.4rem;">{" • ".join(parts) if parts else ""}</div>
                    </div>
                    ''',
                    unsafe_allow_html=True,
                )

    if actions:
        with st.expander("✅ Recommended actions"):
            for a in actions:
                st.markdown(f"- {a}")
