from __future__ import annotations

from typing import Dict

# Minimal UI dictionary. Keep it small and extend as needed.
_STRINGS: Dict[str, Dict[str, str]] = {
    "en": {
        "app_title": "ConstrucSafe BD",
        "app_tagline": "AI-assisted construction safety analysis + legal references (R&D).",
        "nav_language": "Language",
        "nav_backend": "Backend",
        "nav_status": "Status",
        "analyze_title": "Analyze Construction Site Image",
        "upload_help": "Upload a JPG/JPEG/PNG (max 10MB).",
        "include_laws": "Include legal references",
        "mode": "Analysis mode",
        "mode_fast": "fast (lower cost)",
        "mode_accurate": "accurate (higher cost)",
        "analyze_btn": "Analyze image",
        "no_violations": "✅ No violations detected!",
        "need_upload": "📤 Upload an image to begin analysis",
        "click_analyze": "👆 Click \"Analyze image\" to start analysis",
        "browse_title": "Browse Laws by Violation Type",
        "search_title": "Search BNBC Clauses (Text Match)",
        "search_placeholder": "e.g., safety net, guardrail, scaffold, welding, excavation...",
        "search_btn": "Search",
        "about_title": "About",
        "about_disclaimer": "Educational / R&D use. Verify with qualified legal professionals before operational enforcement.",
    },
    "bn": {
        "app_title": "ConstrucSafe BD",
        "app_tagline": "এআই ভিত্তিক নির্মাণ সাইট নিরাপত্তা বিশ্লেষণ + আইনগত রেফারেন্স (R&D)।",
        "nav_language": "ভাষা",
        "nav_backend": "ব্যাকএন্ড",
        "nav_status": "স্ট্যাটাস",
        "analyze_title": "নির্মাণ সাইটের ছবি বিশ্লেষণ",
        "upload_help": "JPG/JPEG/PNG আপলোড করুন (সর্বোচ্চ ১০MB)।",
        "include_laws": "আইনগত রেফারেন্স দেখাও",
        "mode": "বিশ্লেষণ মোড",
        "mode_fast": "fast (কম খরচ)",
        "mode_accurate": "accurate (বেশি খরচ)",
        "analyze_btn": "বিশ্লেষণ শুরু",
        "no_violations": "✅ কোনো ভায়োলেশন পাওয়া যায়নি!",
        "need_upload": "📤 শুরু করতে একটি ছবি আপলোড করুন",
        "click_analyze": "👆 \"বিশ্লেষণ শুরু\" চাপুন",
        "browse_title": "ভায়োলেশন টাইপ অনুযায়ী আইন দেখুন",
        "search_title": "BNBC ক্লজ সার্চ (টেক্সট ম্যাচ)",
        "search_placeholder": "যেমন: safety net, guardrail, scaffold, welding, excavation...",
        "search_btn": "সার্চ",
        "about_title": "About",
        "about_disclaimer": "শুধুমাত্র শিক্ষামূলক / R&D ব্যবহারের জন্য। বাস্তব প্রয়োগের আগে যোগ্য আইন বিশেষজ্ঞের সাথে যাচাই করুন।",
    },
}

def t(key: str, lang: str = "en") -> str:
    lang = "bn" if lang.lower().startswith("bn") else "en"
    return _STRINGS.get(lang, _STRINGS["en"]).get(key, _STRINGS["en"].get(key, key))
