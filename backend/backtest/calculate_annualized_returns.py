"""
Calculate Annualized Returns and ROI Projections

Takes the quarterly results from our validated strategy and projects:
1. Annualized compound return
2. Expected return on $10k investment over 1 year
3. Best/worst case scenarios based on observed volatility
"""

import json
from pathlib import Path

def calculate_compound_annual_return(quarterly_returns):
    """
    Calculate compound annual growth rate (CAGR) from quarterly returns.

    CAGR = (End Value / Start Value) ^ (1 / Years) - 1

    For quarterly returns:
    - Each quarter's return compounds on the previous
    - Annualize by raising to (4 quarters / number of quarters tested)
    """

    # Convert percentages to multipliers (5% = 1.05)
    multipliers = [1 + (r / 100) for r in quarterly_returns]

    # Compound the returns
    compound_multiplier = 1.0
    for m in multipliers:
        compound_multiplier *= m

    # Number of quarters tested
    num_quarters = len(quarterly_returns)

    # Annualize (4 quarters per year)
    years = num_quarters / 4
    annual_multiplier = compound_multiplier ** (1 / years)
    annual_return_pct = (annual_multiplier - 1) * 100

    return annual_return_pct, compound_multiplier


def main():
    print("\n" + "="*80)
    print("ANNUALIZED RETURN CALCULATION - VALIDATED STRATEGY")
    print("="*80 + "\n")

    # All tested periods (seen + unseen)
    all_results = {
        'Q1 2024': +5.80,
        'Q2 2024': -0.71,
        'Q3 2024': +0.75,   # Unseen (validation)
        'Q4 2024': +17.69,  # Unseen (validation)
        'Q2 2025': -1.43,
        'Q3 2025': +6.50,
    }

    print("Quarterly Returns:")
    print("-" * 80)
    for period, ret in all_results.items():
        print(f"  {period}: {ret:>+8.2f}%")

    quarterly_returns = list(all_results.values())
    avg_quarterly = sum(quarterly_returns) / len(quarterly_returns)

    print("-" * 80)
    print(f"  Average per quarter: {avg_quarterly:>+8.2f}%")
    print()

    # Calculate compound annual return
    annual_return, compound_multiplier = calculate_compound_annual_return(quarterly_returns)

    print("="*80)
    print("ANNUALIZED PERFORMANCE")
    print("="*80 + "\n")

    print(f"Compound Annual Growth Rate (CAGR): {annual_return:+.2f}%")
    print()

    # Calculate $10k projections
    starting_capital = 10000

    print("$10,000 Investment Projections:")
    print("-" * 80)

    # Year 1
    year1_value = starting_capital * (1 + annual_return / 100)
    year1_profit = year1_value - starting_capital
    print(f"After 1 year:  ${year1_value:>10,.2f} (profit: ${year1_profit:>+8,.2f})")

    # Year 2
    year2_value = year1_value * (1 + annual_return / 100)
    year2_profit = year2_value - starting_capital
    print(f"After 2 years: ${year2_value:>10,.2f} (profit: ${year2_profit:>+8,.2f})")

    # Year 3
    year3_value = year2_value * (1 + annual_return / 100)
    year3_profit = year3_value - starting_capital
    print(f"After 3 years: ${year3_value:>10,.2f} (profit: ${year3_profit:>+8,.2f})")

    print()

    # Quarterly breakdown
    print("="*80)
    print("QUARTERLY COMPOUNDING EXAMPLE (Starting with $10,000)")
    print("="*80 + "\n")

    capital = starting_capital
    print(f"Starting capital: ${capital:,.2f}\n")

    for period, ret in all_results.items():
        profit = capital * (ret / 100)
        capital += profit
        print(f"{period}: {ret:>+6.2f}% → ${capital:>10,.2f} (quarter profit: ${profit:>+8,.2f})")

    total_profit = capital - starting_capital
    total_return_pct = ((capital - starting_capital) / starting_capital) * 100

    print("-" * 80)
    print(f"Final value: ${capital:,.2f}")
    print(f"Total profit: ${total_profit:>+,.2f}")
    print(f"Total return: {total_return_pct:>+.2f}% over {len(all_results)} quarters")
    print()

    # Volatility analysis
    print("="*80)
    print("RISK ANALYSIS")
    print("="*80 + "\n")

    # Calculate standard deviation of quarterly returns
    mean_return = sum(quarterly_returns) / len(quarterly_returns)
    variance = sum((r - mean_return) ** 2 for r in quarterly_returns) / len(quarterly_returns)
    std_dev = variance ** 0.5

    print(f"Quarterly Return Statistics:")
    print(f"  Mean: {mean_return:>+.2f}%")
    print(f"  Std Dev: {std_dev:>.2f}%")
    print(f"  Best quarter: {max(quarterly_returns):>+.2f}%")
    print(f"  Worst quarter: {min(quarterly_returns):>+.2f}%")
    print()

    # Sharpe-like ratio (assuming 0% risk-free rate for simplicity)
    sharpe_like = mean_return / std_dev if std_dev > 0 else 0
    print(f"Return/Risk Ratio: {sharpe_like:.2f}")
    print()

    # Scenario analysis
    print("="*80)
    print("SCENARIO ANALYSIS (1 Year / 4 Quarters)")
    print("="*80 + "\n")

    # Best case: Average + 1 std dev
    best_case_quarterly = mean_return + std_dev
    best_case_annual = ((1 + best_case_quarterly/100) ** 4 - 1) * 100
    best_case_value = starting_capital * (1 + best_case_annual / 100)

    # Expected case: Average
    expected_annual = ((1 + mean_return/100) ** 4 - 1) * 100
    expected_value = starting_capital * (1 + expected_annual / 100)

    # Worst case: Average - 1 std dev
    worst_case_quarterly = mean_return - std_dev
    worst_case_annual = ((1 + worst_case_quarterly/100) ** 4 - 1) * 100
    worst_case_value = starting_capital * (1 + worst_case_annual / 100)

    print(f"Best Case (Mean + 1σ):     {best_case_annual:>+7.2f}% → ${best_case_value:>10,.2f}")
    print(f"Expected Case (Mean):      {expected_annual:>+7.2f}% → ${expected_value:>10,.2f}")
    print(f"Worst Case (Mean - 1σ):    {worst_case_annual:>+7.2f}% → ${worst_case_value:>10,.2f}")
    print()

    # Win/loss analysis
    positive_quarters = sum(1 for r in quarterly_returns if r > 0)
    negative_quarters = len(quarterly_returns) - positive_quarters

    print("="*80)
    print("WIN/LOSS STATISTICS")
    print("="*80 + "\n")

    print(f"Positive quarters: {positive_quarters}/{len(quarterly_returns)} ({positive_quarters/len(quarterly_returns)*100:.0f}%)")
    print(f"Negative quarters: {negative_quarters}/{len(quarterly_returns)} ({negative_quarters/len(quarterly_returns)*100:.0f}%)")
    print()

    avg_positive = sum(r for r in quarterly_returns if r > 0) / positive_quarters if positive_quarters > 0 else 0
    avg_negative = sum(r for r in quarterly_returns if r < 0) / negative_quarters if negative_quarters > 0 else 0

    print(f"Average winning quarter: {avg_positive:>+.2f}%")
    print(f"Average losing quarter: {avg_negative:>+.2f}%")

    if avg_negative != 0:
        profit_factor = abs(avg_positive / avg_negative)
        print(f"Profit factor (win/loss ratio): {profit_factor:.2f}x")

    print()

    # Comparison to benchmarks
    print("="*80)
    print("BENCHMARK COMPARISON")
    print("="*80 + "\n")

    # Typical market returns
    spy_annual = 10.0  # S&P 500 historical average
    spy_value = starting_capital * (1 + spy_annual / 100)

    print("Investment performance comparison (1 year on $10k):")
    print(f"  This Strategy:  {annual_return:>+7.2f}% → ${year1_value:>10,.2f}")
    print(f"  S&P 500 (avg):  {spy_annual:>+7.2f}% → ${spy_value:>10,.2f}")
    print()

    outperformance = annual_return - spy_annual
    if outperformance > 0:
        print(f"✅ Strategy outperforms S&P 500 by {outperformance:+.2f}% annually")
    else:
        print(f"❌ Strategy underperforms S&P 500 by {abs(outperformance):.2f}% annually")

    print()

    # Save results
    output = {
        'quarterly_returns': all_results,
        'average_quarterly_return': avg_quarterly,
        'annualized_return_cagr': annual_return,
        'starting_capital': starting_capital,
        'year1_value': year1_value,
        'year1_profit': year1_profit,
        'volatility_std_dev': std_dev,
        'best_case_annual': best_case_annual,
        'expected_annual': expected_annual,
        'worst_case_annual': worst_case_annual,
        'positive_quarters': positive_quarters,
        'total_quarters': len(quarterly_returns),
        'outperformance_vs_spy': outperformance,
    }

    output_file = Path(__file__).parent.parent.parent / "annualized_returns.json"
    with open(output_file, 'w') as f:
        json.dump(output, f, indent=2)

    print(f"📊 Results saved to: {output_file}")
    print("\n" + "="*80 + "\n")

    # Final summary
    print("="*80)
    print("EXECUTIVE SUMMARY")
    print("="*80 + "\n")

    print(f"Starting with $10,000:")
    print(f"  • Expected return after 1 year: ${year1_value:,.2f} ({annual_return:+.2f}%)")
    print(f"  • Quarterly volatility: {std_dev:.2f}%")
    print(f"  • Positive quarters: {positive_quarters}/{len(quarterly_returns)} ({positive_quarters/len(quarterly_returns)*100:.0f}%)")
    print(f"  • Profit factor: {profit_factor:.2f}x")
    print(f"  • Outperformance vs S&P 500: {outperformance:+.2f}%")
    print()

    if annual_return > 15:
        print("✅ EXCELLENT: Strategy shows strong returns with acceptable risk")
    elif annual_return > 10:
        print("✅ GOOD: Strategy beats market averages")
    elif annual_return > 5:
        print("⚠️  MODEST: Strategy shows positive but modest returns")
    else:
        print("⚠️  WEAK: Strategy needs further optimization")

    print()


if __name__ == "__main__":
    main()
