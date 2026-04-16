import streamlit as st
import sqlite3
import pandas as pd

def show_dashboard():
    """Render the summary dashboard page."""
    st.title("📊 Sanitation Dashboard")
    st.caption("Overview of all submitted facility reports.")

    # ── Fetch data ──────────────────────────────
    conn = sqlite3.connect("sanitation.db")
    df = pd.read_sql_query("SELECT * FROM reports", conn)
    conn.close()

    if df.empty:
        st.info("No reports yet. Submit one from the Report page!")
        return

    total = len(df)

    # ── Top-level metrics ───────────────────────
    clean_count    = len(df[df["hygiene_label"] == "Clean"])
    moderate_count = len(df[df["hygiene_label"] == "Moderate"])
    dirty_count    = len(df[df["hygiene_label"] == "Dirty"])
    high_priority  = len(df[df["priority"].str.contains("High", na=False)])
    avg_score      = round(df["hygiene_score"].mean(), 1) if "hygiene_score" in df.columns else "N/A"

    st.markdown("### 📈 Key Metrics")
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("📋 Total Reports", total)
    col2.metric("🟢 Clean", clean_count)
    col3.metric("🟡 Moderate", moderate_count)
    col4.metric("🔴 Dirty", dirty_count)
    col5.metric("🚨 High Priority", high_priority)

    st.markdown(f"**Average Hygiene Score:** {avg_score} / 5")

    st.markdown("---")

    # ── Hygiene Distribution Chart ──────────────
    st.markdown("### 🧼 Hygiene Level Distribution")
    hygiene_counts = df["hygiene_label"].value_counts()
    # Reindex to ensure consistent order
    hygiene_counts = hygiene_counts.reindex(["Clean", "Moderate", "Dirty"], fill_value=0)
    st.bar_chart(hygiene_counts)

    # ── Rating Distribution ─────────────────────
    st.markdown("### ⭐ User Rating Distribution")
    rating_counts = df["rating"].value_counts().sort_index()
    # Ensure all ratings 1-5 are present
    rating_counts = rating_counts.reindex([1, 2, 3, 4, 5], fill_value=0)
    st.bar_chart(rating_counts)

    # ── Priority Breakdown ──────────────────────
    st.markdown("### 🚨 Priority Breakdown")
    if "priority" in df.columns:
        priority_counts = df["priority"].value_counts()
        st.bar_chart(priority_counts)
    else:
        st.info("Priority data not available.")

    # ── Issue Frequency ─────────────────────────
    st.markdown("### 🔍 Most Common Issues")
    if "detected_issues" in df.columns:
        all_issues = []
        for issues_str in df["detected_issues"].dropna():
            for issue in issues_str.split(", "):
                issue = issue.strip()
                if issue:
                    all_issues.append(issue)
        if all_issues:
            issue_df = pd.DataFrame(all_issues, columns=["Issue"])
            issue_counts = issue_df["Issue"].value_counts()
            st.bar_chart(issue_counts)
        else:
            st.success("No issues detected across reports!")
    else:
        st.info("Issue data not available.")

    # ── Location-wise Average Score ─────────────
    st.markdown("### 📍 Average Hygiene Score by Location")
    if "hygiene_score" in df.columns:
        loc_scores = df.groupby("location")["hygiene_score"].mean().round(1).sort_values()
        st.bar_chart(loc_scores)

    # ── Recent Reports Table ────────────────────
    st.markdown("---")
    st.subheader("📋 Recent Reports")
    display_cols = ["id", "location", "rating", "hygiene_label", "hygiene_score", "priority", "detected_issues"]
    available_cols = [c for c in display_cols if c in df.columns]
    st.dataframe(
        df[available_cols].sort_values("id", ascending=False).head(20),
        use_container_width=True,
    )

    # ── High Priority Alerts ────────────────────
    high_df = df[df["priority"].str.contains("High", na=False)]
    if not high_df.empty:
        st.markdown("---")
        st.subheader("🚨 High Priority Alerts")
        st.error(f"{len(high_df)} facilities need immediate attention!")
        for _, row in high_df.iterrows():
            with st.expander(f"📍 {row['location']} — Score: {row.get('hygiene_score', 'N/A')}"):
                st.markdown(f"- **Rating:** {row['rating']} / 5")
                st.markdown(f"- **Hygiene:** {row.get('hygiene_label', 'N/A')}")
                st.markdown(f"- **Issues:** {row.get('detected_issues', 'None')}")
                st.markdown(f"- **Review:** {row.get('review', 'N/A')}")


# Allow running standalone
if __name__ == "__main__":
    show_dashboard()