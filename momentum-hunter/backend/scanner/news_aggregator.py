"""
News Aggregator - Detects and analyzes market-moving catalysts.

This module fetches real-time news and identifies catalysts that drive momentum:
- Earnings announcements
- FDA approvals
- Mergers & acquisitions
- Analyst upgrades/downgrades
- Breaking news
- SEC filings

Author: Claude AI + Tanam Bam Sinha
"""

from datetime import datetime, timedelta
from typing import List, Dict, Optional, Set
from dataclasses import dataclass
import logging
from alpaca.data.historical import NewsClient
from alpaca.data.requests import NewsRequest

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class NewsItem:
    """A single news article or announcement."""
    headline: str
    summary: str
    source: str
    url: str
    published_at: datetime
    symbols: List[str]

    # Catalyst classification
    catalyst_type: Optional[str] = None  # FDA, earnings, merger, etc.
    sentiment: Optional[str] = None  # bullish, bearish, neutral
    importance: float = 0.0  # 0-10 scale

    def __str__(self):
        catalyst_str = f" [{self.catalyst_type}]" if self.catalyst_type else ""
        return f"{self.headline}{catalyst_str} ({self.source})"


@dataclass
class CatalystAnalysis:
    """Analysis of news catalyst for a stock."""
    symbol: str
    catalyst_type: str  # FDA, earnings, merger, upgrade, news
    catalyst_strength: float  # 1-10, how strong is this catalyst?
    sentiment: str  # bullish, bearish, neutral
    news_items: List[NewsItem]
    analysis_time: datetime

    # Key details
    headline_summary: str
    key_facts: List[str]

    def __str__(self):
        return (
            f"{self.symbol} - {self.catalyst_type.upper()} "
            f"(Strength: {self.catalyst_strength}/10, {self.sentiment})\n"
            f"  {self.headline_summary}"
        )


class NewsAggregator:
    """
    Aggregates and analyzes news from multiple sources.
    """

    # Catalyst keywords for classification
    CATALYST_KEYWORDS = {
        'FDA': [
            'fda approval', 'fda approves', 'fda clears', 'fda panel',
            'drug approval', 'clinical trial', 'phase 3', 'phase 2',
            'orphan drug', 'breakthrough therapy', 'fast track',
            'pdufa', 'biologics license', 'new drug application'
        ],
        'EARNINGS': [
            'earnings', 'quarterly results', 'eps', 'revenue beat',
            'revenue miss', 'guidance raised', 'guidance lowered',
            'quarterly report', 'fiscal quarter', 'profit', 'loss'
        ],
        'MERGER': [
            'merger', 'acquisition', 'acquired', 'buyout', 'takeover',
            'deal', 'agreement to acquire', 'to be acquired',
            'combination', 'joint venture'
        ],
        'UPGRADE': [
            'upgraded', 'upgrade', 'raised price target', 'outperform',
            'buy rating', 'overweight', 'positive outlook'
        ],
        'DOWNGRADE': [
            'downgraded', 'downgrade', 'lowered price target', 'underperform',
            'sell rating', 'underweight', 'negative outlook', 'cut price'
        ],
        'PRODUCT': [
            'product launch', 'new product', 'product release',
            'unveils', 'announces new', 'introduces'
        ],
        'CONTRACT': [
            'contract award', 'wins contract', 'awarded contract',
            'partnership', 'collaboration', 'deal with'
        ],
        'LEGAL': [
            'lawsuit', 'litigation', 'settlement', 'investigation',
            'sec probe', 'regulatory action', 'violation'
        ],
        'EXECUTIVE': [
            'ceo', 'resigns', 'steps down', 'appointed', 'hires',
            'executive', 'management change', 'board'
        ]
    }

    def __init__(self, api_key: str, secret_key: str):
        """
        Initialize news aggregator.

        Args:
            api_key: Alpaca API key
            secret_key: Alpaca secret key
        """
        self.news_client = NewsClient(api_key, secret_key)
        self.api_key = api_key
        self.secret_key = secret_key

        logger.info("News Aggregator initialized")

    def classify_catalyst(self, headline: str, summary: str) -> Optional[str]:
        """
        Classify news into catalyst type.

        Args:
            headline: News headline
            summary: News summary

        Returns:
            Catalyst type or None
        """
        text = (headline + " " + summary).lower()

        # Check each catalyst type
        for catalyst_type, keywords in self.CATALYST_KEYWORDS.items():
            for keyword in keywords:
                if keyword in text:
                    return catalyst_type

        return 'NEWS'  # Generic news

    def assess_sentiment(self, headline: str, summary: str, catalyst_type: str) -> str:
        """
        Determine if news is bullish, bearish, or neutral.

        Args:
            headline: News headline
            summary: News summary
            catalyst_type: Type of catalyst

        Returns:
            Sentiment: 'bullish', 'bearish', or 'neutral'
        """
        text = (headline + " " + summary).lower()

        # Bullish keywords
        bullish_words = [
            'approval', 'beat', 'raised', 'upgrade', 'positive', 'growth',
            'profit', 'gains', 'outperform', 'breakthrough', 'success',
            'awarded', 'wins', 'partnership', 'deal', 'surge', 'rally'
        ]

        # Bearish keywords
        bearish_words = [
            'miss', 'lowered', 'downgrade', 'negative', 'loss', 'declined',
            'underperform', 'failed', 'lawsuit', 'investigation', 'probe',
            'violation', 'resigns', 'plunge', 'crash', 'warning'
        ]

        bullish_score = sum(1 for word in bullish_words if word in text)
        bearish_score = sum(1 for word in bearish_words if word in text)

        # Special case: downgrades/legal are bearish even if some positive words
        if catalyst_type in ['DOWNGRADE', 'LEGAL']:
            return 'bearish'

        # Special case: upgrades/FDA/mergers typically bullish
        if catalyst_type in ['UPGRADE', 'FDA', 'MERGER', 'CONTRACT']:
            return 'bullish'

        if bullish_score > bearish_score:
            return 'bullish'
        elif bearish_score > bullish_score:
            return 'bearish'
        else:
            return 'neutral'

    def calculate_importance(
        self,
        catalyst_type: str,
        sentiment: str,
        headline: str,
        source: str
    ) -> float:
        """
        Calculate importance score (0-10).

        Args:
            catalyst_type: Type of catalyst
            sentiment: Bullish/bearish/neutral
            headline: News headline
            source: News source

        Returns:
            Importance score 0-10
        """
        # Base scores by catalyst type
        base_scores = {
            'FDA': 9.0,      # Huge for biotech
            'MERGER': 8.5,   # Major catalyst
            'EARNINGS': 7.0, # Important but common
            'UPGRADE': 6.0,
            'DOWNGRADE': 6.0,
            'CONTRACT': 7.5,
            'PRODUCT': 6.5,
            'LEGAL': 5.0,
            'EXECUTIVE': 4.0,
            'NEWS': 3.0
        }

        score = base_scores.get(catalyst_type, 3.0)

        # Boost for major sources
        major_sources = ['bloomberg', 'reuters', 'wsj', 'cnbc', 'benzinga']
        if any(source_name in source.lower() for source_name in major_sources):
            score += 1.0

        # Boost for extreme sentiment words
        extreme_words = ['surge', 'crash', 'plunge', 'soar', 'breakthrough']
        if any(word in headline.lower() for word in extreme_words):
            score += 1.0

        return min(score, 10.0)

    def fetch_news_for_symbol(
        self,
        symbol: str,
        hours_back: int = 24
    ) -> List[NewsItem]:
        """
        Fetch recent news for a specific symbol.

        Args:
            symbol: Stock ticker
            hours_back: How many hours of news to fetch

        Returns:
            List of NewsItem objects
        """
        try:
            start = datetime.now() - timedelta(hours=hours_back)

            request = NewsRequest(
                symbols=symbol,
                start=start,
                limit=50  # Get up to 50 recent articles
            )

            news_set = self.news_client.get_news(request)

            news_items = []

            # Access news articles from the data dictionary
            articles = news_set.data.get(symbol, []) if hasattr(news_set, 'data') and isinstance(news_set.data, dict) else list(news_set.data) if hasattr(news_set, 'data') else []

            for article in articles:
                # Classify catalyst
                catalyst_type = self.classify_catalyst(
                    article.headline,
                    article.summary or ""
                )

                # Assess sentiment
                sentiment = self.assess_sentiment(
                    article.headline,
                    article.summary or "",
                    catalyst_type
                )

                # Calculate importance
                importance = self.calculate_importance(
                    catalyst_type,
                    sentiment,
                    article.headline,
                    article.author
                )

                news_item = NewsItem(
                    headline=article.headline,
                    summary=article.summary or "",
                    source=article.author,
                    url=article.url,
                    published_at=article.created_at,
                    symbols=article.symbols,
                    catalyst_type=catalyst_type,
                    sentiment=sentiment,
                    importance=importance
                )

                news_items.append(news_item)

            # Sort by importance
            news_items.sort(key=lambda x: x.importance, reverse=True)

            return news_items

        except Exception as e:
            logger.error(f"Error fetching news for {symbol}: {e}")
            return []

    def analyze_catalyst(self, symbol: str) -> Optional[CatalystAnalysis]:
        """
        Comprehensive catalyst analysis for a symbol.

        Args:
            symbol: Stock ticker

        Returns:
            CatalystAnalysis or None if no significant catalyst
        """
        # Fetch recent news
        news_items = self.fetch_news_for_symbol(symbol, hours_back=24)

        if not news_items:
            return None

        # Get most important news
        top_news = news_items[0]

        # Only create catalyst analysis if importance > 5
        if top_news.importance < 5.0:
            return None

        # Gather all news of same catalyst type
        related_news = [
            item for item in news_items
            if item.catalyst_type == top_news.catalyst_type
        ]

        # Extract key facts from headlines
        key_facts = [item.headline for item in related_news[:3]]

        catalyst = CatalystAnalysis(
            symbol=symbol,
            catalyst_type=top_news.catalyst_type,
            catalyst_strength=top_news.importance,
            sentiment=top_news.sentiment,
            news_items=related_news,
            analysis_time=datetime.now(),
            headline_summary=top_news.headline,
            key_facts=key_facts
        )

        return catalyst

    def get_market_news(self, limit: int = 20) -> List[NewsItem]:
        """
        Get general market news (not symbol-specific).

        Args:
            limit: Number of articles to fetch

        Returns:
            List of recent news items
        """
        try:
            start = datetime.now() - timedelta(hours=4)

            request = NewsRequest(
                start=start,
                limit=limit
            )

            news_set = self.news_client.get_news(request)

            news_items = []

            # Access news articles from the data - NewsSet returns all news in a list
            articles = list(news_set.data) if hasattr(news_set, 'data') else []

            for article in articles:
                catalyst_type = self.classify_catalyst(
                    article.headline,
                    article.summary or ""
                )

                sentiment = self.assess_sentiment(
                    article.headline,
                    article.summary or "",
                    catalyst_type
                )

                importance = self.calculate_importance(
                    catalyst_type,
                    sentiment,
                    article.headline,
                    article.author
                )

                news_item = NewsItem(
                    headline=article.headline,
                    summary=article.summary or "",
                    source=article.author,
                    url=article.url,
                    published_at=article.created_at,
                    symbols=article.symbols,
                    catalyst_type=catalyst_type,
                    sentiment=sentiment,
                    importance=importance
                )

                news_items.append(news_item)

            return news_items

        except Exception as e:
            logger.error(f"Error fetching market news: {e}")
            return []


def main():
    """Test the news aggregator."""
    import os
    from dotenv import load_dotenv

    load_dotenv()

    api_key = os.getenv('ALPACA_API_KEY')
    secret_key = os.getenv('ALPACA_SECRET_KEY')

    aggregator = NewsAggregator(api_key, secret_key)

    print("\n" + "="*80)
    print("MOMENTUM HUNTER - News Aggregator Test")
    print("="*80 + "\n")

    # Test with some popular stocks
    test_symbols = ['NVDA', 'TSLA', 'AAPL', 'NVAX', 'MRNA']

    print("Analyzing catalysts for recent movers...\n")

    for symbol in test_symbols:
        print(f"\n{'='*80}")
        print(f"Checking {symbol}...")
        print('='*80)

        catalyst = aggregator.analyze_catalyst(symbol)

        if catalyst:
            print(f"\n🎯 CATALYST DETECTED:")
            print(f"\n{catalyst}\n")

            print("Recent News:")
            for i, news in enumerate(catalyst.news_items[:3], 1):
                print(f"  {i}. {news.headline}")
                print(f"     {news.source} - {news.published_at.strftime('%Y-%m-%d %H:%M')}")
                print(f"     Sentiment: {news.sentiment}, Importance: {news.importance:.1f}/10")
                print()
        else:
            print("  No significant catalyst detected.\n")

    # Get general market news
    print("\n" + "="*80)
    print("RECENT MARKET NEWS")
    print("="*80 + "\n")

    market_news = aggregator.get_market_news(limit=10)

    for i, news in enumerate(market_news[:10], 1):
        print(f"{i:2}. [{news.catalyst_type}] {news.headline}")
        print(f"    {news.source} - Importance: {news.importance:.1f}/10, {news.sentiment}")
        print()


if __name__ == "__main__":
    main()
