"""
Wheel Strategy Analyzer
Combines data processing with AI prompt engineering for wheel strategy analysis
"""

import boto3
import json
import logging
from typing import Dict, List, Optional, Tuple
import pandas as pd
from datetime import datetime

from ..data.processors.wheel_strategy_processor import WheelStrategyProcessor
from .prompts.financial_prompts import get_wheel_strategy_prompt, get_system_prompt

class WheelStrategyAnalyzer:
    """Analyze stocks for wheel strategy using AI and prompt engineering"""
    
    def __init__(self, aws_region: str = 'us-east-1', data_folder: str = None):
        """
        Initialize the analyzer
        
        Args:
            aws_region: AWS region for Bedrock
            data_folder: Path to wheel strategy data folder
        """
        self.aws_region = aws_region
        self.processor = WheelStrategyProcessor(data_folder)
        self.logger = logging.getLogger(__name__)
        
        # Initialize Bedrock client
        try:
            self.bedrock_client = boto3.client('bedrock-runtime', region_name=aws_region)
        except Exception as e:
            self.logger.error(f"Error initializing Bedrock client: {e}")
            self.bedrock_client = None
    
    def analyze_ticker(self, ticker: str, date: str = None, 
                      analysis_type: str = "analysis") -> Dict:
        """
        Perform complete wheel strategy analysis on a ticker
        
        Args:
            ticker: Stock ticker symbol
            date: Date folder (defaults to latest available)
            analysis_type: Type of analysis ('analysis', 'entry_signals', 'risk_management', 'performance_tracking')
            
        Returns:
            Dictionary with analysis results
        """
        try:
            # Get available dates if none specified
            if not date:
                available_dates = self.processor.get_available_dates()
                if not available_dates:
                    return {'error': 'No data available'}
                date = available_dates[-1]  # Use latest date
            
            # Load ticker data
            df = self.processor.load_ticker_data(ticker, date)
            if df is None:
                return {'error': f'No data found for {ticker} on {date}'}
            
            # Calculate technical indicators
            df_with_indicators = self.processor.calculate_technical_indicators(df)
            
            # Perform suitability analysis
            suitability_analysis = self.processor.analyze_wheel_suitability(df_with_indicators, ticker)
            
            # Prepare text for AI analysis
            analysis_text = self.processor.prepare_analysis_text(suitability_analysis, df_with_indicators)
            
            # Get AI analysis
            ai_analysis = self._get_ai_analysis(analysis_text, analysis_type)
            
            # Combine results
            result = {
                'ticker': ticker,
                'date': date,
                'analysis_type': analysis_type,
                'data_summary': {
                    'total_bars': len(df),
                    'date_range': f"{df['Date'].min().strftime('%Y-%m-%d')} to {df['Date'].max().strftime('%Y-%m-%d')}",
                    'current_price': float(df_with_indicators['VolumeWeightPrice'].iloc[-1])
                },
                'technical_analysis': suitability_analysis,
                'ai_analysis': ai_analysis,
                'timestamp': datetime.now().isoformat()
            }
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error analyzing {ticker}: {e}")
            return {'error': str(e)}
    
    def analyze_multiple_tickers(self, tickers: List[str], date: str = None,
                                analysis_type: str = "analysis") -> List[Dict]:
        """
        Analyze multiple tickers for wheel strategy
        
        Args:
            tickers: List of ticker symbols
            date: Date folder (defaults to latest available)
            analysis_type: Type of analysis
            
        Returns:
            List of analysis results
        """
        results = []
        
        for ticker in tickers:
            try:
                result = self.analyze_ticker(ticker, date, analysis_type)
                results.append(result)
            except Exception as e:
                self.logger.error(f"Error analyzing {ticker}: {e}")
                results.append({
                    'ticker': ticker,
                    'error': str(e)
                })
        
        return results
    
    def get_top_wheel_candidates(self, date: str = None, limit: int = 10,
                                min_volume: int = 10000) -> List[Dict]:
        """
        Find top wheel strategy candidates based on suitability scores
        
        Args:
            date: Date folder (defaults to latest available)
            limit: Maximum number of candidates to return
            min_volume: Minimum average volume requirement
            
        Returns:
            List of top candidates with basic analysis
        """
        try:
            # Get available dates if none specified
            if not date:
                available_dates = self.processor.get_available_dates()
                if not available_dates:
                    return []
                date = available_dates[-1]
            
            # Get sample of tickers to analyze
            sample_tickers = self.processor.get_random_ticker_sample(date, 50)  # Analyze 50 random tickers
            
            candidates = []
            
            for ticker in sample_tickers:
                try:
                    # Load and analyze data
                    df = self.processor.load_ticker_data(ticker, date)
                    if df is None:
                        continue
                    
                    df_with_indicators = self.processor.calculate_technical_indicators(df)
                    analysis = self.processor.analyze_wheel_suitability(df_with_indicators, ticker)
                    
                    # Apply filters
                    if analysis.get('liquidity', {}).get('avg_volume', 0) < min_volume:
                        continue
                    
                    # Extract key metrics for ranking
                    candidate = {
                        'ticker': ticker,
                        'current_price': analysis['price_stats']['current_price'],
                        'suitability_score': analysis['wheel_recommendations']['suitability_score'],
                        'liquidity_score': analysis['liquidity']['liquidity_score'],
                        'volatility_rank': analysis.get('volatility', {}).get('volatility_rank', 'Unknown'),
                        'avg_volume': analysis['liquidity']['avg_volume'],
                        'annualized_volatility': analysis.get('volatility', {}).get('annualized_volatility', 0),
                        'put_strikes': analysis['wheel_recommendations']['put_strikes'],
                        'estimated_premium': analysis['wheel_recommendations']['estimated_premium_pct']
                    }
                    
                    candidates.append(candidate)
                    
                except Exception as e:
                    self.logger.error(f"Error processing {ticker}: {e}")
                    continue
            
            # Sort by suitability score
            score_order = {'Excellent': 4, 'Good': 3, 'Fair': 2, 'Poor': 1, 'Unknown': 0}
            candidates.sort(key=lambda x: (
                score_order.get(x['suitability_score'], 0),
                x['avg_volume']
            ), reverse=True)
            
            return candidates[:limit]
            
        except Exception as e:
            self.logger.error(f"Error finding top candidates: {e}")
            return []
    
    def _get_ai_analysis(self, analysis_text: str, analysis_type: str) -> str:
        """
        Get AI analysis using AWS Bedrock
        
        Args:
            analysis_text: Prepared analysis text
            analysis_type: Type of analysis prompt to use
            
        Returns:
            AI analysis response
        """
        if not self.bedrock_client:
            return "AI analysis unavailable - Bedrock client not initialized"
        
        try:
            # Get appropriate prompt
            system_prompt = get_system_prompt()
            wheel_prompt = get_wheel_strategy_prompt(analysis_type)
            
            # Combine prompts with data
            full_prompt = f"{wheel_prompt}\n\n**STOCK DATA TO ANALYZE:**\n{analysis_text}"
            
            # Prepare request for Nova Pro
            request_body = {
                "messages": [
                    {
                        "role": "user",
                        "content": [{"text": full_prompt}]
                    }
                ],
                "system": [{"text": system_prompt}],
                "inferenceConfig": {
                    "maxTokens": 4000,
                    "temperature": 0.1,
                    "topP": 0.9
                }
            }
            
            # Make API call
            response = self.bedrock_client.invoke_model(
                modelId="amazon.nova-pro-v1:0",
                contentType="application/json",
                accept="application/json",
                body=json.dumps(request_body)
            )
            
            # Parse response
            response_body = json.loads(response['body'].read())
            
            if 'output' in response_body and 'message' in response_body['output']:
                return response_body['output']['message']['content'][0]['text']
            else:
                return "Error: Unexpected response format from AI model"
                
        except Exception as e:
            self.logger.error(f"Error getting AI analysis: {e}")
            return f"AI analysis error: {str(e)}"
    
    def compare_tickers(self, tickers: List[str], date: str = None) -> Dict:
        """
        Compare multiple tickers for wheel strategy suitability
        
        Args:
            tickers: List of ticker symbols to compare
            date: Date folder (defaults to latest available)
            
        Returns:
            Comparison analysis
        """
        try:
            # Analyze all tickers
            analyses = self.analyze_multiple_tickers(tickers, date, "analysis")
            
            # Extract comparison data
            comparison_data = []
            for analysis in analyses:
                if 'error' in analysis:
                    continue
                    
                tech_analysis = analysis.get('technical_analysis', {})
                comparison_data.append({
                    'ticker': analysis['ticker'],
                    'current_price': tech_analysis.get('price_stats', {}).get('current_price', 0),
                    'suitability_score': tech_analysis.get('wheel_recommendations', {}).get('suitability_score', 'Unknown'),
                    'liquidity_score': tech_analysis.get('liquidity', {}).get('liquidity_score', 'Unknown'),
                    'volatility': tech_analysis.get('volatility', {}).get('annualized_volatility', 0),
                    'avg_volume': tech_analysis.get('liquidity', {}).get('avg_volume', 0),
                    'put_10_otm': tech_analysis.get('wheel_recommendations', {}).get('put_strikes', {}).get('10_percent_otm', 0),
                    'estimated_premium_10_otm': tech_analysis.get('wheel_recommendations', {}).get('estimated_premium_pct', {}).get('10_percent_otm', 0)
                })
            
            # Create comparison text for AI
            comparison_text = f"""WHEEL STRATEGY COMPARISON ANALYSIS

**TICKERS BEING COMPARED:** {', '.join(tickers)}

**COMPARISON DATA:**
"""
            
            for data in comparison_data:
                comparison_text += f"""
**{data['ticker']}:**
- Current Price: ${data['current_price']:.2f}
- Suitability Score: {data['suitability_score']}
- Liquidity Score: {data['liquidity_score']}
- Annualized Volatility: {data['volatility']:.1%}
- Average Volume: {data['avg_volume']:,.0f}
- 10% OTM Put Strike: ${data['put_10_otm']:.2f}
- Estimated Premium (10% OTM): {data['estimated_premium_10_otm']:.1%}
"""
            
            # Get AI comparison analysis
            comparison_prompt = """Compare these stocks for wheel strategy implementation. 
            
**COMPARISON ANALYSIS:**

**Rankings:**
- Rank the stocks from best to worst for wheel strategy
- Explain the ranking criteria used

**Key Differences:**
- Highlight the main differences between the stocks
- Identify which stocks are better for different risk profiles

**Portfolio Allocation:**
- Suggest how to allocate capital across these stocks
- Recommend position sizing based on risk levels

**Strategy Recommendations:**
- Provide specific wheel strategy recommendations for each stock
- Suggest which stocks to prioritize and why

**Risk Considerations:**
- Compare the risk profiles of each stock
- Identify potential correlation risks

Provide specific, actionable recommendations."""
            
            ai_comparison = self._get_ai_analysis(comparison_text, "analysis")
            
            return {
                'tickers': tickers,
                'date': date,
                'comparison_data': comparison_data,
                'ai_comparison': ai_comparison,
                'individual_analyses': analyses,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error comparing tickers: {e}")
            return {'error': str(e)}
    
    def get_available_data_info(self) -> Dict:
        """Get information about available data"""
        try:
            dates = self.processor.get_available_dates()
            info = {
                'available_dates': dates,
                'latest_date': dates[-1] if dates else None,
                'total_dates': len(dates)
            }
            
            # Get ticker info for latest date
            if dates:
                latest_date = dates[-1]
                tickers_by_letter = self.processor.get_available_tickers(latest_date)
                
                total_tickers = sum(len(tickers) for tickers in tickers_by_letter.values())
                info['latest_date_info'] = {
                    'date': latest_date,
                    'total_tickers': total_tickers,
                    'tickers_by_letter': {letter: len(tickers) for letter, tickers in tickers_by_letter.items()},
                    'sample_tickers': {
                        letter: tickers[:5] for letter, tickers in tickers_by_letter.items() 
                        if tickers  # Only include letters with tickers
                    }
                }
            
            return info
            
        except Exception as e:
            self.logger.error(f"Error getting data info: {e}")
            return {'error': str(e)}
