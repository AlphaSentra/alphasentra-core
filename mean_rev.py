"""
Project:     Alphagora Trading System
File:        mean_rev.py
Author:      Daiviet Huynh
Created:     2025-07-22
License:     MIT License
Repository:  https://github.com/daivieth/Alphagora

Description:
Mean-reversion strategy to achieve asymmetrical returns.
"""
from datetime import datetime, timedelta
import yfinance as yf
import numpy as np
from pykalman import KalmanFilter

# --- CONFIGURATION ---

# 2. Mean-Reversion Engine Configuration
PAIRS = {
    'Gold_vs_Miners': ('GLD', 'GDX'),
    'Miners_vs_Gold': ('GDX', 'GLD'),
    'Indices_Long_Short': ('SPY', 'SH'),
    'Short_vs_Indices': ('SH', 'SPY')
}
PAIRS_ALLOCATION = 0.25
PAIRS_LOOKBACK_YEARS = 5  # Years of data for Kalman Filter initialization


# --- MEAN-REVERSION (PAIRS TRADING) ENGINE ---

def mean_reversion_engine():
    """
    Main function to run the mean-reversion engine.
    """
    print("\n" + "=" * 100)
    print(f"\n--- Mean-Reversion Engine ({PAIRS_ALLOCATION:.0%} Allocation) ---")
    print("Strategy: Kalman Filter-based pairs trading reviewed daily.")

    for pair_name, (y_ticker, x_ticker) in PAIRS.items():
        trader = KalmanPairsTrader(y_ticker, x_ticker)
        trader.get_pairs_recommendations()

        print("\n" + " ") 

class KalmanPairsTrader:
    """
    Manages the pairs trading logic for a single pair using a Kalman Filter.
    """

    def __init__(self, dependent_etf, independent_etf):
        self.y_ticker = dependent_etf
        self.x_ticker = independent_etf
        self.kf = None
        self.latest_state_mean = None
        self.latest_state_cov = None

    def _initialize_kalman_filter(self, y_prices, x_prices):
        """
        Initializes and fits the Kalman Filter on historical data.
        """
        obs_mat = np.vstack([x_prices, np.ones(len(x_prices))]).T[:, np.newaxis, :]

        self.kf = KalmanFilter(
            n_dim_state=2,
            n_dim_obs=1,
            initial_state_mean=np.zeros(2),
            initial_state_covariance=np.ones((2, 2)),
            transition_matrices=np.eye(2),
            observation_matrices=obs_mat,
            observation_covariance=1.0,
            transition_covariance=np.full((2, 2), 0.0001)
        )

        self.latest_state_mean, self.latest_state_cov = self.kf.filter(y_prices.values)

    def get_pairs_recommendations(self):
        """
        Calculates and prints recommendations for the pairs trading sleeve.
        """
        pair_name = f"{self.y_ticker}/{self.x_ticker}"
        print(f"\n--- Pairs Trading Analysis: {pair_name} ---\n")

        try:
            end_date = datetime.today()
            start_date = end_date - timedelta(days=365 * PAIRS_LOOKBACK_YEARS)

            full_data_hist = yf.download(
                [self.y_ticker, self.x_ticker],
                start=start_date,
                end=end_date,
                progress=True,
                auto_adjust=True
            )
            if full_data_hist.empty:
                print(f"Could not fetch historical prices for {pair_name}.")
                return

            data = full_data_hist['Close'].dropna()
            y_prices = data[self.y_ticker]
            x_prices = data[self.x_ticker]

            self._initialize_kalman_filter(y_prices, x_prices)

            full_today_data = yf.download(
                [self.y_ticker, self.x_ticker],
                period='2d',
                progress=True,
                auto_adjust=True
            )
            if full_today_data.empty or len(full_today_data) < 2:
                print(f"Could not fetch recent prices for {pair_name}.")
                return

            today_data = full_today_data['Close']
            y_today = today_data[self.y_ticker].iloc[-1]
            x_today = today_data[self.x_ticker].iloc[-1]

            last_mean = self.latest_state_mean[-1]
            last_cov = self.latest_state_cov[-1]

            T = self.kf.transition_matrices
            Q = self.kf.transition_covariance
            pred_mean = np.dot(T, last_mean)
            pred_cov = np.dot(T, np.dot(last_cov, T.T)) + Q

            obs_mat_today = np.array([x_today, 1.0])
            spread = y_today - np.dot(obs_mat_today, pred_mean)

            R = self.kf.observation_covariance
            pred_obs_cov = np.dot(obs_mat_today, np.dot(pred_cov, obs_mat_today.T)) + R
            z_score = spread / np.sqrt(pred_obs_cov)

            slope, intercept = pred_mean[0], pred_mean[1]
            print(f"Analysis based on latest prices: {self.y_ticker}=${y_today:.2f}, {self.x_ticker}=${x_today:.2f}")
            print(f"Kalman Filter State: Slope={slope:.4f}, Intercept={intercept:.4f}")
            print(f"Calculated Spread (Forecast Error): {spread:.4f}")
            print(f"Normalized Z-Score: {z_score:.4f}")

            print("\n--- PAIRS TRADE INSTRUCTIONS ---")
            if z_score > 6.0 or z_score < -6.0:
                print("ACTION: EXIT POSITION (Stop Loss at |z| >= 6.0)")
            elif z_score > 1.0:
                print(f"ACTION: Short the spread. Short {self.y_ticker}, Long {self.x_ticker}.")
                print("  - Tier 1 Entry: |z| > 1.0")
                print("  - Tier 2 Entry: |z| > 2.0")
                print("  -... up to Tier 5 at |z| > 5.0")
            elif z_score < -1.0:
                print(f"ACTION: Long the spread. Long {self.y_ticker}, Short {self.x_ticker}.")
                print("  - Tier 1 Entry: |z| > 1.0")
                print("  - Tier 2 Entry: |z| > 2.0")
                print("  -... up to Tier 5 at |z| > 5.0")
            else:
                print("ACTION: No trade. Z-score is within the [-1.0, 1.0] neutral zone.")
                print("  - If in a position, exit on z-score crossing 0 (Take Profit).")

        except Exception as e:
            print(f"An error occurred in the pairs trading engine for {pair_name}: {e}")


# --- END OF MEAN-REVERSION ENGINE ---
