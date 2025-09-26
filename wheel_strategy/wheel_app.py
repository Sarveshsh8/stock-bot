"""
Wheel Strategy Analysis Application
Standalone Streamlit app for wheel options strategy analysis
"""

import streamlit as st
import sys
import os
import pandas as pd
from datetime import datetime
import logging
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# Configure logging
logging.basicConfig(level=logging.INFO)

def format_ai_analysis(text):
    """
    Format AI analysis text for better display in Streamlit
    Converts markdown syntax to HTML for proper rendering
    """
    import re
    
    # Split text into lines for processing
    lines = text.split('\n')
    formatted_lines = []
    
    for line in lines:
        # Handle headers with multiple # symbols
        if line.startswith('#### '):
            formatted_lines.append(f'<h4 style="color: #1f77b4; font-weight: bold; margin-top: 15px; margin-bottom: 8px;">{line[5:]}</h4>')
        elif line.startswith('### '):
            formatted_lines.append(f'<h3 style="color: #1f77b4; font-weight: bold; margin-top: 20px; margin-bottom: 10px;">{line[4:]}</h3>')
        elif line.startswith('## '):
            formatted_lines.append(f'<h2 style="color: #1f77b4; font-weight: bold; margin-top: 25px; margin-bottom: 15px;">{line[3:]}</h2>')
        elif line.startswith('# '):
            formatted_lines.append(f'<h1 style="color: #1f77b4; font-weight: bold; margin-top: 30px; margin-bottom: 20px;">{line[2:]}</h1>')
        # Handle lines that end with colon (section headers)
        elif line.strip().endswith(':') and not line.startswith('-') and not line.startswith('*'):
            # Check if it's a bold section header
            if line.strip().startswith('**') and line.strip().endswith('**:'):
                # Extract text between ** and **:
                header_text = line.strip()[2:-3]  # Remove ** from start and **: from end
                formatted_lines.append(f'<h4 style="color: #2e8b57; font-weight: bold; margin-top: 15px; margin-bottom: 8px;">{header_text}:</h4>')
            else:
                # Regular section header
                formatted_lines.append(f'<h4 style="color: #2e8b57; font-weight: bold; margin-top: 15px; margin-bottom: 8px;">{line.strip()}</h4>')
        # Handle bullet points
        elif line.startswith('- '):
            # Process the bullet content for bold text
            bullet_content = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', line[2:])
            formatted_lines.append(f'<li style="margin-left: 20px; margin-bottom: 5px;">{bullet_content}</li>')
        elif line.startswith('  * '):
            bullet_content = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', line[4:])
            formatted_lines.append(f'<li style="margin-left: 40px; margin-bottom: 3px;">{bullet_content}</li>')
        elif line.startswith('  - '):
            bullet_content = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', line[4:])
            formatted_lines.append(f'<li style="margin-left: 40px; margin-bottom: 3px;">{bullet_content}</li>')
        elif line.startswith('* '):
            bullet_content = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', line[2:])
            formatted_lines.append(f'<li style="margin-left: 20px; margin-bottom: 5px;">{bullet_content}</li>')
        # Handle regular text
        else:
            # Replace inline bold text
            formatted_line = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', line)
            # Add line if not empty
            if formatted_line.strip():
                formatted_lines.append(formatted_line)
            else:
                formatted_lines.append('<br>')
    
    # Join lines with line breaks
    formatted_content = '<br>'.join(formatted_lines)
    
    # Wrap in a styled div
    formatted_text = f"""
    <div style="
        background-color: #f8f9fa;
        padding: 20px;
        border-radius: 10px;
        border-left: 5px solid #007bff;
        color: #212529;
        font-size: 14px;
        line-height: 1.6;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    ">
        {formatted_content}
    </div>
    """
    
    return formatted_text

def main():
    """Main application function"""
    
    # Page configuration
    st.set_page_config(
        page_title="Wheel Strategy Analyzer",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Header
    st.title("Wheel Strategy Analyzer")
    st.markdown("**AI-Powered Options Wheel Strategy**")
    st.markdown("---")
    
    # Initialize analyzer
    if 'wheel_analyzer' not in st.session_state:
        try:
            from ai.wheel_analyzer import WheelStrategyAnalyzer
            st.session_state.wheel_analyzer = WheelStrategyAnalyzer()
            st.session_state.wheel_data_info = st.session_state.wheel_analyzer.get_available_data_info()
        except Exception as e:
            st.error(f"Error initializing wheel strategy analyzer: {str(e)}")
            st.session_state.wheel_analyzer = None
            st.stop()
    
    if st.session_state.wheel_analyzer:
        # Sidebar - Data Information
        with st.sidebar:
            st.header("Data Overview")
            
            if st.session_state.wheel_data_info and 'error' not in st.session_state.wheel_data_info:
                info = st.session_state.wheel_data_info
                
                st.metric("Available Dates", info.get('total_dates', 0))
                st.metric("Latest Date", info.get('latest_date', 'N/A'))
                
                if 'latest_date_info' in info:
                    st.metric("Total Tickers", info['latest_date_info'].get('total_tickers', 0))
                    
                    # Sample tickers
                    with st.expander("Sample Tickers", expanded=False):
                        sample_tickers = info['latest_date_info'].get('sample_tickers', {})
                        for letter, tickers in sample_tickers.items():
                            if tickers:
                                st.write(f"**{letter}:** {', '.join(tickers[:3])}")
            else:
                st.error("No data available")
                st.stop()
            
            # Refresh data
            if st.button("Refresh Data"):
                st.session_state.wheel_data_info = st.session_state.wheel_analyzer.get_available_data_info()
                st.rerun()
        
        # Main content area
        analysis_option = st.selectbox(
            "Choose Analysis Type:",
            ["Single Ticker Analysis", "Compare Multiple Tickers", "Find Top Candidates", "Custom Analysis"],
            index=0
        )
        
        if analysis_option == "Single Ticker Analysis":
            single_ticker_analysis()
        elif analysis_option == "Compare Multiple Tickers":
            compare_multiple_tickers()
        elif analysis_option == "Find Top Candidates":
            find_top_candidates()
        elif analysis_option == "Custom Analysis":
            custom_analysis()

def single_ticker_analysis():
    """Single ticker analysis interface"""
    st.subheader("Single Ticker Analysis")
    st.markdown("Perform detailed wheel strategy analysis on a specific stock")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        ticker = st.text_input("Enter Ticker Symbol:", placeholder="e.g., AAPL, MSFT, TSLA").upper()
    
    with col2:
        analysis_type = st.selectbox(
            "Analysis Type:",
            ["analysis", "entry_signals", "risk_management", "performance_tracking"],
            format_func=lambda x: {
                "analysis": "General Analysis",
                "entry_signals": "Entry Signals",
                "risk_management": "Risk Management", 
                "performance_tracking": "Performance Tracking"
            }[x]
        )
    
    if st.button("Analyze Ticker", type="primary") and ticker:
        with st.spinner(f"Analyzing {ticker} for wheel strategy..."):
            try:
                result = st.session_state.wheel_analyzer.analyze_ticker(ticker, analysis_type=analysis_type)
                
                if 'error' in result:
                    st.error(f"Error: {result['error']}")
                else:
                    display_single_ticker_results(result)
                    
            except Exception as e:
                st.error(f"Analysis error: {str(e)}")

def display_single_ticker_results(result):
    """Display results for single ticker analysis"""
    st.success(f"Analysis completed for {result['ticker']}")
    
    # Metrics row
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Current Price", f"${result['data_summary']['current_price']:.2f}")
    with col2:
        st.metric("Data Points", result['data_summary']['total_bars'])
    with col3:
        suitability = result.get('technical_analysis', {}).get('wheel_recommendations', {}).get('suitability_score', 'Unknown')
        st.metric("Suitability", suitability)
    with col4:
        st.metric("Date Range", result['data_summary']['date_range'])
    
    # Technical analysis summary
    if 'technical_analysis' in result:
        tech = result['technical_analysis']
        
        st.markdown("### Technical Summary")
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Liquidity & Volume**")
            if 'liquidity' in tech:
                st.write(f"• Liquidity Score: **{tech['liquidity'].get('liquidity_score', 'N/A')}**")
                st.write(f"• Avg Volume: **{tech['liquidity'].get('avg_volume', 0):,.0f}**")
                st.write(f"• Total Trades: **{tech['liquidity'].get('total_trades', 0):,}**")
            
            if 'wheel_recommendations' in tech and 'put_strikes' in tech['wheel_recommendations']:
                st.markdown("**Put Strike Recommendations**")
                strikes = tech['wheel_recommendations']['put_strikes']
                st.write(f"• 5% OTM: **${strikes.get('5_percent_otm', 0):.2f}**")
                st.write(f"• 10% OTM: **${strikes.get('10_percent_otm', 0):.2f}**")
                st.write(f"• 15% OTM: **${strikes.get('15_percent_otm', 0):.2f}**")
        
        with col2:
            st.markdown("**Volatility & Risk**")
            if 'volatility' in tech:
                st.write(f"• Volatility Rank: **{tech['volatility'].get('volatility_rank', 'N/A')}**")
                st.write(f"• Ann. Volatility: **{tech['volatility'].get('annualized_volatility', 0):.1%}**")
                st.write(f"• Daily Range %: **{tech['volatility'].get('avg_daily_range_pct', 0):.2f}%**")
            
            if 'wheel_recommendations' in tech and 'estimated_premium_pct' in tech['wheel_recommendations']:
                st.markdown("**Premium Estimates**")
                premium = tech['wheel_recommendations']['estimated_premium_pct']
                st.write(f"• 5% OTM: **{premium.get('5_percent_otm', 0):.1%}**")
                st.write(f"• 10% OTM: **{premium.get('10_percent_otm', 0):.1%}**")
                st.write(f"• 15% OTM: **{premium.get('15_percent_otm', 0):.1%}**")
    
    # AI Analysis
    st.markdown("### AI Analysis")
    if 'ai_analysis' in result:
        # Process the AI analysis text to format it properly
        formatted_analysis = format_ai_analysis(result['ai_analysis'])
        st.markdown(formatted_analysis, unsafe_allow_html=True)

def compare_multiple_tickers():
    """Multiple ticker comparison interface"""
    st.subheader("Compare Multiple Tickers")
    st.markdown("Compare multiple stocks for wheel strategy suitability")
    
    # Input for multiple tickers
    tickers_input = st.text_input(
        "Enter Ticker Symbols (comma-separated):",
        placeholder="e.g., AAPL, MSFT, TSLA, SPY"
    )
    
    if st.button("Compare Tickers", type="primary") and tickers_input:
        tickers = [t.strip().upper() for t in tickers_input.split(',') if t.strip()]
        
        if len(tickers) > 5:
            st.warning("Limiting comparison to first 5 tickers for performance")
            tickers = tickers[:5]
        
        with st.spinner(f"Comparing {len(tickers)} tickers..."):
            try:
                comparison = st.session_state.wheel_analyzer.compare_tickers(tickers)
                
                if 'error' in comparison:
                    st.error(f"Error: {comparison['error']}")
                else:
                    display_comparison_results(comparison)
                    
            except Exception as e:
                st.error(f"Comparison error: {str(e)}")

def display_comparison_results(comparison):
    """Display comparison results"""
    st.success("Comparison completed!")
    
    # Display comparison table
    if 'comparison_data' in comparison and comparison['comparison_data']:
        df = pd.DataFrame(comparison['comparison_data'])
        
        # Format the dataframe for display
        display_df = df.copy()
        display_df['current_price'] = display_df['current_price'].apply(lambda x: f"${x:.2f}")
        display_df['avg_volume'] = display_df['avg_volume'].apply(lambda x: f"{x:,.0f}")
        display_df['volatility'] = display_df['volatility'].apply(lambda x: f"{x:.1%}")
        display_df['put_10_otm'] = display_df['put_10_otm'].apply(lambda x: f"${x:.2f}")
        display_df['estimated_premium_10_otm'] = display_df['estimated_premium_10_otm'].apply(lambda x: f"{x:.1%}")
        
        # Rename columns for display
        display_df.columns = [
            'Ticker', 'Current Price', 'Suitability', 'Liquidity', 
            'Volatility', 'Avg Volume', '10% OTM Put', 'Est. Premium'
        ]
        
        st.markdown("### Comparison Table")
        st.dataframe(display_df, use_container_width=True)
    
    # AI Comparison Analysis
    if 'ai_comparison' in comparison:
        st.markdown("### AI Comparison Analysis")
        # Process the AI comparison text to format it properly
        formatted_comparison = format_ai_analysis(comparison['ai_comparison'])
        st.markdown(formatted_comparison, unsafe_allow_html=True)

def find_top_candidates():
    """Find top candidates interface"""
    st.subheader("Find Top Candidates")
    st.markdown("Automatically find the best wheel strategy opportunities")
    
    col1, col2 = st.columns(2)
    with col1:
        limit = st.number_input("Number of candidates:", min_value=5, max_value=20, value=10)
    with col2:
        min_volume = st.number_input("Minimum avg volume:", min_value=1000, max_value=100000, value=10000, step=1000)
    
    if st.button("Find Top Candidates", type="primary"):
        with st.spinner("Analyzing candidates..."):
            try:
                candidates = st.session_state.wheel_analyzer.get_top_wheel_candidates(
                    limit=limit, min_volume=min_volume
                )
                
                if candidates:
                    display_top_candidates(candidates)
                else:
                    st.warning("No candidates found matching the criteria")
                    
            except Exception as e:
                st.error(f"Error finding candidates: {str(e)}")

def display_top_candidates(candidates):
    """Display top candidates results"""
    st.success(f"Found {len(candidates)} candidates")
    
    # Create dataframe for display
    df = pd.DataFrame(candidates)
    
    # Format for display
    display_df = df.copy()
    display_df['current_price'] = display_df['current_price'].apply(lambda x: f"${x:.2f}")
    display_df['avg_volume'] = display_df['avg_volume'].apply(lambda x: f"{x:,.0f}")
    display_df['annualized_volatility'] = display_df['annualized_volatility'].apply(lambda x: f"{x:.1%}")
    
    # Select columns for display
    display_cols = ['ticker', 'current_price', 'suitability_score', 'liquidity_score', 
                  'volatility_rank', 'avg_volume', 'annualized_volatility']
    display_df = display_df[display_cols]
    
    # Rename columns
    display_df.columns = ['Ticker', 'Price', 'Suitability', 'Liquidity', 
                        'Vol Rank', 'Avg Volume', 'Ann. Volatility']
    
    st.dataframe(display_df, use_container_width=True)
    
    # Show top 3 with more details
    st.markdown("### Top 3 Candidates Details")
    for i, candidate in enumerate(candidates[:3]):
        with st.expander(f"{i+1}. {candidate['ticker']} - {candidate['suitability_score']}", expanded=i==0):
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**Basic Info**")
                st.write(f"Current Price: **${candidate['current_price']:.2f}**")
                st.write(f"Suitability: **{candidate['suitability_score']}**")
                st.write(f"Liquidity: **{candidate['liquidity_score']}**")
            
            with col2:
                st.markdown("**Risk Metrics**")
                st.write(f"Volatility: **{candidate['volatility_rank']}**")
                st.write(f"Avg Volume: **{candidate['avg_volume']:,.0f}**")
                st.write(f"Ann. Vol: **{candidate['annualized_volatility']:.1%}**")
            
            # Put strike recommendations
            strikes = candidate['put_strikes']
            st.markdown("**Suggested Put Strikes:**")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("5% OTM", f"${strikes['5_percent_otm']:.2f}")
            with col2:
                st.metric("10% OTM", f"${strikes['10_percent_otm']:.2f}")
            with col3:
                st.metric("15% OTM", f"${strikes['15_percent_otm']:.2f}")

def custom_analysis():
    """Custom analysis interface"""
    st.subheader("Custom Analysis")
    st.markdown("Enter any ticker for quick or detailed analysis")
    
    col1, col2 = st.columns([2, 1])
    with col1:
        custom_ticker = st.text_input("Enter ticker symbol:", placeholder="e.g., NVDA").upper()
    with col2:
        if st.button("Quick Analysis") and custom_ticker:
            with st.spinner(f"Quick analysis for {custom_ticker}..."):
                try:
                    # Get just the technical analysis without full AI processing for speed
                    df = st.session_state.wheel_analyzer.processor.load_ticker_data(custom_ticker, None)
                    if df is not None:
                        df_with_indicators = st.session_state.wheel_analyzer.processor.calculate_technical_indicators(df)
                        analysis = st.session_state.wheel_analyzer.processor.analyze_wheel_suitability(df_with_indicators, custom_ticker)
                        
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Current Price", f"${analysis['price_stats']['current_price']:.2f}")
                        with col2:
                            st.metric("Suitability", analysis['wheel_recommendations']['suitability_score'])
                        with col3:
                            st.metric("Liquidity", analysis['liquidity']['liquidity_score'])
                        
                        # Quick recommendations
                        strikes = analysis['wheel_recommendations']['put_strikes']
                        st.markdown("**Quick Put Strike Suggestions:**")
                        st.write(f"• Conservative (5% OTM): **${strikes['5_percent_otm']:.2f}**")
                        st.write(f"• Moderate (10% OTM): **${strikes['10_percent_otm']:.2f}**")
                        st.write(f"• Aggressive (15% OTM): **${strikes['15_percent_otm']:.2f}**")
                    else:
                        st.error(f"No data found for {custom_ticker}")
                except Exception as e:
                    st.error(f"Error: {str(e)}")
    
    # Full custom analysis
    if custom_ticker:
        st.markdown("---")
        if st.button(f"Full AI Analysis for {custom_ticker}", type="primary"):
            with st.spinner("Performing full AI analysis..."):
                try:
                    result = st.session_state.wheel_analyzer.analyze_ticker(custom_ticker)
                    
                    if 'error' in result:
                        st.error(f"Error: {result['error']}")
                    else:
                        st.success("Full analysis completed!")
                        display_single_ticker_results(result)
                except Exception as e:
                    st.error(f"Error: {str(e)}")

if __name__ == "__main__":
    main()
