from __future__ import annotations

import streamlit as st
from PIL import Image

from utils.ui import load_css, sidebar, get_api_client
from utils.i18n import t
from components.violation_card import render_violation_card
from components.flagged_item import render_flagged_item
from components.summary_metrics import render_summary_metrics

st.set_page_config(page_title="Analyze • ConstrucSafe BD", page_icon="🔍", layout="wide")
load_css()
lang = sidebar()

st.title(t("analyze_title", lang))

# session state
if "uploaded_image_bytes" not in st.session_state:
    st.session_state.uploaded_image_bytes = None
if "uploaded_image_name" not in st.session_state:
    st.session_state.uploaded_image_name = None
if "analysis_result" not in st.session_state:
    st.session_state.analysis_result = None

uploaded_file = st.file_uploader(
    "Upload image",
    type=["jpg", "jpeg", "png"],
    help=t("upload_help", lang),
)

if uploaded_file is not None:
    st.session_state.uploaded_image_bytes = uploaded_file.read()
    st.session_state.uploaded_image_name = uploaded_file.name

    try:
        img = Image.open(uploaded_file)
        st.image(img, caption=uploaded_file.name, use_container_width=True)
    except Exception:
        st.info("Preview unavailable for this file.")

    c1, c2, c3 = st.columns([1,1,1])
    with c1:
        include_laws = st.toggle(t("include_laws", lang), value=True)
    with c2:
        mode = st.selectbox(t("mode", lang), options=["fast", "accurate"], index=0, format_func=lambda x: t(f"mode_{x}", lang) if f"mode_{x}" in ["mode_fast","mode_accurate"] else x)
    with c3:
        analyze_clicked = st.button(t("analyze_btn", lang), type="primary", use_container_width=True)

    if analyze_clicked:
        client = get_api_client()
        with st.spinner("Analyzing..."):
            result = client.analyze_image(
                st.session_state.uploaded_image_bytes,
                filename=st.session_state.uploaded_image_name or "image.jpg",
                include_laws=include_laws,
                mode=mode,
            )
        st.session_state.analysis_result = result

    # display results
    if st.session_state.analysis_result:
        result = st.session_state.analysis_result
        if not result.get("success", False):
            st.error(f"❌ Analysis failed: {result.get('error', 'Unknown error')}")
        else:
            # Summary metrics (provided by backend as ui_summary)
            if result.get("ui_summary"):
                render_summary_metrics(result["ui_summary"])

            quality = result.get("image_quality")
            if quality and quality != "good":
                st.warning(f"⚠️ Image quality: {quality}. Results may be less accurate.")

            st.markdown("---")

            violations = result.get("violations", []) or []
            if violations:
                st.markdown(f"### Detected Violations ({len(violations)})")
                for v in violations:
                    render_violation_card(v)
            else:
                st.success(t("no_violations", lang))

            flagged = result.get("flagged_for_review", []) or []
            if flagged:
                st.markdown("---")
                st.markdown(f"### ⚠️ Flagged for Review ({len(flagged)})")
                st.caption("These items require human verification before action.")
                for f in flagged:
                    render_flagged_item(f)

            st.markdown(
                f'''
                <div class="disclaimer-box {("bengali-text" if lang=="bn" else "")}">
                    {result.get("disclaimer", t("about_disclaimer", lang))}
                </div>
                ''',
                unsafe_allow_html=True,
            )
    else:
        st.info(t("click_analyze", lang))
else:
    st.info(t("need_upload", lang))
