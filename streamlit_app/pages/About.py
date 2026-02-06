from __future__ import annotations

import streamlit as st

from utils.ui import load_css, sidebar
from utils.i18n import t

st.set_page_config(page_title="About • ConstrucSafe BD", page_icon="ℹ️", layout="wide")
load_css()
lang = sidebar()

# ── Page Header ──
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

# ── Content ──
if lang == "bn":
    # ──────────────── BENGALI VERSION ────────────────
    st.markdown(
        f"""
        <div class="{bengali_cls}">

### ConstrucSafe BD কী?

ConstrucSafe BD একটি AI-চালিত নির্মাণ সাইট নিরাপত্তা বিশ্লেষণ টুল যা বাংলাদেশের নির্মাণ শিল্পের জন্য বিশেষভাবে তৈরি করা হয়েছে। এই অ্যাপ্লিকেশনটি নির্মাণ সাইটের ছবি বিশ্লেষণ করে নিরাপত্তা লঙ্ঘন শনাক্ত করে এবং সরাসরি বাংলাদেশের আইনের সাথে সংযুক্ত করে।

---

### এটি কীভাবে কাজ করে?

**ধাপ ১: ছবি আপলোড করুন**
নির্মাণ সাইটের একটি পরিষ্কার ছবি তুলুন এবং "Analyze Image" পেজে আপলোড করুন।

**ধাপ ২: AI বিশ্লেষণ**
আমাদের AI মডেল (GPT-4 Vision) ছবিটি বিশ্লেষণ করে এবং নিম্নলিখিত বিষয়গুলো শনাক্ত করে:
- PPE (ব্যক্তিগত সুরক্ষা সরঞ্জাম) অনুপস্থিতি — হেলমেট, জুতা, হাতমোজা, ভেস্ট ইত্যাদি
- পতন সুরক্ষা সমস্যা — গার্ডরেইল, হার্নেস, সেফটি নেট
- খননকার্যের ঝুঁকি — ব্যারিকেড, শোরিং, সাইনেজ
- ভারা (স্ক্যাফোল্ডিং) নিরাপত্তা সমস্যা
- বৈদ্যুতিক ও অগ্নি ঝুঁকি
- সাইট সীমানা ও জনসাধারণের নিরাপত্তা

**ধাপ ৩: আইনি রেফারেন্স**
প্রতিটি শনাক্তকৃত লঙ্ঘনের জন্য, অ্যাপটি স্বয়ংক্রিয়ভাবে প্রাসঙ্গিক আইন, জরিমানা এবং শাস্তির তথ্য দেখায়।

---

### কোন আইনগুলো ব্যবহার করা হয়?

এই অ্যাপ্লিকেশনে নিম্নলিখিত আইন ও বিধিমালা অন্তর্ভুক্ত:

| আইন | বিবরণ |
|------|--------|
| বাংলাদেশ শ্রম আইন, ২০০৬ | শ্রমিক নিরাপত্তা ও স্বাস্থ্য সংক্রান্ত মূল আইন |
| বাংলাদেশ শ্রম বিধিমালা, ২০১৫ | শ্রম আইনের বিস্তারিত নিয়মাবলী |
| BNBC ২০২০ | বাংলাদেশ জাতীয় বিল্ডিং কোড |
| DIFE নির্দেশিকা | কলকারখানা পরিদর্শন অধিদপ্তরের নির্দেশনা |
| ঢাকা মেট্রোপলিটন পুলিশ অধ্যাদেশ, ১৯৭৬ | জনসাধারণের স্থানে বাধা সংক্রান্ত |
| পরিবেশ সংরক্ষণ আইন, ১৯৯৫ | পরিবেশ দূষণ সংক্রান্ত |

---

### জরিমানা ও শাস্তি কীভাবে নির্ধারিত হয়?

বাংলাদেশ শ্রম আইন ২০০৬-এ নির্মাণ নিরাপত্তা লঙ্ঘনের জন্য প্রধানত দুটি শাস্তি ধারা প্রযোজ্য:

- **ধারা ৩০৭** — সাধারণ শাস্তি: প্রথম অপরাধে সর্বোচ্চ ৳২৫,০০০ জরিমানা ও ৩ মাস কারাদণ্ড
- **ধারা ৩০৯** — গুরুতর আঘাত/মৃত্যুর ঝুঁকি থাকলে: সর্বোচ্চ ৳১,০০,০০০ জরিমানা ও ২ বছর কারাদণ্ড

এছাড়াও BNBC ২০২০-এর নির্দিষ্ট ধারাগুলো প্রতিটি লঙ্ঘনের জন্য আলাদাভাবে প্রযোজ্য।

---

### কারা এটি ব্যবহার করতে পারেন?

- নির্মাণ কোম্পানির নিরাপত্তা কর্মকর্তা
- DIFE পরিদর্শক
- প্রকল্প ব্যবস্থাপক
- আইনজীবী ও পরামর্শক
- গবেষক ও শিক্ষার্থী

---

### গুরুত্বপূর্ণ সতর্কতা

</div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown(
        f"""<div class="disclaimer-box {bengali_cls}">
⚠️ এই টুলটি শুধুমাত্র শিক্ষামূলক ও গবেষণা উদ্দেশ্যে। AI-এর ফলাফল চূড়ান্ত নয়। যেকোনো আইনি পদক্ষেপ নেওয়ার আগে অবশ্যই যোগ্য নিরাপত্তা বিশেষজ্ঞ এবং আইন পরামর্শকের সাথে পরামর্শ করুন। "Flagged for Review" বিভাগের আইটেমগুলো AI-এর অনুমান মাত্র — মানব যাচাই ছাড়া এগুলো নিশ্চিত নয়।
</div>""",
        unsafe_allow_html=True,
    )

    st.markdown(
        f"""
<div class="{bengali_cls}">

---

### যোগাযোগ ও সহায়তা

| সংস্থা | যোগাযোগ |
|--------|---------|
| DIFE (কলকারখানা পরিদর্শন অধিদপ্তর) | হটলাইন: 16357 · ওয়েবসাইট: dife.gov.bd |
| জাতীয় জরুরি সেবা | 999 |
| নাগরিক সেবা | 333 |

</div>
        """,
        unsafe_allow_html=True,
    )

else:
    # ──────────────── ENGLISH VERSION ────────────────
    st.markdown(
        """
### What is ConstrucSafe BD?

ConstrucSafe BD is an AI-powered construction site safety analysis tool built specifically for the Bangladesh construction industry. It analyzes photos of construction sites to detect safety violations and automatically maps them to relevant Bangladeshi laws, penalties, and enforcement authorities.

---

### How Does It Work?

**Step 1: Upload a Photo**
Take a clear photograph of a construction site and upload it on the "Analyze Image" page. The clearer the photo, the better the results.

**Step 2: AI Analysis**
Our AI model (GPT-4 Vision) examines the image and identifies safety violations such as:
- **Missing PPE** — helmets, safety shoes, gloves, high-visibility vests, eye/ear protection
- **Fall protection issues** — missing guardrails, harnesses, safety nets
- **Excavation hazards** — no barricades, shoring, or signage
- **Scaffolding problems** — unsafe bracing, missing toeboards, overloading
- **Electrical & fire risks** — exposed wiring, missing fire extinguishers
- **Site boundary issues** — no fencing, public obstruction, missing warning signs

**Step 3: Legal Mapping**
For each detected violation, the app automatically shows the relevant laws, fine amounts, imprisonment terms, and which authority to contact.

---

### What Laws Are Covered?

The system references the following legal sources:

| Law / Regulation | Coverage |
|---|---|
| Bangladesh Labour Act, 2006 (with 2018 amendments) | Primary worker safety and health law |
| Bangladesh Labour Rules, 2015 | Detailed implementation rules for the Labour Act |
| Bangladesh National Building Code (BNBC) 2020 | Technical construction safety standards |
| DIFE Inspection Guidelines & Checklists | Practical inspection criteria |
| Dhaka Metropolitan Police Ordinance, 1976 | Public place obstruction by construction materials |
| Bangladesh Environment Conservation Act, 1995 | Environmental pollution from construction |

---

### Understanding Penalties

Most construction safety violations in Bangladesh fall under two main penalty provisions of the Bangladesh Labour Act 2006:

- **Section 307 (General Penalty)** — For offences where no specific penalty is provided: first offence fine up to ৳25,000 with up to 3 months imprisonment; subsequent offences up to ৳50,000 with up to 6 months
- **Section 309 (Dangerous Violations)** — When the violation is likely to cause serious injury or death: fine up to ৳100,000 with up to 2 years imprisonment

Additionally, specific BNBC 2020 clauses apply to each type of violation with their own technical requirements.

> **Why do many violations show the same penalty sections?** This is how Bangladesh law works — Sections 307 and 309 are "catch-all" provisions that cover most labour safety offences. The BNBC clause references (shown under each violation) are what make each case unique and specific.

---

### Who Can Use This?

- Construction company safety officers
- DIFE (Department of Inspection for Factories and Establishments) inspectors
- Project managers and site engineers
- Lawyers and legal consultants
- Researchers, students, and academics

---

### Analysis Modes

| Mode | Speed | Cost | Violations Detected |
|---|---|---|---|
| **Fast** | ~5 seconds | Lower | Up to 6 |
| **Accurate** | ~15 seconds | Higher | Up to 12 |

For quick site checks, use Fast mode. For thorough inspections or documentation, use Accurate mode.

---

### Important Limitations
        """
    )

    st.markdown(
        """<div class="disclaimer-box">
⚠️ <strong>This tool is for educational and research purposes only.</strong> AI analysis results are not definitive legal findings. Always verify all violations, legal interpretations, and penalty information with qualified safety professionals and legal advisors before taking any enforcement action. Items under "Flagged for Review" are AI hypotheses that require human verification — they are not confirmed violations.
</div>""",
        unsafe_allow_html=True,
    )

    st.markdown(
        """
---

### Key Contacts

| Authority | Contact |
|---|---|
| DIFE (Dept. of Inspection for Factories & Establishments) | Hotline: **16357** · Website: [dife.gov.bd](http://dife.gov.bd) |
| National Emergency Service | **999** |
| Citizen Service | **333** |

---

### Technical Notes

- The backend API is deployed on Railway and communicates over HTTPS
- Image analysis uses OpenAI's GPT-4 Vision models
- The legal database contains 455+ violation types mapped to 8 penalty profiles across 6 legal sources
- All BNBC clause references are sourced from the official Bangladesh National Building Code 2020
- The system supports both English and Bengali (বাংলা) interfaces
        """
    )
