from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

import streamlit as st

from utils.source_catalog import source_title, source_portal_url
from utils.ui import get_api_client
from utils.i18n import t, t_severity, t_confidence

_SEV_COLORS = {
    "critical": "#C62828",
    "high": "#EF6C00",
    "medium": "#F9A825",
    "low": "#2E7D32",
}

_CONF_RANK = {"high": 3.0, "medium": 2.0, "low": 1.0}


def _sev_badge(sev: str, lang: str = "en") -> str:
    color = _SEV_COLORS.get(sev, "#1565C0")
    label = t_severity(sev, lang)
    return f'<span class="severity-badge" style="background:{color};">{label}</span>'


def _conf_badge(conf: str, lang: str = "en") -> str:
    label = t_confidence(conf, lang)
    return f'<span class="confidence-badge">{label}</span>'


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


def _fmt_months_years(p: Dict[str, Any]) -> Optional[str]:
    y = p.get("imprisonment_max_years")
    m = p.get("imprisonment_max_months")
    if y is not None:
        try:
            return f"কারাদণ্ড সর্বোচ্চ {int(y)} বছর" if False else f"Imprisonment up to {int(y)} year(s)"
        except Exception:
            pass
    if m is not None:
        try:
            return f"Imprisonment up to {int(m)} month(s)"
        except Exception:
            pass
    return None


def _penalty_quick_summary(penalties: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Extract a compact penalty summary across all penalty profiles."""
    max_fine = 0
    max_imprison_months = 0
    max_imprison_years = 0
    laws_set = set()

    for p in penalties:
        law_name = p.get("law_name") or p.get("law") or ""
        section = p.get("section") or ""
        if law_name and section:
            laws_set.add(f"{section}")

        for key in ["max_bdt", "fine_max_bdt"]:
            val = p.get(key)
            if val is not None:
                try:
                    max_fine = max(max_fine, int(val))
                except Exception:
                    pass

        first = p.get("first_offense") if isinstance(p.get("first_offense"), dict) else {}
        sub = p.get("subsequent_offense") if isinstance(p.get("subsequent_offense"), dict) else {}

        for obj in [first, sub, p]:
            fmax = obj.get("fine_max_bdt")
            if fmax:
                try:
                    max_fine = max(max_fine, int(fmax))
                except Exception:
                    pass
            im = obj.get("imprisonment_max_months")
            if im:
                try:
                    max_imprison_months = max(max_imprison_months, int(im))
                except Exception:
                    pass
            iy = obj.get("imprisonment_max_years")
            if iy:
                try:
                    max_imprison_years = max(max_imprison_years, int(iy))
                except Exception:
                    pass

    return {
        "max_fine": max_fine,
        "max_imprison_months": max_imprison_months,
        "max_imprison_years": max_imprison_years,
        "sections": sorted(laws_set),
    }


def _penalty_lines(p: Dict[str, Any]) -> List[str]:
    lines: List[str] = []

    summary = p.get("notes") or p.get("summary") or ""
    if summary:
        lines.append(str(summary))

    min_bdt = _fmt_bdt(p.get("min_bdt") or p.get("fine_min_bdt"))
    max_bdt = _fmt_bdt(p.get("max_bdt") or p.get("fine_max_bdt"))

    if min_bdt and max_bdt:
        lines.append(f"Fine range: {min_bdt}–{max_bdt}")
    elif max_bdt:
        lines.append(f"Fine up to: {max_bdt}")
    elif min_bdt:
        lines.append(f"Fine from: {min_bdt}")

    imprison = _fmt_months_years(p)
    if imprison:
        lines.append(imprison)

    first = p.get("first_offense")
    if isinstance(first, dict):
        f_fine = _fmt_bdt(first.get("fine_max_bdt"))
        f_months = first.get("imprisonment_max_months")
        parts = []
        if f_fine:
            parts.append(f"fine up to {f_fine}")
        if f_months is not None:
            try:
                parts.append(f"imprisonment up to {int(f_months)} month(s)")
            except Exception:
                pass
        if parts:
            lines.append("First offence: " + "; ".join(parts))

    sub = p.get("subsequent_offense")
    if isinstance(sub, dict):
        s_fine = _fmt_bdt(sub.get("fine_max_bdt"))
        s_months = sub.get("imprisonment_max_months")
        parts = []
        if s_fine:
            parts.append(f"fine up to {s_fine}")
        if s_months is not None:
            try:
                parts.append(f"imprisonment up to {int(s_months)} month(s)")
            except Exception:
                pass
        if parts:
            lines.append("Subsequent offence: " + "; ".join(parts))

    add_day = p.get("additional_per_day_bdt")
    if add_day is not None:
        add_day_fmt = _fmt_bdt(add_day)
        if add_day_fmt:
            lines.append(f"Additional per day (continuing offence): {add_day_fmt}")

    other = p.get("other")
    if other:
        lines.append(str(other))

    if p.get("or_both") is True:
        lines.append("May apply as imprisonment and/or fine (court discretion).")

    ptype = p.get("penalty_type")
    if ptype:
        lines.append(f"Penalty type: {ptype}")

    seen = set()
    out = []
    for x in lines:
        if x and x not in seen:
            out.append(x)
            seen.add(x)
    return out


def render_violation_card(violation_data: Dict[str, Any], lang: str = "en"):
    """Render a single violation card with compact, professional design."""

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

    # Use display-friendly name
    display_name = vtype.replace("_", " ").title()

    loc_label = t("location", lang)
    affected_label = t("affected", lang)

    # ── Main card ──
    st.markdown(
        f'''
        <div class="violation-card sev-{sev}">
            <div class="v-header">
                <h4 class="v-title">{display_name}</h4>
                <div class="badges-row">
                    {_sev_badge(sev, lang)}
                    {_conf_badge(conf, lang)}
                </div>
            </div>
            <p class="v-desc">{desc}</p>
            <div class="v-meta">
                <span><strong>{loc_label}:</strong> {loc or "N/A"}</span>
                <span><strong>{affected_label}:</strong> {", ".join(parties) if parties else "N/A"}</span>
            </div>
        </div>
        ''',
        unsafe_allow_html=True,
    )

    # ── Inline penalty summary (compact, always visible) ──
    if penalties:
        ps = _penalty_quick_summary(penalties)
        items = []
        if ps["max_fine"] > 0:
            items.append(f'<span class="ps-item">💰 Fine up to ৳{ps["max_fine"]:,}</span>')
        if ps["max_imprison_years"] > 0:
            items.append(f'<span class="ps-item">⚖️ Up to {ps["max_imprison_years"]} year(s)</span>')
        elif ps["max_imprison_months"] > 0:
            items.append(f'<span class="ps-item">⚖️ Up to {ps["max_imprison_months"]} month(s)</span>')
        if ps["sections"]:
            items.append(f'<span class="ps-item">📜 {", ".join(ps["sections"][:3])}</span>')

        if items:
            st.markdown(
                f'''<div class="penalty-summary">
                    <span class="ps-label">Penalty:</span>
                    {"".join(items)}
                </div>''',
                unsafe_allow_html=True,
            )

    # ── Key legal basis (compact) ──
    primary = _pick_primary_law(laws) if isinstance(laws, list) else None
    if primary:
        sid = primary.get("source_id") or "Unknown"
        title = source_title(str(sid))
        portal = source_portal_url(str(sid))
        citation = primary.get("citation") or ""
        interp = primary.get("interpretation") or ""
        conf_val = primary.get("confidence") or ""

        portal_html = f' • <a href="{portal}" target="_blank">official portal</a>' if portal else ""
        basis_label = t("key_legal_basis", lang)
        st.markdown(
            f'''
            <div class="law-highlight">
              <div class="law-source-title">{basis_label}: {title}{portal_html}</div>
              <div class="law-meta"><strong>Citation:</strong> {citation}</div>
              <div class="law-meta"><strong>Why this matches:</strong> {interp[:200]}{"…" if len(interp) > 200 else ""}</div>
              <div class="law-meta" style="opacity:0.7;"><strong>{t("confidence_label", lang)}:</strong> {conf_val}</div>
            </div>
            ''',
            unsafe_allow_html=True,
        )

    # ── Expandable: Legal references ──
    if laws:
        grouped: Dict[str, List[Dict[str, Any]]] = {}
        for law in laws:
            sid = str(law.get("source_id") or "Unknown")
            grouped.setdefault(sid, []).append(law)

        # Compact chips
        chips = []
        for sid, items in sorted(grouped.items(), key=lambda kv: (-len(kv[1]), kv[0]))[:10]:
            chips.append(f'<span class="chip">{source_title(sid)} • {len(items)}</span>')
        st.markdown("".join(chips), unsafe_allow_html=True)

        with st.expander(f"📚 {t('legal_refs', lang)}", expanded=False):
            sids = [sid for sid, _ in sorted(grouped.items(), key=lambda kv: (-len(kv[1]), kv[0]))]
            default_sid = str(primary.get("source_id")) if primary and primary.get("source_id") in grouped else sids[0]
            selected = st.selectbox(
                "Select law source",
                options=sids,
                index=sids.index(default_sid) if default_sid in sids else 0,
                format_func=lambda x: f"{source_title(x)} ({len(grouped.get(x, []))})",
                key=f"lawsrc_{vtype}",
            )
            show_full = st.checkbox("Show full interpretations", value=False, key=f"full_interp_{vtype}")
            show_excerpts = st.checkbox("Show text excerpts (if available)", value=False, key=f"show_excerpt_{vtype}")

            portal = source_portal_url(selected)
            if portal:
                st.markdown(f"[Open official portal]({portal})")

            rows = []
            for it in grouped.get(selected, []):
                interp = it.get("interpretation") or ""
                if not show_full and isinstance(interp, str) and len(interp) > 160:
                    interp = interp[:160] + "…"
                rows.append(
                    {
                        "Citation": it.get("citation") or "",
                        "Confidence": it.get("confidence") or "",
                        "Interpretation": interp,
                    }
                )

            st.dataframe(rows, use_container_width=True, height=200)

            if show_excerpts:
                for it in grouped.get(selected, []):
                    excerpt = it.get("relevant_text_excerpt")
                    if excerpt:
                        cit = it.get("citation") or "excerpt"
                        with st.expander(f"Excerpt • {cit}", expanded=False):
                            st.code(str(excerpt)[:2000])

    # ── Expandable: Full penalty details ──
    if penalties:
        with st.expander(f"💰 {t('penalties', lang)} — {t('penalty_note', lang)[:80]}…", expanded=False):
            st.caption(t("penalty_note", lang))

            seen = set()
            for p in penalties:
                law_name = p.get("law_name") or p.get("law") or ""
                section = p.get("section") or ""
                key = (law_name, section)
                if key in seen:
                    continue
                seen.add(key)
                lines = _penalty_lines(p)

                st.markdown(
                    f'''
                    <div class="penalty-box">
                        <strong>{law_name}</strong> — {section}
                        <div class="penalty-details">
                            {"<br/>".join(lines) if lines else "—"}
                        </div>
                    </div>
                    ''',
                    unsafe_allow_html=True,
                )

    # ── Expandable: Recommended actions ──
    if actions:
        with st.expander(f"✅ {t('recommended_actions', lang)}", expanded=False):
            for a in actions:
                st.markdown(f"- {a}")

                aid = _extract_authority_id(a)
                if aid:
                    info = _get_authority_info(aid)
                    if isinstance(info, dict) and info.get("authority_id"):
                        full_name = info.get("full_name") or aid
                        hotline = info.get("hotline")
                        website = info.get("website")
                        email = info.get("email")

                        st.markdown(f"**Contact ({aid})**: {full_name}")
                        if hotline:
                            st.markdown(f"📞 Hotline: [{hotline}](tel:{hotline})")
                        if email:
                            st.markdown(f"✉️ Email: [{email}](mailto:{email})")
                        if website:
                            st.markdown(f"🌐 Website: {website}")

    # Separator between cards
    st.markdown("<div style='margin-bottom:0.5rem;'></div>", unsafe_allow_html=True)
