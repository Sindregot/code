import streamlit as st
import pandas as pd
import requests
import time

st.set_page_config(page_title="Warframe Endo Calculator", layout="wide")

# ------------------------------
# Helper functions
# ------------------------------
@st.cache_data(ttl=3600)
def get_rivens():
    url = "https://api.warframe.market/v1/auctions/search?type=riven&language=en"
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        auctions = data.get("payload", {}).get("auctions", [])
        if not auctions:
            st.warning("⚠️ No Riven auctions currently available.")
        return auctions, int(time.time())
    except Exception as e:
        st.error(f"⚠️ Failed to fetch Riven data: {e}")
        return [], int(time.time())

def calculate_riven_endo(mastery_rank, mod_rank, rerolls):
    """Calculate endo yield from a Riven mod"""
    return 100 * (mastery_rank - 8) + 22.5 * (2 ** mod_rank) + 200 * rerolls

def highlight_endo(val):
    """Highlight high endo yields"""
    if highlight_toggle:
        if val > 30000:
            return 'background-color: #ffeb3b'
        elif val > 20000:
            return 'background-color: #fff9c4'
    return ''

# ------------------------------
# App UI
# ------------------------------
st.title("💠 Warframe Riven Endo Tracker")

# Sidebar settings
st.sidebar.header("Settings")
highlight_toggle = st.sidebar.toggle("Highlight high Endo yields", value=True)
status_filter = st.sidebar.multiselect(
    "Filter by Seller Status",
    ["ingame", "online", "offline"],
    default=["ingame", "online", "offline"]
)

# Riven endo calculator inputs
st.sidebar.subheader("Riven Endo Calculator")
mastery_rank_input = st.sidebar.number_input("Mastery Rank", 8, 30, 8)
mod_rank_input = st.sidebar.number_input("Riven Mod Rank", 0, 8, 8)
rerolls_input = st.sidebar.number_input("Rerolls", 0, 100, 30)
endo_yield_input = calculate_riven_endo(mastery_rank_input, mod_rank_input, rerolls_input)
st.sidebar.metric("Estimated Endo Yield", f"{endo_yield_input:,.0f}")

# ------------------------------
# Fetch Riven data
# ------------------------------
with st.spinner("Fetching latest Riven data..."):
    rivens, last_fetched = get_rivens()

current_time = int(time.time())
if current_time - last_fetched > 3600:
    st.warning("⚠️ New API data may be available. Click below to refresh.")
    if st.button("🔄 Refresh Now"):
        st.cache_data.clear()
        st.rerun()
else:
    st.success("✅ Data is up to date (within the last hour).")

# ------------------------------
# Process Riven data
# ------------------------------
riven_data = []
for auction in rivens:
    item = auction.get("item", {})
    if not item:
        continue
    auction_id = auction.get("id", "")
    item_name = item.get("name", "Unknown")
    price = auction.get("buyout_price", 0)
    mod_rank = item.get("mod_rank", 0)
    rerolls = item.get("re_rolls", 0)
    mastery_rank = item.get("mastery_level", 8)
    user_status = auction.get("owner", {}).get("status", "offline")

    # Only include filtered statuses
    if user_status not in status_filter:
        continue

    endo = calculate_riven_endo(mastery_rank, mod_rank, rerolls)
    url = f"https://warframe.market/auction/{auction_id}"

    riven_data.append({
        "Item": item_name,
        "Mastery Rank": mastery_rank,
        "Mod Rank": mod_rank,
        "Rerolls": rerolls,
        "Price (p)": price,
        "Endo": int(endo),
        "Status": user_status,
        "Link": url
    })

# ------------------------------
# Display Riven table
# ------------------------------
if not riven_data:
    st.warning("No valid Riven data found.")
else:
    df = pd.DataFrame(riven_data)
    df.sort_values(by="Price (p)", ascending=True, inplace=True)

    # Style dataframe
    styled_df = df.style.applymap(highlight_endo, subset=["Endo"])

    st.subheader("Riven Mods (sorted by price)")
    st.dataframe(styled_df, use_container_width=True)

    # Add clickable links
    for _, row in df.iterrows():
        st.markdown(
            f"[🔗 {row['Item']} on Warframe Market]({row['Link']})",
            unsafe_allow_html=True
        )

st.caption("Data from Warframe Market API. Updated hourly.")
