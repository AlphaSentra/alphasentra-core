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
from statsmodels.tsa.stattools import coint  # For cointegration testing
from helpers import get_beta


# --- CONFIGURATION ---

PAIRS = {
    'Gold_vs_Miners': ('GLD', 'GDX'),
    'Miners_vs_Gold': ('GDX', 'GLD'),
    'VXX_vs_SVXY': ('VXX', 'SVXY'),
}
PAIRS_LOOKBACK_YEARS = 1
ENABLE_COINTEGRATION_TEST = False  # Set to False to skip cointegration check


# --- MEAN-REVERSION (PAIRS TRADING) ENGINE ---

def mean_reversion_engine():
    print(f"\n--- Mean-Reversion Engine ---")
    print("Strategy: Kalman Filter-based pairs trading reviewed daily.")
    if ENABLE_COINTEGRATION_TEST:
        print("Note: Engle-Granger cointegration test ENABLED.")
    else:
        print("Note: Engle-Granger cointegration test DISABLED.")

    for pair_name, (y_ticker, x_ticker) in PAIRS.items():
        trader = KalmanPairsTrader(y_ticker, x_ticker)
        trader.get_pairs_recommendations()
        print("\n")


class KalmanPairsTrader:
    def __init__(self, dependent_etf, independent_etf):
        self.y_ticker = dependent_etf
        self.x_ticker = independent_etf
        self.kf = None
        self.latest_state_mean = None
        self.latest_state_cov = None

    def _initialize_kalman_filter(self, y_prices, x_prices):
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

            if ENABLE_COINTEGRATION_TEST:
                coint_score, p_value, _ = coint(y_prices, x_prices)
                print(f"Engle-Granger Cointegration Test p-value: {p_value:.4f}")
                if p_value > 0.05:
                    print("Result: No significant cointegration found. Skipping pair.")
                    return
                else:
                    print("Result: Cointegration confirmed. Proceeding with Kalman Filter model.")
                    
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

            # --- BETA ADJUSTED ALLOCATION ---
            beta_y = get_beta(self.y_ticker)
            beta_x = get_beta(self.x_ticker)

            if beta_y is None or beta_x is None:
                print("Warning: Unable to compute beta for one or both tickers. Using default allocation split 50/50.")
                beta_y = beta_x = 1.0  # fallback equal weighting

            print(f"Beta Estimates: {self.y_ticker} Beta={beta_y:.2f}, {self.x_ticker} Beta={beta_x:.2f}")

            def tier_print(tier):
                base_alloc_per_tier = 0.025  # 2.5% per tier
                total_alloc = base_alloc_per_tier * tier
                beta_y_abs = abs(beta_y)
                beta_x_abs = abs(beta_x)
                # Avoid division by zero
                if beta_y_abs == 0 or beta_x_abs == 0:
                    alloc_long = alloc_short = total_alloc / 2
                else:
                    inv_beta_y = 1 / beta_y_abs
                    inv_beta_x = 1 / beta_x_abs
                    inv_sum = inv_beta_y + inv_beta_x
                    alloc_long = (inv_beta_y / inv_sum) * total_alloc
                    alloc_short = (inv_beta_x / inv_sum) * total_alloc
                print(f"  - Tier {tier} Entry: Total allocation {total_alloc:.2%}")
                print(f"    Allocate {alloc_long:.2%} long ({self.y_ticker}), {alloc_short:.2%} short ({self.x_ticker}).")

            print("\n" + "=" * 100)
            print(f"--- PAIRS TRADE INSTRUCTIONS {pair_name} ---")
            print("=" * 100)

            if abs(z_score) >= 6.0:
                print("ACTION: EXIT POSITION (Stop Loss at |z| >= 6.0)")
            elif z_score > 1.0:
                print(f"ACTION: Short the spread. Short {self.y_ticker}, Long {self.x_ticker}.")
                if z_score <= 2.0:
                    tier_print(1)
                elif z_score <= 3.0:
                    tier_print(2)
                elif z_score <= 4.0:
                    tier_print(3)
                elif z_score <= 5.0:
                    tier_print(4)
                else:
                    tier_print(5)
            elif z_score < -1.0:
                print(f"ACTION: Long the spread. Long {self.y_ticker}, Short {self.x_ticker}.")
                if z_score >= -2.0:
                    tier_print(1)
                elif z_score >= -3.0:
                    tier_print(2)
                elif z_score >= -4.0:
                    tier_print(3)
                elif z_score >= -5.0:
                    tier_print(4)
                else:
                    tier_print(5)
            else:
                print("ACTION: No trade. Z-score is within the [-1.0, 1.0] neutral zone.")
                print("  - If in a position, exit on z-score crossing 0 (Exit position).")

            print("\n" + "=" * 100)

        except Exception as e:
            print(f"An error occurred in the pairs trading engine for {pair_name}: {e}")


# --- MAIN EXECUTION ---

if __name__ == "__main__":
    mean_reversion_engine()