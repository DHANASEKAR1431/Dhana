
import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import pandas as pd
import google.generativeai as genai
import mimetypes
import os

# Configure Gemini API
API_KEY = "AIzaSyApvQuWPjhmk8kbJ2RbQPrcz4wmQH5iIm0"  # Replace with your API key
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel("models/gemini-1.5-flash")

# System prompt for Gemini AI
system_prompt = """
You are a trading bot. Follow these structured steps to analyze the image for:
- Bullish Engulfing
- Bearish Engulfing
- Bullish Pinbar
- Bearish Pinbar
- Hammer
- Inverted Hammer
- Bullish & Bearish Inside Bar patterns

Provide their locations and explanations.

1. Identify Features: Examine the image to identify key candlestick features (e.g., body size, wick length, relative position to surrounding candles).
2. Evaluate Context: Assess the sequence of candlesticks to find relationships.
3. Classify Patterns: Match the detected features to known candlestick patterns.
4. Document Results: For each detected pattern:
    - Specify the pattern type.
    - Provide the exact location (index or timestamp range).
    - Explain why it matches the criteria.
"""

# UI Header
st.title("📊 Live & Historical Candlestick Pattern Detector")

# Sidebar Inputs
st.sidebar.header("Stock Ticker & Time Parameters")
ticker = st.sidebar.text_input("Enter Stock Ticker (e.g., AAPL, TSLA, BTC-USD):", "AAPL")
interval = st.sidebar.selectbox("Select Time Interval", ["1m", "2m", "5m", "15m", "30m", "1h", "1d"], index=3)
data_type = st.sidebar.radio("Select Data Type", ["Live Data", "Historical Data"])
start_date = st.sidebar.date_input("Start Date", value=pd.to_datetime("2024-01-01"))
end_date = st.sidebar.date_input("End Date", value=pd.to_datetime("today"))

# Validate date range
if start_date > end_date:
    st.sidebar.error("Start date must be before end date!")

# Function to fetch live data
def get_live_data(ticker, interval):
    period_mapping = {
        "1m": "1d",  
        "2m": "1d",  
        "5m": "5d",  
        "15m": "7d",  
        "30m": "14d",  
        "1h": "30d",  
        "1d": "90d"   
    }
    period = period_mapping.get(interval, "1d")  
    stock = yf.Ticker(ticker)
    df = stock.history(interval=interval, period=period)
    return df

# Function to fetch historical data
def get_historical_data(ticker, start_date, end_date):
    stock = yf.Ticker(ticker)
    df = stock.history(start=start_date, end=end_date)
    return df

# Function to generate candlestick chart
def generate_candlestick_chart(df, ticker):
    fig = go.Figure(data=[go.Candlestick(
        x=df.index,
        open=df["Open"],
        high=df["High"],
        low=df["Low"],
        close=df["Close"],
    )])
    fig.update_layout(title=f"{ticker} Candlestick Chart", xaxis_title="Time", yaxis_title="Price")
    return fig

# Function to save the candlestick chart as an image
def save_chart_as_image(fig, img_path="temp_candlestick_chart.png"):
    # Save the plot to an image file (PNG format)
    fig.write_image(img_path)
    return img_path

# Function to generate explanations for detected patterns
def explain_pattern(pattern_type, date): #if gemini breaks or unavailable the app can still run with buid in pattern recognation
    explanations = {
        "Bullish Engulfing": "A strong bullish reversal pattern. The green candle completely engulfs the previous red candle, signaling a potential uptrend.",
        "Bearish Engulfing": "A strong bearish reversal pattern. The red candle completely engulfs the previous green candle, signaling a potential downtrend.",
        "Bullish Pinbar": "A bullish reversal pattern. A long lower wick suggests rejection of lower prices and potential upward movement.",
        "Bearish Pinbar": "A bearish reversal pattern. A long upper wick suggests rejection of higher prices and potential downward movement.",
        "Hammer": "A bullish reversal signal at the bottom of a downtrend. The long lower wick indicates strong buying pressure.",
        "Inverted Hammer": "A potential bullish reversal signal. The long upper wick suggests a failed attempt to push prices lower.",
        "Bullish Inside Bar": "A bullish continuation pattern. The small candle inside the previous candle suggests consolidation before a breakout.",
        "Bearish Inside Bar": "A bearish continuation pattern. The small candle inside the previous candle suggests consolidation before a breakdown."
    }
    return f"📌 **{pattern_type} at {date}**: {explanations.get(pattern_type, 'Pattern explanation not available.')}"
 
# Function to analyze candlestick patterns using logic
def analyze_patterns(df):   #if gemini breaks or unavailable the app can still run with buid in pattern recognation
    patterns = []
    for i in range(1, len(df)):
        date = df.index[i].strftime('%Y-%m-%d')
 
        # Bullish Engulfing
        if df['Close'][i] > df['Open'][i] and df['Close'][i-1] < df['Open'][i-1] and df['Close'][i] > df['Open'][i-1] and df['Open'][i] < df['Close'][i-1]:
            patterns.append(explain_pattern("Bullish Engulfing", date))
 
        # Bearish Engulfing
        elif df['Close'][i] < df['Open'][i] and df['Close'][i-1] > df['Open'][i-1] and df['Close'][i] < df['Open'][i-1] and df['Open'][i] > df['Close'][i-1]:
            patterns.append(explain_pattern("Bearish Engulfing", date))
 
        # Bullish Pinbar
        elif df['Close'][i] > df['Open'][i] and (df['High'][i] - df['Close'][i]) > 2 * (df['Close'][i] - df['Open'][i]):
            patterns.append(explain_pattern("Bullish Pinbar", date))
 
        # Bearish Pinbar
        elif df['Close'][i] < df['Open'][i] and (df['High'][i] - df['Open'][i]) > 2 * (df['Open'][i] - df['Close'][i]):
            patterns.append(explain_pattern("Bearish Pinbar", date))
 
        # Hammer
        elif (df['Close'][i] > df['Open'][i]) and (df['Low'][i] < df['Open'][i] - (df['Close'][i] - df['Open'][i]) * 2):
            patterns.append(explain_pattern("Hammer", date))
 
        # Inverted Hammer
        elif (df['Close'][i] > df['Open'][i]) and (df['High'][i] > df['Close'][i] + (df['Close'][i] - df['Open'][i]) * 2):
            patterns.append(explain_pattern("Inverted Hammer", date))
 
        # Bullish Inside Bar
        elif df['Open'][i] > df['Open'][i-1] and df['Close'][i] < df['Close'][i-1]:
            patterns.append(explain_pattern("Bullish Inside Bar", date))
 
        # Bearish Inside Bar
        elif df['Open'][i] < df['Open'][i-1] and df['Close'][i] > df['Close'][i-1]:
            patterns.append(explain_pattern("Bearish Inside Bar", date))
 
    return patterns

# Function to send image to Gemini API and analyze
def gemini_analyze_image(img_path, system_prompt):
    mime_type, _ = mimetypes.guess_type(img_path)
    if mime_type is None:
        mime_type = "image/png"  # Default to PNG if mime type cannot be detected
    
    with open(img_path, "rb") as img_file:
        image_data = img_file.read()

    file_info = [{"mime_type": mime_type, "data": image_data}]
    
    try:
        response = model.generate_content([system_prompt, file_info[0]])
        return response.text  # Return the response from Gemini
    except Exception as e:
        st.error(f"Error with Gemini API: {str(e)}")
        return None

# Process on button click
if st.sidebar.button("Generate & Analyze Candlestick Chart"):
    if data_type == "Live Data":
        df_live = get_live_data(ticker, interval)
        st.write(f"### 📈 Live Data (Interval: {interval})")
        if not df_live.empty:
            # Generate the chart for live data
            fig_live = generate_candlestick_chart(df_live, ticker)
            st.plotly_chart(fig_live)

            # Save chart as an image
            img_path = save_chart_as_image(fig_live)

            # Analyze patterns using Gemini
            output = gemini_analyze_image(img_path, system_prompt)
            if output:
                st.write("### 📊 Gemini Model Output:")
                st.markdown(output)
            else:
                st.write("⚠️ No patterns detected by Gemini.")
                
            # Remove the temporary image file after use
            os.remove(img_path)
        else:
            st.error("⚠️ No live data available for this interval.")
    
    else:  # Historical Data
        df_historical = get_historical_data(ticker, start_date, end_date)
        st.write(f"### 📈 Historical Data (From {start_date} to {end_date})")
        if not df_historical.empty:
            # Generate the chart for historical data
            fig_historical = generate_candlestick_chart(df_historical, ticker)
            st.plotly_chart(fig_historical)

            # Save chart as an image
            img_path = save_chart_as_image(fig_historical)

            # Analyze patterns using Gemini
            output = gemini_analyze_image(img_path, system_prompt)
            if output:
                st.write("### 📊 Gemini Model Output:")
                st.markdown(output)
            else:
                st.write("⚠️ No patterns detected by Gemini.")
            
            # Remove the temporary image file after use
            os.remove(img_path)
        else:
            st.error("⚠️ No historical data available for this range.")
