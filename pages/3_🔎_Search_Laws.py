from __future__ import annotations

import streamlit as st
import pandas as pd

from utils.ui import load_css, sidebar, get_api_client
from utils.i18n import t

st.set_page_config(page_title="Search Laws • ConstrucSafe BD", page_icon="🔎", layout="wide")
load_css()
lang = sidebar()

st.title(t("search_title", lang))
client = get_api_client()

q = st.text_input("Query", placeholder=t("search_placeholder", lang))
top_k = st.slider("Top K", min_value=1, max_value=20, value=5)

if st.button(t("search_btn", lang), type="primary"):
    if not q.strip():
        st.warning("Enter a query.")
    else:
        with st.spinner("Searching..."):
            try:
                res = client.match_text(q.strip(), top_k=top_k)
            except Exception as e:
                st.error(f"Search failed: {e}")
                res = None

        if res:
            matches = res.get("matches", []) or []
            if not matches:
                st.info("No matches found.")
            else:
                df = pd.DataFrame(matches)
                # order columns for readability
                cols = [c for c in ["score","violation_id","citation","section","title","pdf_page","gazette_page","clause_id","source_catalog_id","confidence"] if c in df.columns]
                st.dataframe(df[cols] if cols else df, use_container_width=True)

                st.caption("Tip: pick a violation_id above and open it in **Browse Laws** to see full details.")
