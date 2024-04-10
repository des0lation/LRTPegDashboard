import streamlit as st
import requests
import time
import pandas as pd
import plotly.express as px

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

st.title("Asset Slippage Dashboard")

max_slippage_amount = st.number_input('Enter max slippage amount (%)', value=1.0, step=0.1)

token_dict = {
    "rswETH":'0xfae103dc9cf190ed75350761e95403b7b8afa6c0',
    "weETH":'0xCd5fE23C85820F7B72D0926FC9b05b43E359b7ee',
    'pufETH':'0xD9A442856C234a39a81a089C06451EBAa4306a72',
    'ezETH':'0xbf5495Efe5DB9ce00f80364C8B423567e58d2110',
    'rsETH':'0xA1290d69c65A6Fe4DF752f95823fae25cB99e5A7'

}
def maketrade(swapToken,amount,max_slippage_amount):
    params = {
        'version': '5',
        'srcToken': str(token_dict[swapToken]),
        'destToken': '0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE',
        'amount': str(amount*10**18),
        'srcDecimals': '18',
        'destDecimals': '18',
        'side': 'SELL',
        'excludeDirectContractMethods': 'false',
        'network': '1',
        'otherExchangePrices': 'true',
        'partner': 'paraswap.io',
        'userAddress': '0x0000000000000000000000000000000000000000'
    }
    response = requests.get(url, headers=headers, params=params).json()
    try:
        responsejson = response['priceRoute']
        outputAmount = int(responsejson['destAmount'])
        slippage = 100*(1- float(responsejson['destUSD'])/float(responsejson['srcUSD']))
    except:
        slippage = max_slippage_amount
    return slippage


def increment(asset):
    if asset == "rswETH":
        return 100
    if asset == "weETH":
        return 100
    if asset == 'pufETH':
        return 100
    if asset =='ezETH':
        return 250
    if asset == 'rsETH':
        return 500


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
        slippage = maketrade(asset, swap_amount, max_slippage_amount)
        time.sleep(1.5)  # Be cautious with this delay to avoid hitting API rate limits

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