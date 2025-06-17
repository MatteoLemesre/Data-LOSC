import streamlit as st

st.set_page_config(page_title="Home - Data LOSC", page_icon="⚽")

st.title("⚽ Data LOSC - Dashboard")

st.markdown("""
Welcome to the **Data LOSC dashboard**, a personal tool to **analyze, compare, and visualize player performances** from LOSC and beyond.

---

## 📁 Available Pages

### 🔢 **1. Player Rating per Match**
> View the rating of each player for every match, based on detailed stats.

📍 *Page: `Player Rating per Match`*

---

### 🏆 **2. Teams of the Season**
> Discover the top players by position, automatically selected based on season-long performance.

📍 *Page: `Teams of the Season`*

---

### 📊 **3. Individual Performances**
> Analyze full-season performance for any player, featuring radar charts and average ratings.

📍 *Page: `Individual Performance`*

---

### ⚡ **4. Top Match Stats**
> Highlight the best individual performances in a single game based on a chosen stat.

📍 *Page: `Top Match Stats`*

---

## 🔍 Data & Methodology

- Data from **FBref**
- Custom role-based performance indexes
- Ratings adjusted by playing time and position

---

> Use the sidebar on the left to start exploring!
""")