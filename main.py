import streamlit as st
import pandas as pd
import requests
import time

st.set_page_config(page_title="Warframe Endo Tracker", layout="wide")

# ------------------------------
# Helper functions
# ------------------------------
@st.cache_data(ttl=3600)
def get_rivens():
    url = "https://api.warframe.market/v1/auctions"
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        contracts = data.get("payload", {}).get("items", [])
        if not contracts:
            st.warning("⚠️ No unveiled Riven contracts currently available.")
        return contracts, int(time.time())
    except Exception as e:
        st.error(f"⚠️ Failed to fetch Riven data: {e}")
        return [], int(time.time())

def calculate_riven_endo(mastery_rank, mod_rank, rerolls):
    return 100 * (mastery_rank - 8) + 22.5 * (2 ** mod_rank) + 200 * rerolls

# ------------------------------
# App UI
# ------------------------------
st.title("💠 Warframe Rank 8 Riven Endo Tracker")

# Sidebar settings
st.sidebar.header("Settings")
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
    contracts, last_fetched = get_rivens()

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
for contract in contracts:
    riven = contract.get("item", {})
    if not riven:
        continue
    rank = riven.get("mod_rank", 0)
    if rank != 8:
        continue  # only show rank 8

    item_name = riven.get("name", "Unknown")
    mastery_rank = riven.get("mastery_level", 8)
    rerolls = riven.get("re_rolls", 0)
    price = contract.get("buyout_price", 0)
    auction_id = contract.get("id", "")
    user_status = contract.get("owner", {}).get("status", "offline")
    if user_status not in status_filter:
        continue

    endo = calculate_riven_endo(mastery_rank, rank, rerolls)
    efficiency = endo / price if price > 0 else 0
    url = f"https://warframe.market/auction/{auction_id}"

    riven_data.append({
        "Item": item_name,
        "Mastery Rank": mastery_rank,
        "Mod Rank": rank,
        "Rerolls": rerolls,
        "Price (p)": int(price),  # remove decimals
        "Endo": int(endo),
        "Efficiency": efficiency,
        "Status": user_status,
        "Link": url
    })

# ------------------------------
# Display Riven table
# ------------------------------
if not riven_data:
    st.warning("No valid Rank 8 Riven contracts found.")
else:
    df = pd.DataFrame(riven_data)
    # Sort by efficiency descending
    df.sort_values(by="Efficiency", ascending=False, inplace=True)

    st.subheader("Rank 8 Riven Contracts")
    # Show table without highlighting
    st.dataframe(df[["Item", "Mastery Rank", "Mod Rank", "Rerolls", "Price (p)", "Endo", "Efficiency", "Status"]], use_container_width=True)

    # Add clickable copy-to-clipboard buttons for links
    st.write("Links to Warframe Market listings:")
    for i, row in df.iterrows():
        st.button(
            f"Copy link for {row['Item']}",
            key=f"link_{i}",
            on_click=st.experimental_set_clipboard,
            args=(row["Link"],)
        )

st.caption("Data from Warframe Market API. Updated hourly.")
