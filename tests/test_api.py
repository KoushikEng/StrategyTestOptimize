from main import run_backtest
from optimize import run_optimization

if __name__ == '__main__':
    print("Testing API Usage...")

    # Test Backtest
    print("\n[1] Testing run_backtest with SBIN (with download)...")
    try:
        results = run_backtest(symbols=['SBIN'], strategy_name='SimpleMACross', interval='15', download=True)
        print("Backtest Results:", results)
        assert len(results) > 0
    except Exception as e:
        print("Backtest Failed:", e)
        import traceback
        traceback.print_exc()
        
    # Test Optimization
    print("\n[2] Testing run_optimization with SBIN...")
    try:
        # Use very small gen/pop for speed check
        results = run_optimization(symbol='SBIN', strategy_name='SimpleMACross', interval='15', pop=7, gen=1)
        if results:
            print("Optimization Results (Top 1):", results[0])
        else:
            print("Optimization Results: None generated (likely constraints or limits)")
            
        assert len(results) > 0 # Optimization might fail to find good params in 1 gen, but should return list
    except Exception as e:
        print("Optimization Failed:", e)
        import traceback
        traceback.print_exc()
