from __future__ import annotations

import streamlit as st

from utils.ui import load_css, sidebar, get_api_client
from utils.i18n import t

st.set_page_config(page_title="Browse Laws • ConstrucSafe BD", page_icon="📚", layout="wide")
load_css()
lang = sidebar()

st.title(t("browse_title", lang))

client = get_api_client()

@st.cache_data(show_spinner=False, ttl=3600)
def _cached_list_violations():
    return client.list_violations()

violations = []
try:
    violations = _cached_list_violations()
except Exception as e:
    st.error(f"Could not load violations list: {e}")

if violations:
    vid = st.selectbox("Violation type", options=sorted(violations))
    if vid:
        with st.spinner("Loading details..."):
            try:
                details = client.get_violation_details(vid)
            except Exception as e:
                st.error(f"Could not load details: {e}")
                details = None

        if details:
            col1, col2 = st.columns([1, 1])
            with col1:
                st.markdown(f"**English:** {details.get('display_name_en', vid)}")
                st.markdown(f"**Bengali:** <span class='bengali-text'>{details.get('display_name_bn', '')}</span>", unsafe_allow_html=True)
                st.markdown(f"**Category:** {details.get('category', 'N/A')}")
                st.markdown(f"**Severity:** {details.get('severity', 'N/A')}")
                st.markdown(f"**Affected:** {', '.join(details.get('affected_parties', [])) or 'N/A'}")
            with col2:
                st.markdown("**Visual indicators:**")
                for ind in details.get("visual_indicators", []) or []:
                    st.markdown(f"- {ind}")

            # primary authority
            enf = details.get("enforcement", {}) or {}
            aid = enf.get("primary_authority")
            if aid:
                st.markdown("---")
                st.markdown("### Enforcement authority")
                try:
                    a = client.get_authority(aid)
                    st.markdown(f"**{a.get('full_name','')}** ({a.get('authority_id','')})")
                    if a.get("full_name_bn"):
                        st.markdown(f"<div class='bengali-text'>{a.get('full_name_bn')}</div>", unsafe_allow_html=True)
                    st.markdown(f"**Jurisdiction:** {a.get('jurisdiction','')}")
                    if a.get("hotline"):
                        st.markdown(f"**Hotline:** {a.get('hotline')}")
                    if a.get("website"):
                        st.markdown(f"**Website:** {a.get('website')}")
                except Exception:
                    st.info("Authority info not available.")

            # legal references
            refs = details.get("legal_references", []) or []
            if refs:
                st.markdown("---")
                st.markdown("### Legal references")
                for ref in refs[:10]:
                    st.markdown(
                        f'''
                        <div class="law-reference">
                            <div class="law-citation">{ref.get("source_id","")} • {ref.get("citation","")}</div>
                            <div style="font-size:0.9rem;">{ref.get("interpretation","")}</div>
                            <div style="font-size:0.8rem; color:#666; margin-top:0.25rem;">Confidence: {ref.get("confidence","")}</div>
                        </div>
                        ''',
                        unsafe_allow_html=True,
                    )
        else:
            st.warning("No details found.")
else:
    st.info("No violations loaded.")
