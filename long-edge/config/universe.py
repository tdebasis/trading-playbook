"""
Stock Universe Configuration

Defines the list of stocks we scan for momentum breakouts.

Last Updated: November 5, 2025
"""

# Current watchlist (23 stocks)
WATCHLIST = [
    # Tech Momentum Leaders (9 stocks)
    # High beta, institutional favorites, AI/cloud/cybersecurity trends
    'NVDA',   # NVIDIA - AI chips
    'TSLA',   # Tesla - EV leader
    'AMD',    # AMD - CPU/GPU competitor
    'PLTR',   # Palantir - AI/Data analytics
    'SNOW',   # Snowflake - Cloud data
    'CRWD',   # CrowdStrike - Cybersecurity
    'NET',    # Cloudflare - Edge computing
    'DDOG',   # Datadog - Monitoring
    'ZS',     # Zscaler - Cloud security

    # Mega-Cap Quality (5 stocks)
    # Stable but capable of 20-40% runs, massive institutional flows
    'AAPL',   # Apple
    'MSFT',   # Microsoft
    'GOOGL',  # Google/Alphabet
    'AMZN',   # Amazon
    'META',   # Meta/Facebook

    # Biotech Volatility (4 stocks)
    # Catalyst-rich (FDA, clinical trials), explosive moves
    'MRNA',   # Moderna - mRNA vaccines
    'BNTX',   # BioNTech - mRNA vaccines
    'SAVA',   # Cassava - Alzheimer's research
    'SGEN',   # Seagen - Cancer therapeutics

    # Fintech & E-commerce (4 stocks)
    # Growth + innovation, retail interest, strong setups
    'SHOP',   # Shopify - E-commerce platform
    'SQ',     # Block (Square) - Payments
    'COIN',   # Coinbase - Crypto exchange
    'RBLX',   # Roblox - Gaming platform

    # Meme/Retail Interest (3 stocks)
    # Extreme momentum when retail piles in
    'GME',    # GameStop
    'AMC',    # AMC Entertainment
    'PTON',   # Peloton
    'SNAP',   # Snap Inc
]

# Alternative watchlists (for testing different universes)

# Tech-only (for testing sector-specific strategy)
TECH_ONLY = [
    'NVDA', 'TSLA', 'AMD', 'PLTR', 'SNOW', 'CRWD', 'NET', 'DDOG', 'ZS',
    'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META'
]

# High volatility only (for aggressive momentum)
HIGH_VOLATILITY = [
    'TSLA', 'PLTR', 'SNOW', 'MRNA', 'BNTX', 'SAVA',
    'GME', 'AMC', 'COIN', 'RBLX'
]

# Mega-caps only (for conservative momentum)
MEGA_CAPS = [
    'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'NVDA', 'TSLA'
]

# Extended universe (for future expansion to 50+ stocks)
EXTENDED_WATCHLIST = WATCHLIST + [
    # Additional tech
    'ADBE',   # Adobe
    'CRM',    # Salesforce
    'NOW',    # ServiceNow
    'PANW',   # Palo Alto Networks
    'OKTA',   # Okta
    'MDB',    # MongoDB
    'TEAM',   # Atlassian

    # Semiconductors
    'AVGO',   # Broadcom
    'QCOM',   # Qualcomm
    'AMAT',   # Applied Materials
    'LRCX',   # Lam Research

    # EV & Clean Energy
    'RIVN',   # Rivian
    'LCID',   # Lucid Motors
    'NIO',    # Nio
    'XPEV',   # XPeng
    'ENPH',   # Enphase Energy

    # Consumer
    'ABNB',   # Airbnb
    'DASH',   # DoorDash
    'UBER',   # Uber
    'LYFT',   # Lyft
    'W',      # Wayfair
    'ETSY',   # Etsy
    'CHWY',   # Chewy

    # Other growth
    'ROKU',   # Roku
    'ZM',     # Zoom
    'DOCU',   # DocuSign
]

# Configuration helpers

def get_universe(name: str = 'default'):
    """
    Get a stock universe by name.

    Args:
        name: 'default', 'tech', 'high_vol', 'mega_caps', 'extended'

    Returns:
        List of stock symbols
    """
    universes = {
        'default': WATCHLIST,
        'tech': TECH_ONLY,
        'high_vol': HIGH_VOLATILITY,
        'mega_caps': MEGA_CAPS,
        'extended': EXTENDED_WATCHLIST,
    }

    return universes.get(name, WATCHLIST)


def get_universe_info():
    """Get information about available universes."""
    return {
        'default': {
            'symbols': WATCHLIST,
            'count': len(WATCHLIST),
            'description': 'Balanced 23-stock universe across sectors'
        },
        'tech': {
            'symbols': TECH_ONLY,
            'count': len(TECH_ONLY),
            'description': 'Tech-focused (no biotech, meme stocks)'
        },
        'high_vol': {
            'symbols': HIGH_VOLATILITY,
            'count': len(HIGH_VOLATILITY),
            'description': 'High volatility stocks only'
        },
        'mega_caps': {
            'symbols': MEGA_CAPS,
            'count': len(MEGA_CAPS),
            'description': 'Mega-cap quality stocks only'
        },
        'extended': {
            'symbols': EXTENDED_WATCHLIST,
            'count': len(EXTENDED_WATCHLIST),
            'description': 'Expanded 50+ stock universe'
        }
    }


if __name__ == "__main__":
    """Print universe information."""
    print("\n" + "="*80)
    print("MOMENTUM HUNTER - STOCK UNIVERSE CONFIGURATION")
    print("="*80 + "\n")

    info = get_universe_info()

    for name, data in info.items():
        print(f"{name.upper()}:")
        print(f"  Count: {data['count']} stocks")
        print(f"  Description: {data['description']}")
        print(f"  Symbols: {', '.join(data['symbols'][:10])}...")
        print()
