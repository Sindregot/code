import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import json
import time

st.set_page_config(page_title="Warframe Riven Endo Tracker", layout="wide")


# ------------------------------
# Helper functions
# ------------------------------
def fetch_riven_auctions():
    url = "https://warframe.market/auctions/riven_mods"
    response = requests.get(url)
    html = response.text
    soup = BeautifulSoup(html, "html.parser")

    # Extract JSON from the script containing 'window.__NUXT__'
    scripts = soup.find_all("script")
    json_text = None
    for script in scripts:
        if "window.__NUXT__" in script.text:
            start = script.text.find("{")
            end = script.text.rfind("}") + 1
            json_text = script.text[start:end]
            break

    if not json_text:
        st.error("⚠️ Could not find Riven auction data on the page.")
        return []

    data = json.loads(json_text)

    # Find Riven auctions in the JSON (may vary depending on site structure)
    auctions = []
    try:
        all_auctions = data["state"]["auctions"]
        for a in all_auctions:
            if a["item"]["item_type"] == "RIVEN":
                auctions.append(a)
    except KeyError:
        st.error("⚠️ Unexpected JSON structure. Unable to parse auctions.")

    return auctions


def calculate_riven_endo(mastery_rank, mod_rank, rerolls):
    return 100 * (mastery_rank - 8) + 22.5 * (2 ** mod_rank) + 200 * rerolls


# ------------------------------
# Streamlit UI
# ------------------------------
st.title("💠 Warframe Riven Endo Tracker (Web Scraping)")

# Sidebar inputs for Riven simulation
st.sidebar.header("Riven Endo Calculator")
mastery_rank_input = st.sidebar.number_input("Mastery Rank", 8, 30, 8)
mod_rank_input = st.sidebar.number_input("Riven Mod Rank", 0, 8, 8)
rerolls_input = st.sidebar.number_input("Rerolls", 0, 100, 30)
endo_yield_input = calculate_riven_endo(mastery_rank_input, mod_rank_input, rerolls_input)
st.sidebar.metric("Estimated Endo Yield", f"{endo_yield_input:,.0f}")

# ------------------------------
# Fetch Riven auctions
# ------------------------------
with st.spinner("Fetching Riven auctions from Warframe Market..."):
    riven_auctions = fetch_riven_auctions()
    last_fetched = int(time.time())

if not riven_auctions:
    st.warning("No Riven auctions found.")
else:
    st.success(f"✅ {len(riven_auctions)} Riven auctions fetched.")

# ------------------------------
# Process auctions into DataFrame
# ------------------------------
riven_data = []
for a in riven_auctions:
    item = a["item"]
    price = a.get("buyout_price", 0)
    mastery_rank = item.get("mastery_level", 8)
    mod_rank = item.get("mod_rank", 0)
    rerolls = item.get("re_rolls", 0)
    endo = calculate_riven_endo(mastery_rank, mod_rank, rerolls)
    efficiency = endo / price if price > 0 else 0
    auction_id = a.get("id", "")
    status = a.get("owner", {}).get("status", "offline")
    url = f"https://warframe.market/auction/{auction_id}"

    riven_data.append({
        "Item": item.get("name", "Unknown"),
        "Mastery Rank": mastery_rank,
        "Mod Rank": mod_rank,
        "Rerolls": rerolls,
        "Price (p)": int(price),
        "Endo": int(endo),
        "Efficiency": efficiency,
        "Status": status,
        "Link": url
    })

# Convert to DataFrame
df = pd.DataFrame(riven_data)
df.sort_values(by="Efficiency", ascending=False, inplace=True)

# ------------------------------
# Display table
# ------------------------------
st.subheader("Riven Auctions")
st.dataframe(df[["Item", "Mastery Rank", "Mod Rank", "Rerolls", "Price (p)", "Endo", "Efficiency", "Status"]],
             use_container_width=True)

# ------------------------------
# Copy-link buttons
# ------------------------------
st.write("Copy auction links:")
for i, row in df.iterrows():
    st.button(
        f"Copy link for {row['Item']}",
        key=f"link_{i}",
        on_click=st.experimental_set_clipboard,
        args=(row["Link"],)
    )

st.caption("Data scraped from Warframe Market. Updated live on page refresh.")
