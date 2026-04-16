import streamlit as st
import sqlite3
import pandas as pd
import pydeck as pdk
import random

LOCATION_COORDS = {
    # Tamil Nadu
    "chennai": (13.0827, 80.2707),
    "coimbatore": (11.0168, 76.9558),
    "madurai": (9.9252, 78.1198),
    "tiruchirappalli": (10.7905, 78.7047),
    "salem": (11.6643, 78.1460),
    "tirunelveli": (8.7139, 77.7567),
    "vellore": (12.9165, 79.1325),
    "thoothukudi": (8.7642, 78.1348),
    "kanchipuram": (12.8342, 79.7036),
    "erode": (11.3410, 77.7172),
    "hosur": (12.7409, 77.8253),
    "dindigul": (10.3673, 77.9803),
    "thanjavur": (10.7867, 79.1378),

    # India major cities
    "bangalore": (12.9716, 77.5946),
    "bengaluru": (12.9716, 77.5946),
    "mumbai": (19.0760, 72.8777),
    "delhi": (28.7041, 77.1025),
    "kolkata": (22.5726, 88.3639),
    "hyderabad": (17.3850, 78.4867),
    "pune": (18.5204, 73.8567),
    "ahmedabad": (23.0225, 72.5714),
}

# ─────────────────────────────────────────────
def guess_coordinates(location_text):
    text = str(location_text).lower()

    for key, coords in LOCATION_COORDS.items():
        if key in text:
            return coords

    # fallback: INDIA RANDOM SPREAD ONLY
    return (
        random.uniform(8, 34),     # India latitude range
        random.uniform(68, 97)     # India longitude range
    )

# ─────────────────────────────────────────────
def get_color(label):
    if label == "Clean":
        return [46, 204, 113, 200]
    elif label == "Moderate":
        return [241, 196, 15, 200]
    else:
        return [231, 76, 60, 200]

# ─────────────────────────────────────────────
def show_map():
    st.title("🗺️ India Sanitation Monitoring Map")

    conn = sqlite3.connect("sanitation.db")
    df = pd.read_sql_query("SELECT * FROM reports", conn)
    conn.close()

    if df.empty:
        st.info("No reports yet.")
        return

    data = []

    for _, row in df.iterrows():
        lat, lon = guess_coordinates(row["location"])

        data.append({
            "lat": lat,
            "lon": lon,
            "location": row["location"],
            "rating": row["rating"],
            "hygiene_label": row["hygiene_label"],
            "detected_issues": row["detected_issues"],
            "hygiene_score": row["hygiene_score"],
            "priority": row["priority"],
            "color": get_color(row["hygiene_label"]),
        })

    map_df = pd.DataFrame(data)

    st.markdown("### Filter")

    selected = st.multiselect(
        "Hygiene Level:",
        ["Clean", "Moderate", "Dirty"],
        default=["Clean", "Moderate", "Dirty"]
    )

    filtered = map_df[map_df["hygiene_label"].isin(selected)]

    if filtered.empty:
        st.warning("No data available.")
        return

    layer = pdk.Layer(
        "ScatterplotLayer",
        data=filtered,
        get_position='[lon, lat]',
        get_color='color',
        get_radius=30000,
        pickable=True,
    )

    view_state = pdk.ViewState(
        latitude=22.0,
        longitude=79.0,
        zoom=4.5,   # 🇮🇳 India zoom
        pitch=0,
    )

    tooltip = {
        "html": """
        <b>📍 {location}</b><br/>
        ⭐ Rating: {rating}<br/>
        🧼 {hygiene_label}<br/>
        🧾 {detected_issues}<br/>
        🚨 {priority}
        """,
        "style": {"backgroundColor": "black", "color": "white"}
    }

    st.pydeck_chart(pdk.Deck(layers=[layer], initial_view_state=view_state, tooltip=tooltip))

    st.markdown("---")
    st.subheader("📋 Report Data")
    st.dataframe(filtered, use_container_width=True)


if __name__ == "__main__":
    show_map()