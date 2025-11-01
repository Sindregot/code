import streamlit as st
import pandas as pd
import requests
import time

st.set_page_config(page_title="Warframe Endo Calculator", layout="wide")

@st.cache_data(ttl=3600)
def get_rivens():
    url = "https://api.warframe.market/v1/auctions/search?type=riven"
    response = requests.get(url)
    data = response.json()
    if "payload" not in data or "auctions" not in data["payload"]:
        st.error("⚠️ Failed to fetch Riven data from API.")
        return [], int(time.time())
    auctions = data["payload"]["auctions"]
    return auctions, int(time.time())

def calculate_riven_endo(mastery_rank, mod_rank, rerolls):
    return 100 * (mastery_rank - 8) + 22.5 * (2 ** mod_rank) + 200 * rerolls

# Endo values for standard items
AYATAN_VALUES = {
    "Piv": 2000,
    "Valana": 3000,
    "Anasa": 3450,
    "Orta": 1000,
}

MOD_ENDO_VALUES = {
    "Rare Rank 10": 30000,
    "Legendary Rank 10": 40000,
    "Uncommon Rank 10": 20000,
    "Common Rank 10": 10000,
}

st.title("💠 Warframe Endo Value Tracker")

# Load Riven data
with st.spinner("Fetching latest Riven data..."):
    rivens, last_fetched = get_rivens()

# Check for new API data
current_time = int(time.time())
if current_time - last_fetched > 3600:
    st.warning("⚠️ New API data may be available. Click below to refresh.")
    if st.button("🔄 Refresh Now"):
        st.cache_data.clear()
        st.rerun()
else:
    st.success("✅ Data is up to date (within the last hour).")

# Sidebar
st.sidebar.header("Settings")

highlight = st.sidebar.toggle("Highlight high Endo yields", value=True)
show_non_riven = st.sidebar.toggle("Include regular mods & Ayatans", value=True)

# Input fields for Riven simulation
st.sidebar.subheader("Riven Endo Calculator")
mastery_rank = st.sidebar.number_input("Mastery Rank", 8, 30, 8)
mod_rank = st.sidebar.number_input("Riven Mod Rank", 0, 8, 8)
rerolls = st.sidebar.number_input("Rerolls", 0, 100, 30)
endo_yield = calculate_riven_endo(mastery_rank, mod_rank, rerolls)
st.sidebar.metric("Estimated Endo Yield", f"{endo_yield:,.0f}")

# Process Riven data
riven_data = []
for a in rivens:
    item = a.get("item", {})
    if not item:
        continue
    item_name = item.get("name", "Unknown")
    price = a.get("buyout_price", 0)
    mod_rank = item.get("mod_rank", 0)
    rerolls = item.get("re_rolls", 0)
    mastery_rank = item.get("mastery_level", 8)
    auction_id = a.get("id", "")
    user_status = a.get("owner", {}).get("status", "offline")

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

if not riven_data:
    st.error("No valid Riven data found.")
else:
    df = pd.DataFrame(riven_data)
    df.sort_values(by="Price (p)", ascending=True, inplace=True)

    # Filter status
    status_options = st.sidebar.multiselect(
        "Filter by Seller Status",
        ["ingame", "online", "offline"],
        default=["ingame", "online", "offline"]
    )
    df = df[df["Status"].isin(status_options)]

    # Highlight logic
    def highlight_endo(val):
        if not highlight:
            return ''
        if val > 30000:
            return 'background-color: #ffeb3b'
        elif val > 20000:
            return 'background-color: #fff9c4'
        return ''

    styled_df = df.style.applymap(highlight_endo, subset=["Endo"])

    # Display Rivens
    st.subheader("Riven Mods (sorted by price)")
    st.dataframe(styled_df, use_container_width=True)

    # Add clickable links
    for _, row in df.iterrows():
        st.markdown(
            f"[🔗 {row['Item']} on Warframe Market]({row['Link']})",
            unsafe_allow_html=True
        )

# Optional section: Non-Riven Endo
if show_non_riven:
    st.subheader("Additional Endo Sources")

    cols = st.columns(2)

    with cols[0]:
        st.write("### Regular Mods")
        mod_table = pd.DataFrame(
            list(MOD_ENDO_VALUES.items()), columns=["Mod Type", "Endo Yield"]
        )
        st.table(mod_table)

    with cols[1]:
        st.write("### Ayatan Sculptures")
        ayatan_table = pd.DataFrame(
            list(AYATAN_VALUES.items()), columns=["Sculpture", "Endo Yield"]
        )
        st.table(ayatan_table)

st.caption("Data from Warframe Market API. Updated hourly.")
