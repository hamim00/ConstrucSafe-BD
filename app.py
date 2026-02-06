from __future__ import annotations

import streamlit as st

from utils.ui import load_css, sidebar
from utils.i18n import t

st.set_page_config(
    page_title="ConstrucSafe BD",
    page_icon="🦺",
    layout="wide",
)

load_css()
lang = sidebar()

st.title(t("app_title", lang))
st.caption(t("app_tagline", lang))

st.markdown(
    f'''
    <div class="disclaimer-box {("bengali-text" if lang=="bn" else "")}">
        {t("about_disclaimer", lang)}
    </div>
    ''',
    unsafe_allow_html=True,
)

st.markdown("### What you can do")
st.markdown("- **Analyze** an image to detect violations and see laws/penalties.")
st.markdown("- **Browse Laws** by violation type (English/Bengali names, indicators, citations).")
st.markdown("- **Search Laws** by free text against BNBC clause keywords.")
