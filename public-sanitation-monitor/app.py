import streamlit as st
import sqlite3
import os
import numpy as np
from PIL import Image

# ─────────────────────────────────────────────
# DATABASE
# ─────────────────────────────────────────────
def init_db():
    conn = sqlite3.connect("sanitation.db")
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS reports (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            image_path      TEXT,
            review          TEXT,
            rating          INTEGER,
            location        TEXT,
            hygiene_label   TEXT,
            detected_issues TEXT,
            hygiene_score   REAL,
            priority        TEXT
        )
    """)
    conn.commit()
    conn.close()

def save_report(image_path, review, rating, location,
                hygiene_label, detected_issues, hygiene_score, priority):
    conn = sqlite3.connect("sanitation.db")
    c = conn.cursor()
    c.execute("""
        INSERT INTO reports
            (image_path, review, rating, location,
             hygiene_label, detected_issues, hygiene_score, priority)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (image_path, review, rating, location,
          hygiene_label, ", ".join(detected_issues), hygiene_score, priority))
    conn.commit()
    conn.close()

def fetch_all_reports():
    conn = sqlite3.connect("sanitation.db")
    c = conn.cursor()
    c.execute("SELECT * FROM reports")
    rows = c.fetchall()
    col_names = [description[0] for description in c.description] if c.description else []
    conn.close()
    return rows, col_names

# ─────────────────────────────────────────────
# IMAGE CLASSIFICATION
# ─────────────────────────────────────────────
def classify_hygiene(image_file):
    img = image_file.convert("RGB").resize((100, 100))
    pixels = np.array(img, dtype=float)

    brightness = pixels.mean()

    r = pixels[:, :, 0].mean()
    g = pixels[:, :, 1].mean()
    b = pixels[:, :, 2].mean()

    # better stain detection (more sensitive)
    stain_score = (r * 0.4 + g * 0.4) - (b * 0.2)

    # NORMALIZED SCORING (IMPORTANT FIX)
    hygiene_index = brightness + (stain_score * 0.6)

    if hygiene_index > 170:
        label = "Clean"
    elif hygiene_index > 120:
        label = "Moderate"
    else:
        label = "Dirty"

    return label, round(brightness, 1), round(stain_score, 1)
# ─────────────────────────────────────────────
# NLP ISSUE DETECTION
# ─────────────────────────────────────────────
ISSUE_KEYWORDS = {
    "🧹 Cleanliness Problem": ["dirty", "filthy", "stained", "unhygienic", "messy",
                               "grimy", "unclean", "disgusting", "waste", "garbage"],
    "💧 No Water":            ["no water", "dry tap", "pipe broken", "water not working",
                               "no supply", "tap dry", "no running water"],
    "🤢 Bad Smell":           ["smell", "stink", "stinking", "odour", "odor",
                               "stench", "foul", "bad smell", "reeks"],
    "💡 Poor Lighting":       ["dark", "dim", "no light", "broken light", "poor lighting",
                               "can't see", "lights not working", "pitch black"],
    "♿ Accessibility Issue":  ["wheelchair", "no ramp", "narrow", "can't access",
                               "not accessible", "disabled", "steps only", "no handle"],
}

def detect_issues(review_text: str):
    text   = review_text.lower()
    issues = []
    for category, keywords in ISSUE_KEYWORDS.items():
        if any(kw in text for kw in keywords):
            issues.append(category)
    return issues

# ─────────────────────────────────────────────
# HYGIENE SCORE
# ─────────────────────────────────────────────
IMAGE_SCORE_MAP = {"Clean": 5, "Moderate": 3, "Dirty": 1}

def compute_hygiene_score(user_rating: int, hygiene_label: str, issues: list):
    image_score = IMAGE_SCORE_MAP.get(hygiene_label, 3)
    base_score  = (user_rating + image_score) / 2
    deduction   = len(issues) * 0.5
    final       = max(1.0, min(5.0, base_score - deduction))
    return round(final, 1)

def get_priority(score: float):
    if score < 2.5:
        return "🚨 High Priority"
    elif score <= 3.5:
        return "⚠️ Medium Priority"
    else:
        return "✅ Low Priority"

# ─────────────────────────────────────────────
# RATING LABELS
# ─────────────────────────────────────────────
RATING_LABELS = {1: "Very Poor", 2: "Poor", 3: "Average", 4: "Good", 5: "Excellent"}

# ─────────────────────────────────────────────
# INIT
# ─────────────────────────────────────────────
init_db()
os.makedirs("images", exist_ok=True)

st.set_page_config(page_title="Public Sanitation Monitor", page_icon="🚻", layout="wide")

# ─────────────────────────────────────────────
# SIDEBAR NAVIGATION
# ─────────────────────────────────────────────
st.sidebar.title("🚻 Sanitation Monitor")
st.sidebar.markdown("---")
page = st.sidebar.radio(
    "Navigate to:",
    ["📝 Submit Report", "📊 Dashboard", "🗺️ Map View"],
    index=0,
)

# ─────────────────────────────────────────────
# PAGE: SUBMIT REPORT
# ─────────────────────────────────────────────
if page == "📝 Submit Report":
    st.title("🚻 Submit a Sanitation Report")
    st.caption("Report and rate the hygiene of public toilets near you.")

    # ── Location detection ──────────────────────
    if "location_value" not in st.session_state:
        st.session_state.location_value = ""

    if st.button("📍 Use Current Location"):
        st.session_state.location_value = "Chennai, India"
        st.rerun()

    if st.session_state.location_value:
        st.caption(f"✅ Detected: {st.session_state.location_value}")

    # ── Rating preview ──────────────────────────
    if "rating_value" not in st.session_state:
        st.session_state.rating_value = 3

    st.markdown("#### ⭐ Select Your Rating")
    rating_preview = st.slider(
        "Rating", min_value=1, max_value=5,
        value=st.session_state.rating_value,
        label_visibility="collapsed", key="rating_slider"
    )
    label = RATING_LABELS[rating_preview]
    color_map = {1: "🔴", 2: "🟠", 3: "🟡", 4: "🟢", 5: "✅"}
    st.markdown(f"{color_map[rating_preview]} **{rating_preview} — {label}**")

    # ── Submission form ─────────────────────────
    with st.form("report_form"):
        uploaded_file = st.file_uploader("📷 Upload Toilet Image", type=["jpg", "jpeg", "png"])
        review        = st.text_area("📝 Write Your Review",
                                     placeholder="e.g. Very dirty, bad smell, no water…")
        location      = st.text_input("📍 Enter Location",
                                      value=st.session_state.location_value,
                                      placeholder="e.g. Bus Stand, Chennai")
        submitted     = st.form_submit_button("🚀 Submit Report")

    if submitted:
        if not uploaded_file:
            st.warning("Please upload an image before submitting.")
        elif not review.strip():
            st.warning("Please enter a review.")
        elif not location.strip():
            st.warning("Please enter or detect your location.")
        else:
            img_path = os.path.join("images", uploaded_file.name)
            with open(img_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            image = Image.open(uploaded_file)

            hygiene_label, brightness, stain_score = classify_hygiene(image)
            issues = detect_issues(review)
            final_score = compute_hygiene_score(rating_preview, hygiene_label, issues)
            priority    = get_priority(final_score)

            save_report(img_path, review, rating_preview, location,
                        hygiene_label, issues, final_score, priority)

            st.success("✅ Report submitted successfully!")
            st.image(image, caption="Uploaded Image", use_container_width=True)

            col1, col2 = st.columns(2)
            with col1:
                st.metric("📍 Location", location)
                st.metric("⭐ Rating",  f"{rating_preview} — {RATING_LABELS[rating_preview]}")
            with col2:
                st.metric("🖼️ Image Analysis", hygiene_label)
                st.metric("🧮 Hygiene Score",  f"{final_score} / 5")

            st.info(f"📝 **Review:** {review}")

            st.markdown("### Priority Level")
            if final_score < 2.5:
                st.error(f"{priority} — Immediate Attention Needed!")
            elif final_score <= 3.5:
                st.warning(f"{priority} — Needs Monitoring")
            else:
                st.success(f"{priority} — Looks Acceptable")

            if issues:
                st.markdown("### 🔍 Detected Issues")
                cols = st.columns(len(issues))
                for i, issue in enumerate(issues):
                    cols[i].error(issue)
            else:
                st.success("✅ No major issues detected from the review.")

            with st.expander("📊 How was this score calculated?"):
                st.markdown(f"""
| Factor | Value |
|---|---|
| User Rating | {rating_preview} / 5 |
| Image Score | {IMAGE_SCORE_MAP.get(hygiene_label)} / 5 ({hygiene_label}) |
| Base Score (avg) | {round((rating_preview + IMAGE_SCORE_MAP.get(hygiene_label, 3)) / 2, 2)} |
| Issues Detected | {len(issues)} × −0.5 = −{len(issues) * 0.5} |
| **Final Score** | **{final_score} / 5** |
""")

            with st.expander("🔬 Image Analysis Details"):
                st.markdown(f"- **Brightness:** `{brightness}` (higher = cleaner appearance)")
                st.markdown(f"- **Stain Score:** `{stain_score}` (lower = less discolouration)")

    # ── Past Reports ────────────────────────────
    st.markdown("---")
    st.subheader("📋 All Submitted Reports")
    reports, col_names = fetch_all_reports()
    if reports:
        import pandas as pd
        df = pd.DataFrame(reports, columns=col_names)
        st.dataframe(df, use_container_width=True)
    else:
        st.info("No reports submitted yet.")

# ─────────────────────────────────────────────
# PAGE: DASHBOARD
# ─────────────────────────────────────────────
elif page == "📊 Dashboard":
    from dashboard import show_dashboard
    show_dashboard()

# ─────────────────────────────────────────────
# PAGE: MAP VIEW
# ─────────────────────────────────────────────
elif page == "🗺️ Map View":
    from map_view import show_map
    show_map()