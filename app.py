from __future__ import annotations

import streamlit as st

# Main entry: send users directly to Analyze.
st.set_page_config(page_title="ConstrucSafe BD", layout="wide")

try:
    # Streamlit multipage navigation
    st.switch_page("pages/Analyze.py")
except Exception:
    # Fallback: render Analyze page inline if switch_page isn't available
    from pages.Analyze import *  # noqa: F401,F403
