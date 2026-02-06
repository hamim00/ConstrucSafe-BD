from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

import streamlit as st

from utils.source_catalog import source_title, source_portal_url
from utils.ui import get_api_client

_SEV_COLORS = {
    "critical": "#DC3545",
    "high": "#FD7E14",
    "medium": "#FFC107",
    "low": "#28A745",
}

_CONF_RANK = {"high": 3.0, "medium": 2.0, "low": 1.0}


def _sev_badge(sev: str) -> str:
    color = _SEV_COLORS.get(sev, "#2E75B6")
    return f'<span class="severity-badge" style="background:{color};">{sev.upper()}</span>'


def _conf_badge(conf: str) -> str:
    return f'<span class="confidence-badge">{conf.upper()}</span>'


def _conf_rank(conf: Any) -> float:
    if conf is None:
        return 0.0
    if isinstance(conf, (int, float)):
        return float(conf)
    s = str(conf).strip().lower()
    if s in _CONF_RANK:
        return _CONF_RANK[s]
    try:
        return float(s)
    except Exception:
        return 0.0


def _pick_primary_law(laws: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    if not laws:
        return None
    # Prefer higher confidence; stable fallback is the first element
    return sorted(laws, key=lambda x: _conf_rank(x.get("confidence")), reverse=True)[0]


_AUTH_RE = re.compile(r":\s*([A-Za-z0-9_\-]+)\s*$")


def _extract_authority_id(action: str) -> Optional[str]:
    if not action or not isinstance(action, str):
        return None
    m = _AUTH_RE.search(action)
    if m:
        return m.group(1).strip()
    return None


@st.cache_data(show_spinner=False, ttl=3600)
def _get_authority_info(authority_id: str) -> Optional[Dict[str, Any]]:
    try:
        client = get_api_client()
        return client.get_authority(authority_id)
    except Exception:
        return None


def _fmt_bdt(x: Any) -> Optional[str]:
    try:
        if x is None:
            return None
        val = int(x)
        return f"৳{val:,}"
    except Exception:
        return None


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
            <div style="display:flex; justify-content:space-between; align-items:center; gap: 0.75rem;">
                <h4 style="margin:0; color:#1F4E79;">{vtype}</h4>
                <div style="white-space:nowrap;">{_sev_badge(sev)} {_conf_badge(conf)}</div>
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

    # --- Key legal basis (user-friendly) ---
    primary = _pick_primary_law(laws) if isinstance(laws, list) else None
    if primary:
        sid = primary.get("source_id") or "Unknown"
        title = source_title(str(sid))
        portal = source_portal_url(str(sid))
        citation = primary.get("citation") or ""
        interp = primary.get("interpretation") or ""
        conf_val = primary.get("confidence") or ""

        portal_html = f' • <a href="{portal}" target="_blank">official portal</a>' if portal else ""
        st.markdown(
            f'''
            <div class="law-highlight">
              <div class="law-source-title">Key legal basis: {title}{portal_html}</div>
              <div class="law-meta"><strong>Citation:</strong> {citation}</div>
              <div class="law-meta"><strong>Why this matches:</strong> {interp}</div>
              <div class="law-meta" style="opacity:0.85;"><strong>Confidence:</strong> {conf_val}</div>
            </div>
            ''',
            unsafe_allow_html=True,
        )

    # --- Legal references (full list, grouped) ---
    if laws:
        with st.expander("📚 All legal references"):
            grouped: Dict[str, List[Dict[str, Any]]] = {}
            for law in laws:
                sid = str(law.get("source_id") or "Unknown")
                grouped.setdefault(sid, []).append(law)

            for sid, items in grouped.items():
                st.markdown(f"**{source_title(sid)}**")
                portal = source_portal_url(sid)
                if portal:
                    st.caption(f"Official portal: {portal}")

                for law in items:
                    st.markdown(
                        f'''
                        <div class="law-reference">
                            <div class="law-citation">{sid} • {law.get("citation","")}</div>
                            <div style="font-size:0.9rem;">{law.get("interpretation","")}</div>
                            <div style="font-size:0.8rem; color:#666; margin-top:0.25rem;">Confidence: {law.get("confidence","")}</div>
                        </div>
                        ''',
                        unsafe_allow_html=True,
                    )

    # --- Penalties (must be interpretable to non-lawyers) ---
    if penalties:
        with st.expander("💰 Penalties (what the cited sections imply)"):
            for p in penalties:
                law_name = p.get("law_name") or p.get("law") or ""
                section = p.get("section") or ""
                notes = p.get("notes") or p.get("summary") or ""
                min_bdt = _fmt_bdt(p.get("min_bdt") or p.get("fine_min_bdt"))
                max_bdt = _fmt_bdt(p.get("max_bdt") or p.get("fine_max_bdt"))
                penalty_type = p.get("penalty_type") or ""

                fine_text = None
                if min_bdt and max_bdt:
                    fine_text = f"Fine range: {min_bdt}–{max_bdt}"
                elif max_bdt:
                    fine_text = f"Fine up to: {max_bdt}"
                elif min_bdt:
                    fine_text = f"Fine from: {min_bdt}"

                lines = []
                if notes:
                    lines.append(str(notes))
                if fine_text:
                    lines.append(fine_text)
                if penalty_type:
                    lines.append(f"Penalty type: {penalty_type}")

                st.markdown(
                    f'''
                    <div class="penalty-box">
                        <div><strong>{law_name}</strong> — {section}</div>
                        <div style="margin-top:0.35rem; color:#444; font-size:0.9rem;">{"<br/>".join(lines) if lines else "—"}</div>
                    </div>
                    ''',
                    unsafe_allow_html=True,
                )

    # --- Recommended actions + contact links ---
    if actions:
        with st.expander("✅ Recommended actions"):
            for a in actions:
                st.markdown(f"- {a}")

                aid = _extract_authority_id(a)
                if aid:
                    info = _get_authority_info(aid)
                    if isinstance(info, dict) and info.get("authority_id"):
                        full_name = info.get("full_name") or aid
                        hotline = info.get("hotline")
                        website = info.get("website")

                        st.markdown(f"**Contact ({aid})**: {full_name}")
                        if hotline:
                            # tel: link works on mobile and some desktop apps
                            st.markdown(f"📞 Hotline: [{hotline}](tel:{hotline})")
                        if website:
                            st.markdown(f"🌐 Website: {website}")
                        st.markdown("---")
