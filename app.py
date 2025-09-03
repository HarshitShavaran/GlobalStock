import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from datetime import datetime, timedelta
import io
import requests

# Configure page
st.set_page_config(
    page_title="Stock Analysis Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better dark theme integration
st.markdown("""
<style>
    .metric-card {
        background-color: #262730;
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #404040;
    }
    .stDownloadButton > button {
        background-color: #00ff41;
        color: #0e1117;
        border: none;
        font-weight: bold;
    }
    .stDownloadButton > button:hover {
        background-color: #00cc33;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_data(ttl=3600)  # Cache for 1 hour
def get_usd_to_inr_rate():
    """Get current USD to INR exchange rate"""
    try:
        # Using Yahoo Finance to get USD/INR rate
        ticker = yf.Ticker("USDINR=X")
        data = ticker.history(period="1d")
        if not data.empty:
            return data['Close'].iloc[-1]
        else:
            # Fallback rate if API fails
            return 83.0
    except:
        # Fallback rate if API fails
        return 83.0

def validate_stock_symbol(symbol):
    """Validate if the stock symbol exists and has data"""
    if not symbol or len(symbol.strip()) == 0:
        return False, "Please enter a stock symbol"
    
    try:
        ticker = yf.Ticker(symbol.upper())
        info = ticker.info
        if not info or 'regularMarketPrice' not in info:
            return False, f"No data found for symbol '{symbol}'. Please check the symbol and try again."
        return True, ""
    except Exception as e:
        return False, f"Error validating symbol '{symbol}': {str(e)}"

def fetch_stock_data(symbol, period="1y"):
    """Fetch stock data from Yahoo Finance"""
    try:
        ticker = yf.Ticker(symbol.upper())
        
        # Get historical data
        hist_data = ticker.history(period=period)
        if hist_data.empty:
            return None, None, f"No historical data found for {symbol}"
        
        # Get company info
        info = ticker.info
        
        return hist_data, info, None
    except Exception as e:
        return None, None, f"Error fetching data for {symbol}: {str(e)}"

def get_currency_symbol(symbol, convert_to_inr=False):
    """Get appropriate currency symbol based on stock symbol and conversion preference"""
    if convert_to_inr:
        return "₹"
    
    # Indian stocks
    if symbol.endswith('.NS') or symbol.endswith('.BO'):
        return "₹"
    # Japanese stocks
    elif symbol.endswith('.T'):
        return "¥"
    # UK stocks
    elif symbol.endswith('.L'):
        return "£"
    # European stocks
    elif symbol.endswith('.DE') or symbol.endswith('.PA') or symbol.endswith('.AS'):
        return "€"
    # Canadian stocks
    elif symbol.endswith('.TO'):
        return "C$"
    # Australian stocks
    elif symbol.endswith('.AX'):
        return "A$"
    # South Korean stocks
    elif symbol.endswith('.KS'):
        return "₩"
    # Brazilian stocks
    elif symbol.endswith('.SA'):
        return "R$"
    # Russian stocks
    elif symbol.endswith('.ME'):
        return "₽"
    # Default to USD
    else:
        return "$"

def format_number(value, format_type="currency", currency_symbol="$", convert_to_inr=False, usd_to_inr_rate=83.0, is_indian_stock=False):
    """Format numbers for display"""
    if pd.isna(value) or value is None:
        return "N/A"
    
    try:
        # Convert USD to INR if requested and it's not already an Indian stock
        if convert_to_inr and not is_indian_stock and currency_symbol == "$":
            value = value * usd_to_inr_rate
            currency_symbol = "₹"
        
        if format_type == "currency":
            if value >= 1e12:
                return f"{currency_symbol}{value/1e12:.2f}T"
            elif value >= 1e9:
                return f"{currency_symbol}{value/1e9:.2f}B"
            elif value >= 1e6:
                return f"{currency_symbol}{value/1e6:.2f}M"
            elif value >= 1e3:
                return f"{currency_symbol}{value/1e3:.2f}K"
            else:
                return f"{currency_symbol}{value:.2f}"
        elif format_type == "number":
            if value >= 1e12:
                return f"{value/1e12:.2f}T"
            elif value >= 1e9:
                return f"{value/1e9:.2f}B"
            elif value >= 1e6:
                return f"{value/1e6:.2f}M"
            elif value >= 1e3:
                return f"{value/1e3:.2f}K"
            else:
                return f"{value:.2f}"
        elif format_type == "percentage":
            return f"{value:.2f}%" if value else "N/A"
        else:
            return str(value)
    except:
        return "N/A"

def create_price_chart(hist_data, symbol):
    """Create interactive price and volume charts"""
    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.05,
        subplot_titles=(f'{symbol} Stock Price', 'Volume'),
        row_heights=[0.7, 0.3]
    )
    
    # Price candlestick chart
    fig.add_trace(
        go.Candlestick(
            x=hist_data.index,
            open=hist_data['Open'],
            high=hist_data['High'],
            low=hist_data['Low'],
            close=hist_data['Close'],
            name='Price',
            increasing_line_color='#00ff41',
            decreasing_line_color='#ff4b4b',
            increasing_fillcolor='#00ff41',
            decreasing_fillcolor='#ff4b4b'
        ),
        row=1, col=1
    )
    
    # Volume chart
    colors = ['#00ff41' if close >= open else '#ff4b4b' 
              for close, open in zip(hist_data['Close'], hist_data['Open'])]
    
    fig.add_trace(
        go.Bar(
            x=hist_data.index,
            y=hist_data['Volume'],
            name='Volume',
            marker_color=colors,
            opacity=0.7
        ),
        row=2, col=1
    )
    
    # Update layout for dark theme
    fig.update_layout(
        template='plotly_dark',
        height=600,
        showlegend=False,
        xaxis_rangeslider_visible=False,
        paper_bgcolor='#0e1117',
        plot_bgcolor='#0e1117',
        font=dict(color='#fafafa')
    )
    
    # Update x-axes
    fig.update_xaxes(
        gridcolor='#404040',
        linecolor='#404040'
    )
    
    # Update y-axes
    fig.update_yaxes(
        gridcolor='#404040',
        linecolor='#404040'
    )
    
    return fig

def create_metrics_table(info, hist_data, symbol, convert_to_inr=False, usd_to_inr_rate=83.0):
    """Create a comprehensive metrics table"""
    current_price = hist_data['Close'].iloc[-1] if not hist_data.empty else info.get('regularMarketPrice', 0)
    
    # Get appropriate currency symbol
    currency_symbol = get_currency_symbol(symbol, convert_to_inr)
    is_indian_stock = symbol.endswith('.NS') or symbol.endswith('.BO')
    
    metrics_data = {
        'Metric': [
            'Current Price',
            'Market Cap',
            'Volume (Avg)',
            'P/E Ratio',
            'EPS',
            'Dividend Yield',
            '52W High',
            '52W Low',
            'Beta',
            'Revenue',
            'Profit Margins',
            'Book Value',
            'Price to Book',
            'Forward P/E',
            'PEG Ratio'
        ],
        'Value': [
            format_number(current_price, currency_symbol=currency_symbol, convert_to_inr=convert_to_inr, usd_to_inr_rate=usd_to_inr_rate, is_indian_stock=is_indian_stock),
            format_number(info.get('marketCap'), 'currency', currency_symbol, convert_to_inr, usd_to_inr_rate, is_indian_stock),
            format_number(info.get('averageVolume'), 'number'),
            format_number(info.get('trailingPE')),
            format_number(info.get('trailingEps'), currency_symbol=currency_symbol, convert_to_inr=convert_to_inr, usd_to_inr_rate=usd_to_inr_rate, is_indian_stock=is_indian_stock),
            format_number(info.get('dividendYield', 0) * 100 if info.get('dividendYield') else 0, 'percentage'),
            format_number(info.get('fiftyTwoWeekHigh'), currency_symbol=currency_symbol, convert_to_inr=convert_to_inr, usd_to_inr_rate=usd_to_inr_rate, is_indian_stock=is_indian_stock),
            format_number(info.get('fiftyTwoWeekLow'), currency_symbol=currency_symbol, convert_to_inr=convert_to_inr, usd_to_inr_rate=usd_to_inr_rate, is_indian_stock=is_indian_stock),
            format_number(info.get('beta')),
            format_number(info.get('totalRevenue'), 'currency', currency_symbol, convert_to_inr, usd_to_inr_rate, is_indian_stock),
            format_number(info.get('profitMargins', 0) * 100 if info.get('profitMargins') else 0, 'percentage'),
            format_number(info.get('bookValue'), currency_symbol=currency_symbol, convert_to_inr=convert_to_inr, usd_to_inr_rate=usd_to_inr_rate, is_indian_stock=is_indian_stock),
            format_number(info.get('priceToBook')),
            format_number(info.get('forwardPE')),
            format_number(info.get('pegRatio'))
        ]
    }
    
    return pd.DataFrame(metrics_data)

def convert_df_to_csv(df):
    """Convert dataframe to CSV for download"""
    output = io.StringIO()
    df.to_csv(output, index=False)
    return output.getvalue().encode('utf-8')

# Main app
def main():
    st.title("📈 Stock Analysis Dashboard")
    st.markdown("### Comprehensive financial analysis with real-time data from Yahoo Finance")
    
    # Sidebar for controls
    with st.sidebar:
        st.header("📊 Controls")
        
        # Stock symbol input
        symbol = st.text_input(
            "Stock Symbol",
            placeholder="e.g., AAPL, RELIANCE.NS, TCS.NS",
            help="Enter a valid stock ticker symbol. For Indian stocks, use .NS (NSE) or .BO (BSE) suffix"
        ).upper().strip()
        
        # Country and stock selection
        st.markdown("**🌍 Select by Country & Company:**")
        
        # Define popular stocks by country
        country_stocks = {
            "🇺🇸 United States": {
                "AAPL": "Apple Inc.",
                "GOOGL": "Alphabet Inc.",
                "MSFT": "Microsoft Corporation",
                "AMZN": "Amazon.com Inc.",
                "TSLA": "Tesla Inc.",
                "META": "Meta Platforms Inc.",
                "NVDA": "NVIDIA Corporation",
                "JPM": "JPMorgan Chase & Co."
            },
            "🇮🇳 India": {
                "RELIANCE.NS": "Reliance Industries",
                "TCS.NS": "Tata Consultancy Services", 
                "INFY.NS": "Infosys",
                "HDFCBANK.NS": "HDFC Bank",
                "ICICIBANK.NS": "ICICI Bank",
                "ITC.NS": "ITC Limited",
                "SBIN.NS": "State Bank of India",
                "BHARTIARTL.NS": "Bharti Airtel"
            },
            "🇯🇵 Japan": {
                "7203.T": "Toyota Motor Corporation",
                "6758.T": "Sony Group Corporation",
                "9984.T": "SoftBank Group Corp.",
                "8306.T": "Mitsubishi UFJ Financial",
                "6861.T": "Keyence Corporation",
                "9434.T": "SoftBank Corp.",
                "8035.T": "Tokyo Electron Limited",
                "4689.T": "LY Corporation"
            },
            "🇬🇧 United Kingdom": {
                "SHEL.L": "Shell plc",
                "AZN.L": "AstraZeneca PLC",
                "BP.L": "BP p.l.c.",
                "ULVR.L": "Unilever PLC",
                "RIO.L": "Rio Tinto Group",
                "HSBA.L": "HSBC Holdings plc",
                "VOD.L": "Vodafone Group Plc",
                "GSK.L": "GSK plc"
            },
            "🇩🇪 Germany": {
                "SAP.DE": "SAP SE",
                "ASME.DE": "ASML Holding N.V.",
                "SIE.DE": "Siemens AG",
                "MBG.DE": "Mercedes-Benz Group AG",
                "ALV.DE": "Allianz SE",
                "BAS.DE": "BASF SE",
                "BMW.DE": "Bayerische Motoren Werke AG",
                "DTE.DE": "Deutsche Telekom AG"
            },
            "🇫🇷 France": {
                "MC.PA": "LVMH Moët Hennessy",
                "OR.PA": "L'Oréal S.A.",
                "ASML.AS": "ASML Holding N.V.",
                "TTE.PA": "TotalEnergies SE",
                "SAN.PA": "Sanofi",
                "BNP.PA": "BNP Paribas",
                "AIR.PA": "Airbus SE",
                "RMS.PA": "Hermès International"
            },
            "🇨🇦 Canada": {
                "SHOP.TO": "Shopify Inc.",
                "CNQ.TO": "Canadian Natural Resources",
                "RY.TO": "Royal Bank of Canada",
                "TD.TO": "The Toronto-Dominion Bank",
                "BNS.TO": "The Bank of Nova Scotia",
                "ENB.TO": "Enbridge Inc.",
                "SU.TO": "Suncor Energy Inc.",
                "CP.TO": "Canadian Pacific Railway"
            },
            "🇦🇺 Australia": {
                "CBA.AX": "Commonwealth Bank of Australia",
                "BHP.AX": "BHP Group Limited",
                "CSL.AX": "CSL Limited",
                "WBC.AX": "Westpac Banking Corporation",
                "ANZ.AX": "Australia and New Zealand Banking",
                "NAB.AX": "National Australia Bank",
                "FMG.AX": "Fortescue Metals Group",
                "RIO.AX": "Rio Tinto Limited"
            },
            "🇰🇷 South Korea": {
                "005930.KS": "Samsung Electronics Co.",
                "000660.KS": "SK Hynix Inc.",
                "035420.KS": "NAVER Corporation",
                "051910.KS": "LG Chem Ltd.",
                "006400.KS": "Samsung SDI Co.",
                "035720.KS": "Kakao Corp.",
                "003670.KS": "Korea Mobile Game Corp.",
                "028260.KS": "Samsung C&T Corporation"
            },
            "🇧🇷 Brazil": {
                "VALE3.SA": "Vale S.A.",
                "PETR4.SA": "Petróleo Brasileiro S.A.",
                "ITUB4.SA": "Itaú Unibanco Holding S.A.",
                "BBDC4.SA": "Banco Bradesco S.A.",
                "ABEV3.SA": "Ambev S.A.",
                "B3SA3.SA": "B3 S.A.",
                "WEGE3.SA": "WEG S.A.",
                "MGLU3.SA": "Magazine Luiza S.A."
            },
            "🇷🇺 Russia": {
                "GAZP.ME": "Gazprom",
                "SBER.ME": "Sberbank",
                "LKOH.ME": "Lukoil",
                "ROSN.ME": "Rosneft",
                "NVTK.ME": "Novatek",
                "GMKN.ME": "Norilsk Nickel",
                "MTSS.ME": "Mobile TeleSystems",
                "YNDX.ME": "Yandex"
            }
        }
        
        selected_country = st.selectbox(
            "Select Country",
            options=["Choose a country..."] + list(country_stocks.keys())
        )
        
        if selected_country != "Choose a country...":
            stocks = country_stocks[selected_country]
            selected_stock = st.selectbox(
                f"Select Company from {selected_country}",
                options=["Choose a company..."] + list(stocks.keys()),
                format_func=lambda x: f"{x} - {stocks.get(x, '')}" if x in stocks else x
            )
            
            if selected_stock != "Choose a company...":
                symbol = selected_stock
        
        # Period selection
        period_options = {
            "1 Month": "1mo",
            "3 Months": "3mo", 
            "6 Months": "6mo",
            "1 Year": "1y",
            "2 Years": "2y",
            "5 Years": "5y"
        }
        
        selected_period = st.selectbox(
            "Time Period",
            options=list(period_options.keys()),
            index=3  # Default to 1 year
        )
        
        period = period_options[selected_period]
        
        # Currency display option
        st.markdown("**💱 Currency Display:**")
        show_in_inr = st.checkbox(
            "Show all prices in INR (₹)",
            help="Convert USD prices to Indian Rupees for easier comparison"
        )
        
        analyze_button = st.button("🔍 Analyze Stock", type="primary", use_container_width=True)
    
    # Main content area
    if analyze_button or symbol:
        if not symbol:
            st.error("⚠️ Please enter a stock symbol to get started.")
            return
        
        # Validate symbol
        is_valid, error_msg = validate_stock_symbol(symbol)
        if not is_valid:
            st.error(f"❌ {error_msg}")
            return
        
        # Show loading spinner
        with st.spinner(f"📡 Fetching data for {symbol}..."):
            hist_data, info, error = fetch_stock_data(symbol, period)
            if show_in_inr:
                usd_to_inr_rate = get_usd_to_inr_rate()
            else:
                usd_to_inr_rate = 1.0
        
        if error:
            st.error(f"❌ {error}")
            return
        
        if hist_data is None or hist_data.empty:
            st.error(f"❌ No data available for {symbol}")
            return
        
        # Company header
        company_name = info.get('longName', symbol) if info else symbol
        sector = info.get('sector', 'N/A') if info else 'N/A'
        industry = info.get('industry', 'N/A') if info else 'N/A'
        
        st.header(f"{company_name} ({symbol})")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Sector", sector)
        with col2:
            st.metric("Industry", industry)
        with col3:
            current_price = hist_data['Close'].iloc[-1]
            prev_close = info.get('previousClose', hist_data['Close'].iloc[-2] if len(hist_data) > 1 else current_price) if info else (hist_data['Close'].iloc[-2] if len(hist_data) > 1 else current_price)
            price_change = current_price - prev_close
            price_change_pct = (price_change / prev_close) * 100 if prev_close != 0 else 0
            
            # Get appropriate currency symbol and convert if needed
            is_indian_stock = symbol.endswith('.NS') or symbol.endswith('.BO')
            currency_symbol = get_currency_symbol(symbol, show_in_inr)
            
            if show_in_inr and not is_indian_stock:
                display_price = current_price * usd_to_inr_rate
                display_change = price_change * usd_to_inr_rate
            else:
                display_price = current_price
                display_change = price_change
            
            st.metric(
                "Current Price", 
                f"{currency_symbol}{display_price:.2f}",
                f"{display_change:+.2f} ({price_change_pct:+.2f}%)"
            )
        
        # Interactive Charts
        st.subheader("📈 Price & Volume Analysis")
        
        try:
            chart = create_price_chart(hist_data, symbol)
            st.plotly_chart(chart, use_container_width=True)
        except Exception as e:
            st.error(f"Error creating chart: {str(e)}")
        
        # Financial Metrics Table
        st.subheader("💼 Financial Metrics")
        
        try:
            metrics_df = create_metrics_table(info, hist_data, symbol, show_in_inr, usd_to_inr_rate if show_in_inr else 1.0)
            
            # Display metrics in a nice format
            col1, col2 = st.columns(2)
            
            mid_point = len(metrics_df) // 2
            
            with col1:
                st.dataframe(
                    metrics_df.iloc[:mid_point], 
                    hide_index=True,
                    use_container_width=True
                )
            
            with col2:
                st.dataframe(
                    metrics_df.iloc[mid_point:], 
                    hide_index=True,
                    use_container_width=True
                )
            
            # CSV Download
            st.subheader("📥 Export Data")
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Download metrics
                metrics_csv = convert_df_to_csv(metrics_df)
                st.download_button(
                    label="📊 Download Metrics as CSV",
                    data=metrics_csv,
                    file_name=f"{symbol}_metrics_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv",
                    use_container_width=True
                )
            
            with col2:
                # Download historical data
                hist_csv = convert_df_to_csv(hist_data.reset_index())
                st.download_button(
                    label="📈 Download Historical Data as CSV",
                    data=hist_csv,
                    file_name=f"{symbol}_historical_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv",
                    use_container_width=True
                )
                
        except Exception as e:
            st.error(f"Error creating metrics table: {str(e)}")
        
        # Additional Information
        if info and info.get('longBusinessSummary'):
            with st.expander("📋 Company Summary"):
                st.write(info['longBusinessSummary'])
    
    else:
        # Welcome screen
        st.info("👋 Welcome! Enter a stock symbol in the sidebar to begin your analysis.")
        
        st.markdown("""
        ### Features:
        - 📊 **Real-time stock data** from Yahoo Finance
        - 📈 **Interactive charts** with candlestick patterns and volume
        - 💼 **Comprehensive financial metrics** including P/E, market cap, and more  
        - 📥 **CSV export** functionality for data analysis
        - 🌙 **Dark theme** optimized for extended viewing
        - 📱 **Responsive design** for all devices
        
        ### How to use:
        1. Enter a stock ticker symbol manually **OR**
        2. Select from country dropdown and choose a company
        3. Choose your preferred time period
        4. Optionally enable INR conversion for easier comparison
        5. Click "Analyze Stock" to fetch and display data
        6. Explore interactive charts and download data as needed
        
        ### Supported Global Markets:
        - 🇺🇸 **United States:** NYSE, NASDAQ (e.g., AAPL, GOOGL)
        - 🇮🇳 **India:** NSE (.NS), BSE (.BO) (e.g., RELIANCE.NS, TCS.NS)
        - 🇯🇵 **Japan:** Tokyo Stock Exchange (.T) (e.g., 7203.T, 6758.T)
        - 🇬🇧 **United Kingdom:** London Stock Exchange (.L) (e.g., SHEL.L, AZN.L)
        - 🇩🇪 **Germany:** Frankfurt Stock Exchange (.DE) (e.g., SAP.DE, SIE.DE)
        - 🇫🇷 **France:** Euronext Paris (.PA) (e.g., MC.PA, OR.PA)
        - 🇨🇦 **Canada:** Toronto Stock Exchange (.TO) (e.g., SHOP.TO, RY.TO)
        - 🇦🇺 **Australia:** Australian Securities Exchange (.AX) (e.g., CBA.AX, BHP.AX)
        - 🇰🇷 **South Korea:** Korea Exchange (.KS) (e.g., 005930.KS)
        - 🇧🇷 **Brazil:** B3 (.SA) (e.g., VALE3.SA, PETR4.SA)
        - 🇷🇺 **Russia:** Moscow Exchange (.ME) (e.g., GAZP.ME, SBER.ME)
        """)
        
        st.markdown("---")
        st.markdown("*Powered by Yahoo Finance API | Built with Streamlit & Plotly*")

if __name__ == "__main__":
    main()
