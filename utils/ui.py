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

    # ── Brand ──
    st.sidebar.markdown(
        """
        <div class="sidebar-brand">
            <h2>🏗️ ConstrucSafe BD</h2>
            <div class="tagline">AI Safety Compliance</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ── Navigation (replaces hidden default nav) ──
    st.sidebar.page_link("pages/Analyze.py", label="🔍 Analyze Image", use_container_width=True)
    st.sidebar.page_link("pages/Browse_Laws.py", label="📚 Browse Laws", use_container_width=True)
    st.sidebar.page_link("pages/Search_Laws.py", label="🔎 Search Clauses", use_container_width=True)
    st.sidebar.page_link("pages/About.py", label="ℹ️ About", use_container_width=True)

    st.sidebar.markdown("---")

    # ── Language ──
    st.sidebar.markdown(f"#### ⚙️ {t('sidebar_settings', lang)}")

    lang_label = st.sidebar.radio(
        t("nav_language", lang),
        options=["English", "বাংলা"],
        index=0 if st.session_state.lang == "en" else 1,
        horizontal=True,
    )
    st.session_state.lang = "bn" if lang_label == "বাংলা" else "en"

    # ── Backend status ──
    st.sidebar.markdown("---")
    client = get_api_client()
    try:
        h = client.health()
        version = h.get("version", "n/a")
        st.sidebar.success(f"Backend: ✅ v{version}")
    except Exception:
        st.sidebar.error("Backend: ❌ Unavailable")

    st.sidebar.caption("ConstrucSafe BD • v2.0")

    return st.session_state.lang
