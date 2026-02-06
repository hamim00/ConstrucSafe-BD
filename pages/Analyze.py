from __future__ import annotations

import io
from typing import Optional, Tuple

import streamlit as st
from PIL import Image

from utils.ui import load_css, sidebar, get_api_client
from utils.i18n import t
from components.violation_card import render_violation_card
from components.flagged_item import render_flagged_item
from components.summary_metrics import render_summary_metrics
from utils.source_catalog import source_title

st.set_page_config(page_title="Analyze • ConstrucSafe BD", layout="wide")
load_css()
lang = sidebar()

# ── Page Header ──
st.markdown(
    f"""
    <div class="page-header">
        <h1>🔍 {t("analyze_title", lang)}</h1>
        <div class="subtitle">{t("analyze_subtitle", lang)}</div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ── Session state ──
if "uploaded_image_bytes" not in st.session_state:
    st.session_state.uploaded_image_bytes = None
if "uploaded_image_name" not in st.session_state:
    st.session_state.uploaded_image_name = None
if "analysis_result" not in st.session_state:
    st.session_state.analysis_result = None


def _resize_for_preview(img: Image.Image, max_w: int = 900, max_h: int = 450) -> Image.Image:
    """Resize large images for UI-friendly preview while preserving aspect ratio."""
    w, h = img.size
    scale = min(max_w / max(w, 1), max_h / max(h, 1), 1.0)
    if scale >= 1.0:
        return img
    new_size = (max(1, int(w * scale)), max(1, int(h * scale)))
    return img.resize(new_size, Image.Resampling.LANCZOS)


# ── Upload & Controls ──
left, right = st.columns([1, 2], gap="large")

with left:
    uploaded_file = st.file_uploader(
        "Upload image",
        type=["jpg", "jpeg", "png"],
        help=t("upload_help", lang),
        label_visibility="collapsed",
    )

    include_laws = st.toggle(t("include_laws", lang), value=True)
    mode = st.selectbox(
        t("mode", lang),
        options=["fast", "accurate"],
        index=0,
        format_func=lambda x: t(f"mode_{x}", lang),
    )

    show_full_image = st.checkbox(t("show_full_image", lang), value=False)

    analyze_clicked = st.button(
        t("analyze_btn", lang),
        type="primary",
        use_container_width=True,
    )

with right:
    if uploaded_file is not None:
        image_bytes = uploaded_file.read()
        st.session_state.uploaded_image_bytes = image_bytes
        st.session_state.uploaded_image_name = uploaded_file.name

        try:
            img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
            preview = _resize_for_preview(img)
            st.image(
                preview,
                caption=t("preview_caption", lang).format(name=uploaded_file.name),
                use_container_width=True,
            )

            if show_full_image:
                with st.expander("Full-size image", expanded=False):
                    st.image(img, caption=uploaded_file.name, use_container_width=True)
        except Exception:
            st.info("Preview unavailable for this file.")
    else:
        st.markdown(
            f"""<div class='empty-preview'>📷 {t("need_upload", lang)}</div>""",
            unsafe_allow_html=True,
        )

# ── Analyze ──
if analyze_clicked:
    if not st.session_state.uploaded_image_bytes:
        st.warning(t("need_upload", lang))
    else:
        client = get_api_client()
        with st.spinner(t("analyzing", lang)):
            result = client.analyze_image(
                st.session_state.uploaded_image_bytes,
                filename=st.session_state.uploaded_image_name or "image.jpg",
                include_laws=include_laws,
                mode=mode,
            )
        st.session_state.analysis_result = result

# ── Results ──
if st.session_state.analysis_result:
    result = st.session_state.analysis_result
    st.markdown("---")

    if not result.get("success", False):
        st.error(f"❌ Analysis failed: {result.get('error', 'Unknown error')}")
    else:
        # ── Summary metrics ──
        if result.get("ui_summary"):
            render_summary_metrics(result["ui_summary"], lang=lang)

        # ── Image quality warning ──
        quality = result.get("image_quality")
        if quality and quality != "good":
            st.warning(t("image_quality_warn", lang).format(q=quality))

        # ── Legal basis overview bar ──
        violations = result.get("violations", []) or []
        if violations:
            src_counts = {}
            for item in violations:
                for law in item.get("laws") or []:
                    sid = str(law.get("source_id") or "Unknown")
                    src_counts[sid] = src_counts.get(sid, 0) + 1

            if src_counts:
                chips = []
                for sid, cnt in sorted(src_counts.items(), key=lambda x: (-x[1], x[0]))[:8]:
                    chips.append(f'<span class="chip">{source_title(sid)} • {cnt}</span>')
                st.markdown(
                    f"""
                    <div class="legal-overview-bar">
                        <div class="lo-title">📜 {t("legal_overview", lang)}</div>
                        {"".join(chips)}
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

        # ── Detected Violations ──
        if violations:
            st.markdown(
                f"""
                <div class="section-header">
                    <span class="section-icon">🚨</span>
                    <h3>{t("detected_violations", lang)}</h3>
                    <span class="section-count">{len(violations)}</span>
                </div>
                """,
                unsafe_allow_html=True,
            )

            # Show top 3 violations directly
            TOP_N = 3
            top_violations = violations[:TOP_N]
            remaining_violations = violations[TOP_N:]

            for v in top_violations:
                render_violation_card(v, lang=lang)

            # Remaining violations in expander
            if remaining_violations:
                n_more = len(remaining_violations)
                with st.expander(
                    t("show_more_violations", lang).format(n=n_more),
                    expanded=False,
                ):
                    for v in remaining_violations:
                        render_violation_card(v, lang=lang)
        else:
            st.markdown(
                f"""
                <div class="no-violations-box">
                    <div class="nv-icon">✅</div>
                    <div class="nv-text">{t("no_violations", lang)}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        # ── Flagged for Review ──
        flagged = result.get("flagged_for_review", []) or []
        if flagged:
            st.markdown(
                f"""
                <div class="section-header">
                    <span class="section-icon">⚠️</span>
                    <h3>{t("flagged_for_review", lang)}</h3>
                    <span class="section-count">{len(flagged)}</span>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.caption(t("flagged_caption", lang))

            for f in flagged:
                render_flagged_item(f, lang=lang)

        # ── Disclaimer ──
        disclaimer_text = result.get("disclaimer", t("about_disclaimer", lang))
        bengali_cls = "bengali-text" if lang == "bn" else ""
        st.markdown(
            f"""
            <div class="disclaimer-box {bengali_cls}">
                {disclaimer_text}
            </div>
            """,
            unsafe_allow_html=True,
        )
else:
    # No result yet
    if st.session_state.uploaded_image_bytes:
        st.info(t("click_analyze", lang))
    else:
        st.info(t("need_upload", lang))
