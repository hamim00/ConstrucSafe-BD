from __future__ import annotations

import streamlit as st
from pathlib import Path

from utils.api_client import ConstructSafeAPIClient
from utils.i18n import t


def load_css():
    css_path = Path(__file__).resolve().parents[1] / "assets" / "style.css"
    if css_path.exists():
        st.markdown(f"<style>{css_path.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)


@st.cache_resource
def get_api_client() -> ConstructSafeAPIClient:
    return ConstructSafeAPIClient()


def sidebar() -> str:
    # language
    if "lang" not in st.session_state:
        st.session_state.lang = "en"

    st.sidebar.markdown("### ⚙️ Settings")
    lang_label = st.sidebar.radio(
        t("nav_language", st.session_state.lang),
        options=["English", "বাংলা"],
        index=0 if st.session_state.lang == "en" else 1,
    )
    st.session_state.lang = "bn" if lang_label == "বাংলা" else "en"

    # backend status
    st.sidebar.markdown("---")
    st.sidebar.markdown(f"**{t('nav_backend', st.session_state.lang)}**")
    client = get_api_client()
    try:
        h = client.health()
        st.sidebar.success(f"{t('nav_status', st.session_state.lang)}: {h.get('status', 'ok')} (v{h.get('version', 'n/a')})")
    except Exception:
        st.sidebar.warning(f"{t('nav_status', st.session_state.lang)}: unavailable")

    st.sidebar.markdown("---")
    st.sidebar.caption("ConstrucSafe BD • Streamlit Frontend")

    return st.session_state.lang
