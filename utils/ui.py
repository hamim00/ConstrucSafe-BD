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
    """Render sidebar and return current language code."""

    if "lang" not in st.session_state:
        st.session_state.lang = "en"

    lang = st.session_state.lang

    # Brand
    st.sidebar.markdown(
        """
        <div class="sidebar-brand">
            <h2>🏗️ ConstrucSafe BD</h2>
            <div class="tagline">AI Safety Compliance</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Navigation
    st.sidebar.page_link("pages/Analyze.py", label="🔍 " + t("analyze_title", lang)[:20])
    st.sidebar.page_link("pages/Browse_Laws.py", label="📚 " + t("browse_title", lang)[:25])
    st.sidebar.page_link("pages/Search_Laws.py", label="🔎 " + t("search_title", lang)[:25])
    st.sidebar.page_link("pages/About.py", label="ℹ️ " + t("about_title", lang)[:15])

    st.sidebar.markdown("---")

    # Settings
    st.sidebar.markdown(f"### ⚙️ {t('sidebar_settings', lang)}")

    lang_label = st.sidebar.radio(
        t("nav_language", lang),
        options=["English", "বাংলা"],
        index=0 if st.session_state.lang == "en" else 1,
        horizontal=True,
    )
    st.session_state.lang = "bn" if lang_label == "বাংলা" else "en"

    # Backend status
    st.sidebar.markdown("---")
    st.sidebar.markdown(f"**{t('nav_backend', st.session_state.lang)}**")
    client = get_api_client()
    try:
        h = client.health()
        version = h.get("version", "n/a")
        st.sidebar.success(f"{t('nav_status', st.session_state.lang)}: ✅ v{version}")
    except Exception:
        st.sidebar.error(f"{t('nav_status', st.session_state.lang)}: ❌ Unavailable")

    st.sidebar.markdown("---")
    st.sidebar.caption("ConstrucSafe BD • v2.0")

    return st.session_state.lang
