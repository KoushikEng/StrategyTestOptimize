"""
Strategy Reviewer Agent

The "Hostile Critic" that validates backtest results for sanity and robustness.
This agent REJECTS strategies that show signs of:
- Overfitting
- Data leakage
- Insufficient sample size
- Unrealistic performance
"""

from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass


@dataclass
class ReviewResult:
    """Result of strategy review."""
    passed: bool
    score: float  # 0-100
    issues: List[str]
    warnings: List[str]
    recommendations: List[str]


def review_strategy(
    results: List[List],  # Output from run_backtest
    min_trades: int = 30,
    max_win_rate: float = 0.95,
    min_sharpe: float = 0.1,
    max_drawdown: float = -0.50,
) -> ReviewResult:
    """
    Review backtest results for sanity and robustness.
    
    Args:
        results: List of [symbol, net_profit, win_rate, sharpe, sortino, max_dd, trades]
        min_trades: Minimum trades required for validity
        max_win_rate: Maximum allowed win rate (higher = suspicious)
        min_sharpe: Minimum Sharpe ratio
        max_drawdown: Maximum allowed drawdown (negative value)
        
    Returns:
        ReviewResult with pass/fail and detailed feedback
    """
    issues = []
    warnings = []
    recommendations = []
    
    if not results:
        return ReviewResult(
            passed=False,
            score=0,
            issues=["No results to review"],
            warnings=[],
            recommendations=["Ensure data is available and strategy generates trades"]
        )
    
    # Aggregate metrics across symbols
    total_trades = sum(r[6] for r in results)
    avg_profit = sum(r[1] for r in results) / len(results)
    avg_win_rate = sum(r[2] for r in results) / len(results) / 100  # Convert from %
    avg_sharpe = sum(r[3] for r in results) / len(results)
    avg_sortino = sum(r[4] for r in results) / len(results)
    worst_dd = min(r[5] for r in results) / 100  # Convert from %, already negative
    
    # === HARD GATES ===
    
    # 1. Minimum trades check
    if total_trades < min_trades:
        issues.append(f"Insufficient trades: {total_trades} < {min_trades} minimum")
    
    # 2. Suspiciously high win rate (data leak / curve fitting)
    if avg_win_rate > max_win_rate:
        issues.append(f"Suspicious win rate: {avg_win_rate:.1%} > {max_win_rate:.0%} (likely overfitting)")
    
    # 3. 100% win rate = almost certainly a bug
    if avg_win_rate >= 1.0:
        issues.append("100% win rate detected - this is almost always a data leak or bug")
    
    # 4. Zero trades = strategy not triggering
    if total_trades == 0:
        issues.append("Zero trades executed - strategy conditions never met")
    
    # 5. Excessive drawdown
    if worst_dd < max_drawdown:
        issues.append(f"Excessive drawdown: {worst_dd:.1%} worse than {max_drawdown:.0%} limit")
    
    # === SOFT CHECKS (Warnings) ===
    
    # Low Sharpe ratio
    if avg_sharpe < min_sharpe:
        warnings.append(f"Low Sharpe ratio: {avg_sharpe:.2f} < {min_sharpe} (poor risk-adjusted returns)")
    
    # Negative Sortino
    if avg_sortino < 0:
        warnings.append(f"Negative Sortino ratio: {avg_sortino:.2f} (losing money on average)")
    
    # Low trade count (but above minimum)
    if min_trades <= total_trades < min_trades * 2:
        warnings.append(f"Borderline trade count: {total_trades} (consider more data)")
    
    # === RECOMMENDATIONS ===
    
    if avg_sharpe > 0 and avg_sharpe < 0.5:
        recommendations.append("Consider adjusting parameters - returns are positive but not compelling")
    
    if total_trades > 500:
        recommendations.append("High trade count - consider higher timeframe for longer-term signals")
    
    # === SCORING ===
    
    score = 100.0
    
    # Deduct points for issues (critical)
    score -= len(issues) * 30
    
    # Deduct points for warnings (moderate)
    score -= len(warnings) * 10
    
    # Bonus for good metrics
    if avg_sharpe > 1.0:
        score += 10
    if avg_win_rate > 0.5 and avg_win_rate < 0.7:
        score += 5  # Healthy win rate range
    if worst_dd > -0.20:
        score += 10  # Low drawdown
    
    # Clamp score
    score = max(0, min(100, score))
    
    # Pass if no critical issues
    passed = len(issues) == 0 and score >= 50
    
    return ReviewResult(
        passed=passed,
        score=score,
        issues=issues,
        warnings=warnings,
        recommendations=recommendations
    )


def format_review(review: ReviewResult) -> str:
    """Format review result for display."""
    lines = []
    
    status = "✅ PASSED" if review.passed else "❌ REJECTED"
    lines.append(f"Strategy Review: {status}")
    lines.append(f"Score: {review.score:.0f}/100")
    lines.append("")
    
    if review.issues:
        lines.append("🚨 Critical Issues:")
        for issue in review.issues:
            lines.append(f"  - {issue}")
        lines.append("")
    
    if review.warnings:
        lines.append("⚠️ Warnings:")
        for warning in review.warnings:
            lines.append(f"  - {warning}")
        lines.append("")
    
    if review.recommendations:
        lines.append("💡 Recommendations:")
        for rec in review.recommendations:
            lines.append(f"  - {rec}")
    
    return "\n".join(lines)


# Example / Testing
if __name__ == "__main__":
    # Simulate some backtest results
    # [symbol, net_profit, win_rate, sharpe, sortino, max_dd, trades]
    
    # Good strategy
    good_results = [
        ["SBIN", 15.5, 55.0, 0.8, 0.6, -12.3, 45],
        ["RELIANCE", 12.3, 52.0, 0.7, 0.5, -15.1, 38],
    ]
    
    # Bad strategy (too few trades, high win rate)
    bad_results = [
        ["SBIN", 100.0, 100.0, 2.5, 2.0, -5.0, 5],
    ]
    
    print("=== Good Strategy ===")
    review = review_strategy(good_results)
    print(format_review(review))
    
    print("\n=== Bad Strategy ===")
    review = review_strategy(bad_results)
    print(format_review(review))
