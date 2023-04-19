import requests
import time
import pandas as pd
import plotly.express as px
import plotly.graph_objs as go
import streamlit as st
import io

st.set_page_config(page_title="Token Swaps Transaction Search", layout="wide")

dark_theme = """
    <style>
        body {
            background-color: #1f1f1f;
            color: #f8f8f8;
        }
        .st-bw {
            color: #f8f8f8;
        }
        .js-plotly-plot .hovertext {
            background-color: #ffffff;
            color: #000000;
        }
    </style>
"""


# Add CSS style block to the app
st.markdown(dark_theme, unsafe_allow_html=True)



chain_ids = {
    "1": "Ethereum",
    "56": "BSC",
    "137": "Polygon",
    "43114": "Avalanche",
    "42161": "Arbitrum",
    "250": "Fantom",
    "42220": "CELO",
    "10": "Optimism",
    "100": "Gnosis",
    "7000": "Canto",
    "42170": "Arbitrum Nova"
}


def get_transactions(chain_id, token_address, symbol, time_range, wallet_categories=None):
    url_template = "https://api.dev.dex.guru/v1/chain/{chain_id}/tokens/{token_address}/transactions/swaps?begin_timestamp={begin_timestamp}&end_timestamp={end_timestamp}&sort_by={sort_by}&order={order}&limit={limit}"

    headers = {
        "accept": "application/json",
        "api-key": "D5V-7R4r_GQcbwNCbtoT1HVX9wHh5aGkc8g5lWZ8MDg"
    }

    # Calculate begin and end timestamps
    end_timestamp = int(time.time())
    begin_timestamp = end_timestamp - (time_range * 86400)

    url = url_template.format(
        chain_id=chain_id,
        token_address=token_address,
        begin_timestamp=begin_timestamp,
        end_timestamp=end_timestamp,
        sort_by="timestamp",
        order="desc",
        limit=50000
    )

    transactions = []

    for i in range(5):
        response = requests.get(url, headers=headers)

        # Filter transactions where direction is 'out' and symbol is the user-specified symbol
        filtered_transactions = [tx for tx in response.json()["data"] if tx["direction"] == "out" and any(token["symbol"] == symbol for token in tx["tokens_out"]) and (not wallet_categories or tx["wallet_category"] in wallet_categories)]

        # Extract required fields from filtered transactions
        output = []
        for tx in filtered_transactions:
            out_token = [token for token in tx["tokens_out"] if token["symbol"] == symbol][0]
            output.append({
                "timestamp": tx["timestamp"],
                "transaction_address": tx["transaction_address"],
                "amount_usd": tx["amount_usd"],
                "amount_out": out_token["amount_out"],
                "symbol": out_token["symbol"],
                "price_usd": out_token["price_usd"],
                "wallet_category": tx["wallet_category"]
            })

        # Convert output to pandas DataFrame
        df = pd.DataFrame(output)
        df.index = df.index + 1 
        df["date"] = pd.to_datetime(df["timestamp"], unit="s")
        df = df[['date', 'transaction_address', 'amount_usd', 'amount_out', 'price_usd', 'wallet_category']]
        df = df.rename(columns={
            'date': 'Date', 
            'transaction_address': 'Transaction Address', 
            'amount_usd': 'Amount (USD)', 
            'amount_out': 'Amount (Token)', 
            'price_usd': 'Price (USD)', 
            'wallet_category': 'Wallet Category'
        })
        df[['Amount (USD)', 'Amount (Token)']] = df[['Amount (USD)', 'Amount (Token)']].round(decimals=0)
        
        transactions += df.to_dict('records')
        
        time.sleep(0.2)

    # Convert output to pandas DataFrame
    df = pd.DataFrame(output)
    df.index = df.index + 1 
    df["date"] = pd.to_datetime(df["timestamp"], unit="s")
    df = df[['date', 'transaction_address', 'amount_usd', 'amount_out', 'price_usd', 'wallet_category']]
    df = df.rename(columns={
        'date': 'Date', 
        'transaction_address': 'Transaction Address', 
        'amount_usd': 'Amount (USD)', 
        'amount_out': 'Amount (Token)', 
        'price_usd': 'Price (USD)', 
        'wallet_category': 'Wallet Category'
    })
    df[['Amount (USD)', 'Amount (Token)']] = df[['Amount (USD)', 'Amount (Token)']].round(decimals=0)
    return df

st.sidebar.header("Search Criteria")
selected_chain_id = st.sidebar.selectbox("Select a chain ID:", list(chain_ids.keys()), format_func=lambda x: chain_ids[x])
token_address = st.sidebar.text_input("Enter the token address:")
symbol = st.sidebar.text_input("Enter the token symbol:").upper()
time_range = st.sidebar.slider("Enter time range in days:", min_value=1, max_value=30, value=1, step=1, format="%d days")
search_button = st.sidebar.button("Search")
wallet_categories = ['heavy', 'medium', 'casual', 'bot', 'noob']
selected_wallet_categories = st.sidebar.multiselect('Select wallet categories', wallet_categories, default=wallet_categories)





# Create a sidebar container
info_sidebar = st.sidebar.container()

# Add a header to the sidebar
with info_sidebar:
    st.header("Additional Information")

# Add links to the sidebar
with info_sidebar:
    st.write("Check out the following links:")
    st.write("[DexGuru - source of the data](https://dex.guru/)")
    st.write("[Wallet Categories definition & data limitations](https://dexguru.readme.io/docs/)")
    st.write("[Supported DEXes](https://docs.dex.guru/data/supported-dexs)")


if search_button:
    with st.spinner("Searching transactions..."):
        df = get_transactions(selected_chain_id, token_address, symbol, time_range, wallet_categories=selected_wallet_categories)

        day_or_days = 'day' if int(time_range) == 1 else 'days'
    
        if not df.empty:
            from datetime import datetime
            start_time = pd.to_datetime(time.time() - (time_range * 86400), unit="s").strftime("%Y-%m-%d %H:%M:%S")
            end_time = pd.to_datetime(time.time(), unit="s").strftime("%Y-%m-%d %H:%M:%S")
            st.write(f"Chosen period (UTC): {start_time} - {end_time}")
            st.write(f"Total number of buys in the given time period: {len(df)}")
            st.write(df[['Date', 'Transaction Address', 'Amount (USD)', 'Amount (Token)', 'Price (USD)', 'Wallet Category']])
            output = io.BytesIO()
            writer = pd.ExcelWriter(output, engine='xlsxwriter')
            df.to_excel(writer, sheet_name='Sheet1')
            writer.save()
            output.seek(0)
            st.download_button(
                label="Download as Excel",
                data=output,
                file_name=f"{symbol}_transactions.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )

            # Get current token price
            url = f"https://api.dev.dex.guru/v1/chain/{selected_chain_id}/tokens/market?token_addresses={token_address}&sort_by=timestamp&order=desc&limit=1&offset=0"
            headers = {
                "accept": "application/json",
                "api-key": "D5V-7R4r_GQcbwNCbtoT1HVX9wHh5aGkc8g5lWZ8MDg"
            }
            response = requests.get(url, headers=headers)
            data = response.json()
            current_price = data["data"][0]["price_usd"]

            day_or_days = 'day' if int(time_range) == 1 else 'days'
            fig = px.scatter(df, x='Amount (USD)', y='Price (USD)', template='plotly_dark', color='Wallet Category', color_continuous_scale='portland', hover_data={'Date': True, 'Amount (USD)':True, 'Amount (Token)':True,'Price (USD)':True})

            if current_price is not None:
                # Add line for current token price
                fig.add_trace(go.Scatter(x=[df['Amount (USD)'].min(), df['Amount (USD)'].max()], y=[current_price, current_price],mode="lines", line=dict(color="white", width=1, dash="dot"), showlegend=False))

            # Update layout
            num_bins = 20  # Change the number of bins for the y-axis
            num_binsx = 20
            fig.update_layout(
                title=f"{symbol} - buys in the past {time_range} {day_or_days}",  # Modify chart title
                xaxis_title="Money Spent (USD)",
                yaxis_title="Token Price (USD)",
                font=dict(family="Arial", size=15, color="white"),
                coloraxis=dict(colorscale="portland"),
                height=600,
                xaxis=dict(showgrid=False, nticks=num_binsx),
                yaxis=dict(showgrid=False, nticks=num_bins),  # Set the y-axis type to 'log' and number of bins
                legend=dict(font=dict(size=12, color="white"), orientation="h", yanchor="top", y=1, xanchor="left", x=0),
            )
            fig.update_xaxes(tickfont=dict(size=12))
            fig.update_yaxes(tickfont=dict(size=12))

            fig.update_layout(
                legend=dict(
                    orientation="v",
                    yanchor="top",
                    y=1,
                    xanchor="left",
                    x=1.05,
                    font=dict(size=12, color="white"),
                ),
            )

            fig.update_yaxes(tickformat="$.3f")
            fig.update_xaxes(tickformat="%.0f")

            fig.update_layout(
                hoverlabel=dict(
                    bgcolor="white",
                    font_size=12,
                    font_family="Arial",
                    font_color="black",
                    bordercolor="black"
                )
            )
           



            st.plotly_chart(fig, use_container_width=True)
