from calculate.indicators import calculate_rsi
import numpy as np

if __name__ == "__main__":
    prices = np.random.randint(10, 100, size=100)

    print(prices)
    rsi = calculate_rsi(prices)
    print(rsi)
