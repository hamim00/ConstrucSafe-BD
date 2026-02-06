from __future__ import annotations

import streamlit as st

from utils.ui import load_css, sidebar
from utils.i18n import t

st.set_page_config(page_title="About • ConstrucSafe BD", page_icon="ℹ️", layout="wide")
load_css()
lang = sidebar()

# Page header
st.markdown(
    f"""
    <div class="page-header">
        <h1>ℹ️ {t("about_title", lang)}</h1>
        <div class="subtitle">{t("app_tagline", lang)}</div>
    </div>
    """,
    unsafe_allow_html=True,
)

bengali_cls = "bengali-text" if lang == "bn" else ""

st.markdown(
    f"""
    <div class="disclaimer-box {bengali_cls}">
        {t("about_disclaimer", lang)}
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown(f"### {t('about_notes_title', lang)}")
st.markdown(f"- {t('about_note_1', lang)}")
st.markdown(f"- {t('about_note_2', lang)}")
st.markdown(f"- {t('about_note_3', lang)}")
