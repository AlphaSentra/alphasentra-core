import yfinance as yf
import pandas as pd
import numpy as np
from pykalman import KalmanFilter
from datetime import datetime, timedelta

# --- CONFIGURATION ---

# 1. Momentum Engine Configuration
MOMENTUM_ETFS = ['XLC', 'XLY', 'XLP', 'XLE', 'XLF', 'XLV', 'XLI', 'XLB', 'XLRE', 'XLK', 'XLU']
MOMENTUM_ALLOCATION_MIN = 0.50  # 50%
MOMENTUM_ALLOCATION_MAX = 0.75  # 75%

# 2. Mean-Reversion Engine Configuration
PAIRS = {
    'Gold_vs_Miners': ('GDX', 'GLD'),
    'Yield_Curve': ('TLT', 'IEI')
}
PAIRS_ALLOCATION = 0.25
PAIRS_LOOKBACK_YEARS = 5 # Years of data for Kalman Filter initialization

# --- MOMENTUM ENGINE ---

def get_momentum_recommendations(bull_bear_score):
    """
    Calculates and prints recommendations for the momentum sleeve of the portfolio.
    """
    print("\n--- Momentum Engine (50% - 75% Allocation) ---\n")
    print(f"Comparing the following {len(MOMENTUM_ETFS)} sector ETFs: {', '.join(MOMENTUM_ETFS)}")
    print("Strategy: Monthly rotation of top 3 sectors based on 12-1 month momentum.")

    # Validate bull_bear_score
    if not 1 <= bull_bear_score <= 10:
        print("Error: Bull/Bear score must be between 1 and 10.")
        return

    # Calculate allocation based on the score
    momentum_allocation = MOMENTUM_ALLOCATION_MIN + (bull_bear_score - 1) * (MOMENTUM_ALLOCATION_MAX - MOMENTUM_ALLOCATION_MIN) / 9
    print(f"Bull/Bear Score: {bull_bear_score}/10 -> Momentum Allocation: {momentum_allocation:.2%}")

    try:
        # Fetch ~16 months of monthly data to ensure we have at least 14 data points for the calculation.
        end_date = datetime.today()
        # Increased lookback period to 480 days to ensure enough data points are fetched.
        start_date = end_date - timedelta(days=480) 
        
        # Download monthly historical data. auto_adjust=True is the new yfinance default.
        # It provides adjusted prices in the 'Close' column and removes 'Adj Close'.
        full_data = yf.download(MOMENTUM_ETFS, start=start_date, end=end_date, interval='1mo', progress=True, auto_adjust=True)
        
        if full_data.empty:
            print("Could not download momentum data. Please check tickers and network connection.")
            return

        # Use the 'Close' column which is auto-adjusted by yfinance
        data = full_data['Close']
        
        if data.empty:
            print("Could not extract price data. Please check tickers and network connection.")
            return

        # Calculate 12-1 month momentum
        # Formula: (Price 1 month ago / Price 13 months ago) - 1. 
        momentum = (data.shift(1) / data.shift(13)) - 1
        
        # Get the latest momentum scores
        latest_momentum = momentum.iloc[-1].dropna()

        # Fallback for start-of-month scenarios where the last row might be incomplete
        if len(latest_momentum) < 3 and len(momentum) > 1:
            print("Last row has insufficient data, attempting to use second to last row.")
            latest_momentum = momentum.iloc[-2].dropna()
        
        if len(latest_momentum) < 3:
            print("Error: Not enough data to rank ETFs for momentum even after fallback.")
            print("This can happen if the script is run over a weekend or at the very start of a month.")
            return

        # Sort all ETFs by momentum score to show the full comparison
        all_ranked_etfs = latest_momentum.sort_values(ascending=False)
        
        print("\nFull Ranking of Sector ETFs by Momentum Score (for comparison):")
        print(all_ranked_etfs.to_string())

        # Select top 3
        top_3_etfs = all_ranked_etfs.head(3)

        # Generate trade instructions
        print("\n--- MOMENTUM TRADE INSTRUCTIONS ---")
        print(f"1. Adjust total allocation to the momentum sleeve to {momentum_allocation:.2%}.")
        print("2. Sell any currently held sector ETFs that are NOT in the list below.")
        print("3. Buy the following Top 3 ETFs in equal weights:")
        for etf, score in top_3_etfs.items():
            weight_per_etf = momentum_allocation / 3
            print(f"   - {etf}: Allocate {weight_per_etf:.2%} of the total portfolio. (Momentum Score: {score:.4f})")

    except Exception as e:
        print(f"An error occurred in the momentum engine: {e}")


# --- MEAN-REVERSION (PAIRS TRADING) ENGINE ---

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
        # The state is 2D: [slope, intercept]
        # The observation is 1D: price of Y
        # The observation matrix F is time-varying: [price_of_X, 1]
        obs_mat = np.vstack([x_prices, np.ones(len(x_prices))]).T[:, np.newaxis, :]

        # Using pykalman to set up the filter
        self.kf = KalmanFilter(
            n_dim_state=2,
            n_dim_obs=1,
            initial_state_mean=np.zeros(2),
            initial_state_covariance=np.ones((2, 2)),
            transition_matrices=np.eye(2),  # Random walk for slope and intercept
            observation_matrices=obs_mat,
            observation_covariance=1.0, # Can be estimated with EM
            transition_covariance=np.full((2, 2), 0.0001) # Small drift for state evolution
        )
        
        # Fit the filter on historical data to get the final state
        self.latest_state_mean, self.latest_state_cov = self.kf.filter(y_prices.values)

    def get_pairs_recommendations(self):
        """
        Calculates and prints recommendations for the pairs trading sleeve.
        """
        pair_name = f"{self.y_ticker}/{self.x_ticker}"
        print(f"\n--- Pairs Trading Analysis: {pair_name} ---\n")

        try:
            # 1. Fetch historical data for initialization
            end_date = datetime.today()
            start_date = end_date - timedelta(days=365 * PAIRS_LOOKBACK_YEARS)
            
            # Download daily historical data
            full_data_hist = yf.download([self.y_ticker, self.x_ticker], start=start_date, end=end_date, progress=True, auto_adjust=True)
            if full_data_hist.empty:
                print(f"Could not fetch historical prices for {pair_name}.")
                return

            data = full_data_hist['Close'].dropna()
            
            y_prices = data[self.y_ticker]
            x_prices = data[self.x_ticker]

            # 2. Initialize and run the Kalman Filter on historical data
            self._initialize_kalman_filter(y_prices, x_prices)
            
            # 3. Fetch the most recent prices for today's signal
            full_today_data = yf.download([self.y_ticker, self.x_ticker], period='2d', progress=True, auto_adjust=True)
            if full_today_data.empty or len(full_today_data) < 2:
                print(f"Could not fetch recent prices for {pair_name}.")
                return

            today_data = full_today_data['Close']
                
            y_today = today_data[self.y_ticker].iloc[-1]
            x_today = today_data[self.x_ticker].iloc[-1]

            # 4. Predict today's state based on yesterday's filtered state
            last_mean = self.latest_state_mean[-1]
            last_cov = self.latest_state_cov[-1]
            
            # This performs the prediction step of the filter
            pred_mean, pred_cov = self.kf.filter_update(
                filtered_state_mean=last_mean,
                filtered_state_covariance=last_cov,
                observation=None # No observation, this is a pure prediction
            )

            # 5. Calculate the z-score for today's observation
            obs_mat_today = np.array([x_today, 1.0])
            # The forecast error (spread) is the difference between observed Y and predicted Y
            spread = y_today - np.dot(obs_mat_today, pred_mean)
            
            # Calculate spread variance (innovation covariance)
            # Q_t = H_t * P_t|t-1 * H_t' + R
            pred_obs_cov = np.dot(obs_mat_today, np.dot(pred_cov, obs_mat_today.T)) + self.kf.observation_covariance
            z_score = spread / np.sqrt(pred_obs_cov)

            slope, intercept = pred_mean[0], pred_mean[1]
            print(f"Analysis based on today's prices: {self.y_ticker}=${y_today:.2f}, {self.x_ticker}=${x_today:.2f}")
            print(f"Kalman Filter State: Slope={slope:.4f}, Intercept={intercept:.4f}")
            print(f"Calculated Spread (Forecast Error): {spread:.4f}")
            print(f"Normalized Z-Score: {z_score:.4f}")

            # 6. Generate trade instructions based on z-score
            # This script assumes we start with no position and only prints entry/exit signals.
            # A real implementation would need to track the current position state.
            print("\n--- PAIRS TRADE INSTRUCTIONS ---")
            if z_score > 6.0 or z_score < -6.0:
                print(f"ACTION: EXIT POSITION (Stop Loss at |z| >= 6.0)")
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


# --- MAIN EXECUTION ---

def main():
    """
    Main function to run the hybrid strategy analysis.
    """
    print("="*50)
    print("Hybrid Portfolio Strategy - Daily Trade Analysis")
    print(f"Date: {datetime.today().strftime('%Y-%m-%d')}")
    print("="*50)
    print("Disclaimer: This script is for educational purposes only and is not financial advice.")
    print("It uses publicly available APIs and data may have inaccuracies.")
    
    # --- Part 1: Momentum Engine ---
    try:
        bull_bear_score = int(input("\nEnter the Bull/Bear Score (1-10, where 10 is most bullish): "))
        get_momentum_recommendations(bull_bear_score)
    except ValueError:
        print("Invalid input. Please enter an integer between 1 and 10.")
        return

    # --- Part 2: Mean-Reversion Engine ---
    print("\n" + "="*50)
    print(f"\n--- Mean-Reversion Engine ({PAIRS_ALLOCATION:.0%} Allocation) ---")
    print("Strategy: Kalman Filter-based pairs trading reviewed daily.")
    
    for pair_name, (y_ticker, x_ticker) in PAIRS.items():
        trader = KalmanPairsTrader(y_ticker, x_ticker)
        trader.get_pairs_recommendations()

    print("\n" + "="*50)
    print("Analysis Complete.")
    print("="*50)

if __name__ == "__main__":
    # Note: To run this script, you need to install the following packages:
    # pip install yfinance pandas numpy pykalman
    main()
