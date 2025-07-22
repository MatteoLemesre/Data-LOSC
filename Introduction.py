# streamlit run "/Users/matteolemesre/Desktop/Data LOSC/Github/Introduction.py"
import streamlit as st

st.set_page_config(page_title="Home - Data LOSC", page_icon="⚽")

st.title("⚽ Data LOSC")

st.markdown("""I'm passionate about **data analysis**, **data science**, and **football**, especially as a dedicated **Lille OSC** supporter. This dashboard is a **personal data science project** built to **analyze, compare, and visualize football player performances**.

It is the result of a complete **end-to-end workflow**, including:

- 🌐 **Web scraping** of detailed player statistics from [FBref.com](https://fbref.com), covering the **Top 5 European leagues** (*Ligue 1, Serie A, Premier League, Liga, Bundesliga*) and the **3 major European cups** (*UEFA Champions League, Europa League, and Conference League*), totaling **2100+ matches per season**.
- 🧹 **Data cleaning**: standardizing, enriching, and formatting raw scraped data for analysis.
- 📈 **Data analysis**: extracting key indicators per position, filtering relevant metrics, and identifying patterns.
- 🧮 **Custom rating algorithm**: a performance index I personally designed, combining multiple metrics weighted by **position** and **playing time** to deliver a **match-by-match rating**.
- 🎯 **Percentile-based comparison system**: highlights player strengths by comparing them to their peers.

This dashboard brings together **statistics**, **visuals**, and **contextual insights**, all tailored for **football analysis** from a **data-driven perspective**.

---

> 👉 Use the **sidebar on the left** to start exploring the data!
""")