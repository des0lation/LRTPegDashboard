import streamlit as st
import requests
import time
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


url = 'https://api.paraswap.io/prices/'

headers = {
    'accept': 'application/json, text/plain, */*',
    'accept-language': 'en-AU,en-GB;q=0.9,en-US;q=0.8,en;q=0.7',
    'if-none-match': 'W/"d28-4Cm/k3yOZ+ErybntIG2GfQfeNJU"',
    'ipn': 'ART2099',
    'origin': 'https://app.paraswap.io',
    'referer': 'https://app.paraswap.io/',
    'sec-ch-ua': '"Google Chrome";v="123", "Not:A-Brand";v="8", "Chromium";v="123"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-site',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36'
}
st.set_page_config(layout="wide")
st.title("Asset Slippage Dashboard")

tvl_data = {
    "rswETH": requests.get('https://api.llama.fi/tvl/swell-liquid-restaking').json(),
    "ezETH": requests.get('https://api.llama.fi/tvl/renzo').json(),
    "weETH": requests.get('https://api.llama.fi/tvl/ether.fi-stake').json(),
    "pufETH": requests.get('https://api.llama.fi/tvl/puffer-finance').json(),
    "rsETH": requests.get('https://api.llama.fi/tvl/kelp-dao').json()
}


eth_price = requests.get('https://coins.llama.fi/prices/current/ethereum:0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2?searchWidth=4h').json()["coins"]["ethereum:0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"]["price"]
max_slippage_amount = st.number_input('Enter max slippage amount (%)', value=0.5, step=0.1)

tvl_fig = go.Figure()

# Adding data to the chart
tvl_fig.add_trace(go.Bar(
    x=["Swell rswETH", "Renzo ezETH", "EtherFi eETH","Puffer Finance pufETH","Kelp rseTH"],
    y=[tvl_data["rswETH"],tvl_data["ezETH"],tvl_data["weETH"],tvl_data["pufETH"],tvl_data["rsETH"]],
))

tvl_fig.update_layout(
    title="LRT Protocl TVLs",
    xaxis_title="Projects",
    yaxis_title="Total Value Locked (TVL)",
    template="plotly_dark"
)

st.plotly_chart(tvl_fig)

token_dict = {
    "rswETH":'0xfae103dc9cf190ed75350761e95403b7b8afa6c0',
    "weETH":'0xCd5fE23C85820F7B72D0926FC9b05b43E359b7ee',
    'pufETH':'0xD9A442856C234a39a81a089C06451EBAa4306a72',
    'ezETH':'0xbf5495Efe5DB9ce00f80364C8B423567e58d2110',
    'rsETH':'0xA1290d69c65A6Fe4DF752f95823fae25cB99e5A7'
}

def makeKyberTrade(token_in,amount_in,max_slippage_amount):
    base_url = "https://aggregator-api.kyberswap.com/ethereum/api/v1/routes"
    params = {
        'tokenIn': token_dict[token_in],
        'tokenOut': '0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE',
        'amountIn': amount_in*10**18,
        'gasInclude': True
    }
    response = requests.get(base_url, headers=headers, params=params)
    try:
        responsejson = response.json()['data']["routeSummary"]
        slippage = 100*(1- float(responsejson['amountOutUsd'])/float(responsejson['amountInUsd']))
    except:
        st.write("Encountered Kyberswap Rate Limit on",token_in)
        slippage = max_slippage_amount
    return slippage

def increment(asset):
    if asset == "rswETH":
        return 250
    if asset == "weETH":
        return 250
    if asset == 'pufETH':
        return 250
    if asset =='ezETH':
        return 250
    if asset == 'rsETH':
        return 250

progress_bar = st.progress(0)
progress_text = st.empty()

# List to store data for plotting
asset_data = []

# Processing each asset
total_assets = len(token_dict)
processed_assets = 0

for asset in token_dict.keys():
    slippage = 0
    swap_amount = 0
    increment_amount = increment(asset)
    while slippage < max_slippage_amount:
        swap_amount += increment_amount
        slippage = makeKyberTrade(asset, swap_amount, max_slippage_amount)
        time.sleep(1)
        print(slippage)

    asset_data.append({'Asset': asset, 'Swap Amount': swap_amount})
    processed_assets += 1
    progress_bar.progress(processed_assets / total_assets)
    progress_text.text(f"Processing {processed_assets} of {total_assets} assets...")

# Clear the progress text and bar after completion
progress_text.empty()
progress_bar.empty()

# Creating a DataFrame and plotting
df = pd.DataFrame(asset_data)
fig = px.bar(df, x='Asset', y='Swap Amount', title="Trade Sizes by Asset for Sub Max Slippage%")
st.plotly_chart(fig)

st.write(asset_data)

asset_list = []
tvl_ratio = []
for asset in asset_data:
    asset_list.append(asset['Asset'])
    tvl = tvl_data[asset['Asset']]
    ratio = (asset['Swap Amount']*eth_price)/tvl
    tvl_ratio.append(ratio)

tvl_ratio_fig = go.Figure()

# Adding data to the chart
tvl_ratio_fig.add_trace(go.Bar(
    x=asset_list,
    y=tvl_ratio,
))

tvl_ratio_fig.update_layout(
    title="LRT Protocol Liquidity to TVL Ratio",
    xaxis_title="Projects",
    yaxis_title="TVL to Liquidity Ratio",
    template="plotly_dark"
)

st.plotly_chart(tvl_ratio_fig)