from __future__ import annotations

from typing import Dict

_STRINGS: Dict[str, Dict[str, str]] = {
    "en": {
        "app_title": "ConstrucSafe BD",
        "app_tagline": "AI-powered construction safety analysis with legal references.",
        "nav_language": "Language",
        "nav_backend": "Backend",
        "nav_status": "Status",
        "analyze_title": "Analyze Construction Site Image",
        "analyze_subtitle": "Upload a photo to detect safety violations and get legal references under Bangladesh law.",
        "upload_help": "Upload a JPG/JPEG/PNG (max 10 MB).",
        "include_laws": "Include legal references",
        "mode": "Analysis mode",
        "mode_fast": "Fast (lower cost)",
        "mode_accurate": "Accurate (higher cost)",
        "analyze_btn": "Analyze Image",
        "no_violations": "No safety violations detected — site appears compliant.",
        "need_upload": "Upload an image to begin analysis.",
        "click_analyze": "Click \"Analyze Image\" to start.",
        "browse_title": "Browse Laws by Violation Type",
        "search_title": "Search BNBC Clauses",
        "search_placeholder": "e.g., safety net, guardrail, scaffold, welding, excavation...",
        "search_btn": "Search",
        "about_title": "About ConstrucSafe BD",
        "about_disclaimer": "Educational / R&D use only. Verify all findings with qualified safety professionals and legal advisors before operational enforcement.",
        "detected_violations": "Detected Violations",
        "flagged_for_review": "Flagged for Review",
        "flagged_caption": "These items need human verification before action.",
        "legal_overview": "Legal Basis Overview",
        "show_more_violations": "Show {n} more violation(s)",
        "show_less": "Show less",
        "key_legal_basis": "Key legal basis",
        "legal_refs": "Legal references (grouped)",
        "penalties": "Penalties",
        "penalty_note": "Note: Many safety violations map to general penalty provisions under the Bangladesh Labour Act. Exact applicability depends on specific facts and enforcement authority.",
        "recommended_actions": "Recommended actions",
        "image_quality_warn": "Image quality: {q}. Results may be less accurate.",
        "total": "Total",
        "high": "High",
        "medium": "Medium",
        "low": "Low",
        "review": "Review",
        "show_full_image": "Show full-size image (can be large)",
        "preview_caption": "Preview: {name}",
        "analyzing": "Analyzing image…",
        "location": "Location",
        "affected": "Affected",
        "confidence_label": "Confidence",
        "why_flagged": "Why flagged",
        "sidebar_settings": "Settings",
    },
    "bn": {
        "app_title": "ConstrucSafe BD",
        "app_tagline": "এআই-চালিত নির্মাণ সাইট নিরাপত্তা বিশ্লেষণ ও আইনগত রেফারেন্স।",
        "nav_language": "ভাষা",
        "nav_backend": "ব্যাকএন্ড",
        "nav_status": "অবস্থা",
        "analyze_title": "নির্মাণ সাইটের ছবি বিশ্লেষণ",
        "analyze_subtitle": "নিরাপত্তা লঙ্ঘন শনাক্ত করতে এবং বাংলাদেশের আইনের অধীনে আইনি রেফারেন্স পেতে একটি ছবি আপলোড করুন।",
        "upload_help": "JPG/JPEG/PNG আপলোড করুন (সর্বোচ্চ ১০ MB)।",
        "include_laws": "আইনি রেফারেন্স অন্তর্ভুক্ত করুন",
        "mode": "বিশ্লেষণ মোড",
        "mode_fast": "দ্রুত (কম খরচ)",
        "mode_accurate": "নির্ভুল (বেশি খরচ)",
        "analyze_btn": "ছবি বিশ্লেষণ করুন",
        "no_violations": "কোনো নিরাপত্তা লঙ্ঘন শনাক্ত হয়নি — সাইট মানসম্মত।",
        "need_upload": "বিশ্লেষণ শুরু করতে একটি ছবি আপলোড করুন।",
        "click_analyze": "\"ছবি বিশ্লেষণ করুন\" বোতামে ক্লিক করুন।",
        "browse_title": "লঙ্ঘনের ধরন অনুযায়ী আইন দেখুন",
        "search_title": "BNBC ধারা অনুসন্ধান",
        "search_placeholder": "যেমন: safety net, guardrail, scaffold, welding, excavation...",
        "search_btn": "অনুসন্ধান",
        "about_title": "ConstrucSafe BD সম্পর্কে",
        "about_disclaimer": "শুধুমাত্র শিক্ষামূলক / গবেষণা ব্যবহারের জন্য। কার্যকরী প্রয়োগের আগে যোগ্য নিরাপত্তা বিশেষজ্ঞ ও আইন পরামর্শকের সাথে সমস্ত ফলাফল যাচাই করুন।",
        "detected_violations": "শনাক্তকৃত লঙ্ঘন",
        "flagged_for_review": "পর্যালোচনার জন্য চিহ্নিত",
        "flagged_caption": "এই বিষয়গুলো পদক্ষেপ নেওয়ার আগে মানব যাচাই প্রয়োজন।",
        "legal_overview": "আইনি ভিত্তি সারসংক্ষেপ",
        "show_more_violations": "আরো {n}টি লঙ্ঘন দেখুন",
        "show_less": "কম দেখুন",
        "key_legal_basis": "প্রধান আইনি ভিত্তি",
        "legal_refs": "আইনি রেফারেন্স (গোষ্ঠীবদ্ধ)",
        "penalties": "জরিমানা ও শাস্তি",
        "penalty_note": "দ্রষ্টব্য: অনেক নিরাপত্তা লঙ্ঘন বাংলাদেশ শ্রম আইনের সাধারণ শাস্তি বিধানের অধীনে আসে। সঠিক প্রযোজ্যতা নির্দিষ্ট তথ্য এবং প্রয়োগকারী কর্তৃপক্ষের উপর নির্ভর করে।",
        "recommended_actions": "সুপারিশকৃত পদক্ষেপ",
        "image_quality_warn": "ছবির মান: {q}। ফলাফল কম নির্ভুল হতে পারে।",
        "total": "মোট",
        "high": "উচ্চ",
        "medium": "মাঝারি",
        "low": "নিম্ন",
        "review": "পর্যালোচনা",
        "show_full_image": "পূর্ণ আকারের ছবি দেখুন (বড় হতে পারে)",
        "preview_caption": "প্রিভিউ: {name}",
        "analyzing": "ছবি বিশ্লেষণ হচ্ছে…",
        "location": "অবস্থান",
        "affected": "প্রভাবিত",
        "confidence_label": "আস্থা",
        "why_flagged": "কেন চিহ্নিত",
        "sidebar_settings": "সেটিংস",
    },
}

_SEVERITY_BN = {"critical": "গুরুতর", "high": "উচ্চ", "medium": "মাঝারি", "low": "নিম্ন"}
_CONFIDENCE_BN = {"high": "উচ্চ", "medium": "মাঝারি", "low": "নিম্ন"}


def t(key: str, lang: str = "en") -> str:
    lang = "bn" if lang.lower().startswith("bn") else "en"
    return _STRINGS.get(lang, _STRINGS["en"]).get(key, _STRINGS["en"].get(key, key))


def t_severity(severity: str, lang: str = "en") -> str:
    if lang.startswith("bn"):
        return _SEVERITY_BN.get(severity.lower(), severity)
    return severity.upper()


def t_confidence(confidence: str, lang: str = "en") -> str:
    if lang.startswith("bn"):
        return _CONFIDENCE_BN.get(confidence.lower(), confidence)
    return confidence.upper()
