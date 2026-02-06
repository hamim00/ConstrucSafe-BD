from __future__ import annotations

import streamlit as st

from utils.ui import load_css, sidebar
from utils.i18n import t

st.set_page_config(page_title="About • ConstrucSafe BD", page_icon="ℹ️", layout="wide")
load_css()
lang = sidebar()

st.title(t("about_title", lang))

st.markdown(
    f'''
    <div class="disclaimer-box {("bengali-text" if lang=="bn" else "")}">
        {t("about_disclaimer", lang)}
    </div>
    ''',
    unsafe_allow_html=True,
)

st.markdown("### Notes")
st.markdown("- Backend is deployed on Railway; the frontend calls it via HTTPS.")
st.markdown("- Analysis results depend on image quality and model behavior.")
st.markdown("- For operational enforcement, validate all legal interpretations with qualified professionals.")
