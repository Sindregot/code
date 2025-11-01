import streamlit as st
import pandas as pd
import requests
import time

st.set_page_config(page_title="Warframe Endo Tracker", layout="wide")

# ------------------------------
# Helper functions
# ------------------------------
@st.cache_data(ttl=3600)
def get_auctions():
    url = "https://api.warframe.market/v1/auctions/search?type=riven"
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        auctions = data.get("payload", {}).get("auctions", [])
        if not auctions:
            st.warning("⚠️ No auctions currently available.")
        return auctions, int(time.time())
    except Exception as e:
        st.error(f"⚠️ Failed to fetch auction data: {e}")
        return [], int(time.time())

def calculate_riven_endo(mastery_rank, mod_rank, rerolls):
    return 100 * (mastery_rank - 8) + 22.5 * (2 ** mod_rank) + 200 * rerolls

# ------------------------------
# App UI
# ------------------------------
st.title("💠 Warframe Riven Endo Tracker")

# Sidebar inputs for simulation
st.sidebar.header("Riven Endo Calculator")
mastery_rank_input = st.sidebar.number_input("Mastery Rank", 8, 30, 8)
mod_rank_input = st.sidebar.number_input("Riven Mod Rank", 0, 8, 8)
rerolls_input = st.sidebar.number_input("Rerolls", 0, 100, 30)
endo_yield_input = calculate_riven_endo(mastery_rank_input, mod_rank_input, rerolls_input)
st.sidebar.metric("Estimated Endo Yield", f"{endo_yield_input:,.0f}")

# ------------------------------
# Fetch auction data
# ------------------------------
with st.spinner("Fetching latest auction data..."):
    auctions, last_fetched = get_auctions()

current_time = int(time.time())
if current_time - last_fetched > 3600:
    st.warning("⚠️ New API data may be available. Click below to refresh.")
    if st.button("🔄 Refresh Now"):
        st.cache_data.clear()
        st.rerun()
else:
    st.success("✅ Data is up to date (within the last hour).")

# ------------------------------
# Process Riven auctions
# ------------------------------
riven_data = []
for a in auctions:
    item = a.get("item", {})
    if not item or item.get("item_type") != "RIVEN":
        continue

    item_name = item.get("name", "Unknown")
    mod_rank = item.get("mod_rank", 0)
    mastery_rank = item.get("mastery_level", 8)
    rerolls = item.get("re_rolls", 0)
    price = a.get("buyout_price", 0)
    auction_id = a.get("id", "")
    user_status = a.get("owner", {}).get("status", "offline")

    endo = calculate_riven_endo(mastery_rank, mod_rank, rerolls)
    efficiency = endo / price if price > 0 else 0
    url = f"https://warframe.market/auction/{auction_id}"

    riven_data.append({
        "Item": item_name,
        "Mastery Rank": mastery_rank,
        "Mod Rank": mod_rank,
        "Rerolls": rerolls,
        "Price (p)": int(price),
        "Endo": int(endo),
        "Efficiency": efficiency,
        "Status": user_status,
        "Link": url
    })

# ------------------------------
# Display table
# ------------------------------
if not riven_data:
    st.warning("No Riven auctions found.")
else:
    df = pd.DataFrame(riven_data)
    df.sort_values(by="Efficiency", ascending=False, inplace=True)

    st.subheader("Riven Auctions")
    st.dataframe(df[["Item", "Mastery Rank", "Mod Rank", "Rerolls", "Price (p)", "Endo", "Efficiency", "Status"]], use_container_width=True)

    st.write("Links to Warframe Market listings (click to copy):")
    for i, row in df.iterrows():
        st.button(
            f"Copy link for {row['Item']}",
            key=f"link_{i}",
            on_click=st.experimental_set_clipboard,
            args=(row["Link"],)
        )

st.caption("Data from Warframe Market API. Updated hourly.")
