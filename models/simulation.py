import numpy as np
import random
from typing import List, Dict, Any
from logging_utils import log_error, log_warning, log_info

def apply_stochastic_noise(value: float, scale: float) -> float:
    """Applies Gaussian noise to a value."""
    return value + np.random.normal(0, scale)

def dynamic_correlation_strength(prices, min_strength=0.3, max_strength=0.8, window=20):
    """
    Adjusts correlation_strength based on recent price volatility.
    
    prices: list or np.array of recent stock prices
    min_strength: minimum correlation (diffuse, independent)
    max_strength: maximum correlation (trend-driven)
    window: lookback period for volatility calculation
    """
    prices = np.array(prices)
    if len(prices) < window:
        return min_strength  # not enough data, default to independent
    
    # Calculate recent returns
    returns = np.diff(prices[-window:]) / prices[-window:-1]
    
    # Measure volatility as std of returns
    volatility = np.std(returns)
    
    # Normalize volatility to 0-1 (can tweak scale_factor)
    scale_factor = 0.05  # typical daily return std is ~5%
    normalized_vol = min(volatility / scale_factor, 1.0)
    
    # Scale correlation_strength between min_strength and max_strength
    correlation_strength = min_strength + normalized_vol * (max_strength - min_strength)
    
    return correlation_strength

def update_simulation_with_stochastic(
    simulation_data: List[Dict[str, Any]],
    num_additional_points: int = 1000,
    base_c_scale: float = 0.12,
    base_s_scale: float = 0.18,
    extrapolate_c_scale: float = 0.25,
    extrapolate_s_scale: float = 0.3,
    prices: List[float] = None   # Price history for dynamic correlation
) -> List[Dict[str, Any]]:
    """
    Processes simulation data and generates additional synthetic points by:
    1. Applying stochastic noise to original conviction/sentiment values
    2. Generating new points by extrapolating from initial profiles
    3. Using a soft correlation model to prevent artificial diagonals
    """
    processed_data = []

    # Calculate dynamic correlation strength
    if prices is None:
        correlation_strength = 0.3  # default to min strength
    else:
        correlation_strength = dynamic_correlation_strength(
            prices,
            min_strength=0.3,
            max_strength=0.8,
            window=20
        )

    # === 1. Process the original data points ===
    for entry in simulation_data:
        base_name = entry['profile'].split('#')[0].strip()
        random_id = random.randint(1, 1_000_000)
        unique_profile_name = f"{base_name} #{random_id}"
        
        # Apply stochastic noise
        stochastic_c = apply_stochastic_noise(entry['conviction'], base_c_scale)
        stochastic_s = apply_stochastic_noise(entry['sentiment'], base_s_scale)
        
        # Soft correlation (prevents diagonal X-shape)
        stochastic_s = (correlation_strength * stochastic_c +
                        (1 - correlation_strength) * stochastic_s)
        
        # Clip to range [-1, 1]
        stochastic_c = float(np.clip(stochastic_c, -1, 1))
        stochastic_s = float(np.clip(stochastic_s, -1, 1))

        # Determine market position
        if stochastic_c > 0:
            final_position = "BULLISH"
        elif stochastic_c < 0:
            final_position = "BEARISH"
        else:
            final_position = "NEUTRAL"

        processed_data.append({
            "profile": unique_profile_name,
            "conviction": round(stochastic_c, 4),
            "sentiment": round(stochastic_s, 4),
            "position": final_position
        })

    # === 2. Generate additional synthetic points ===
    if simulation_data:
        for _ in range(num_additional_points):
            base_profile = simulation_data[np.random.randint(0, len(simulation_data))]
            base_name = base_profile['profile'].split('#')[0].strip()
            random_id = random.randint(1, 1_000_000)
            unique_profile_name = f"{base_name} #{random_id}"
            
            new_c = apply_stochastic_noise(base_profile['conviction'], extrapolate_c_scale)
            new_s = apply_stochastic_noise(base_profile['sentiment'], extrapolate_s_scale)
            
            # Apply soft correlation
            new_s = (correlation_strength * new_c +
                     (1 - correlation_strength) * new_s)
            
            # Clip to realistic sentiment/conviction range
            new_c = float(np.clip(new_c, -1, 1))
            new_s = float(np.clip(new_s, -1, 1))
            
            # Determine position
            if new_c > 0:
                new_position = "BULLISH"
            elif new_c < 0:
                new_position = "BEARISH"
            else:
                new_position = "NEUTRAL"

            processed_data.append({
                "profile": unique_profile_name,
                "conviction": round(new_c, 4),
                "sentiment": round(new_s, 4),
                "position": new_position
            })

    return processed_data


# --- AGENT-BASED MARKET SIMULATION ---

class Agent:
    """
    Base class for an Investor Agent, initializing parameters based on the t=0 snapshot.
    The parameters (Risk Aversion, Bias) are reverse-engineered from the initial C/S data.
    """
    def __init__(self, data: Dict[str, Any], initial_price: float):
        self.profile = data['profile']
        self.conviction = data['conviction']
        self.sentiment = data['sentiment']
        self.position = data['position']
        self.initial_price = initial_price
        self.current_position_value = self._get_position_value(self.position) # -1, 0, or 1

        # Reverse-engineer parameters (Crucial for ABM "correctness")
        # Higher |C - S| gap implies higher initial behavioral bias (less rational).
        self.recency_bias = abs(self.conviction - self.sentiment) + random.uniform(0.01, 0.1) 
        # Extreme conviction implies lower risk aversion (more willing to take aggressive stance).
        self.risk_aversion = 1.0 - abs(self.conviction) 
        
        # P&L tracking
        self.entry_price = initial_price
        self.pnl = 0.0

    def _get_position_value(self, position_str: str) -> int:
        """Converts position string to a quantifiable trade signal."""
        if position_str == "BULLISH": return 1
        if position_str == "BEARISH": return -1
        return 0 # Neutral

    def calculate_pnl(self, new_price: float):
        """Updates P&L based on new price."""
        # P&L is calculated only on the held position
        price_change = new_price - self.entry_price
        self.pnl = price_change * self.current_position_value
        
    def calculate_new_conviction(self, public_info: float, macro_shock: float) -> float:
        """
        Academic Function C_i = f(Public Info, Noise, Risk Aversion)
        Public Info simulates the asset's fundamental value or momentum signal.
        """
        # --- ABM LOGIC IMPLEMENTATION (C_i function) ---
        # 1. Base Conviction is influenced by public information and macro shocks.
        base_conv = public_info * (1.0 - self.risk_aversion) + macro_shock
        
        # 2. Add Fundamental Noise (Normal Distribution as per agent_based_modeling.md)
        fundamental_noise = np.random.normal(loc=0, scale=0.05)
        
        # New conviction is clamped between -1 and 1
        new_c = np.clip(base_conv + fundamental_noise, -1.0, 1.0)
        return new_c

    def calculate_new_sentiment(self, agg_sentiment: float) -> float:
        """
        Academic Function S_i = g(Past Returns, Aggregate Sentiment, Recency Bias)
        """
        # --- ABM LOGIC IMPLEMENTATION (S_i function) ---
        # 1. Driven by recent utility (P&L) and Herd Effect.
        # P&L is normalized (using a small, arbitrary scale factor for simplicity)
        pnl_effect = np.tanh(self.pnl * 0.5) 
        
        # 2. Herd Effect: influenced by overall market sentiment, scaled by agent's bias.
        herd_effect = agg_sentiment * self.recency_bias
        
        # New sentiment is an emotional weighted average
        new_s = np.clip((pnl_effect * 0.5) + (herd_effect * 0.5), -1.0, 1.0)
        
        # Sentiment cannot exceed Conviction (rational constraint)
        return min(new_s, self.conviction)


    def execute_trade(self):
        """Determines new position based on new conviction threshold."""
        # Use a random threshold to simulate uncertainty in trade execution
        trade_threshold = random.uniform(0.3, 0.6) 

        if self.conviction > trade_threshold:
            self.position = "BULLISH"
            self.current_position_value = 1
        elif self.conviction < -trade_threshold:
            self.position = "BEARISH"
            self.current_position_value = -1
        else:
            self.position = "NEUTRAL"
            self.current_position_value = 0

    def get_state(self) -> Dict[str, Any]:
        """Returns the current dynamic state of the agent."""
        return {
            "profile": self.profile,
            "conviction": round(self.conviction, 4),
            "sentiment": round(self.sentiment, 4),
            "position": self.position,
            "P&L": round(self.pnl, 4),
            "Risk_Aversion": round(self.risk_aversion, 4),
            "Recency_Bias": round(self.recency_bias, 4)
        }

class MarketSimulator:
    """Core market simulation engine modeling price dynamics and investor behavior.
    
    Attributes:
        agents (list): Investor agent objects participating in the market
        price (float): Current market price
        price_history (list): Record of historical prices
        volume (float): Current trading volume
        market_sentiment (float): Aggregate market sentiment (-1.0 to 1.0)
        
    Methods:
        run_time_step: Advance simulation by one time step
        calculate_market_sentiment: Compute aggregate market mood
        update_agent_positions: Process individual investor decisions
        apply_market_impact: Calculate price changes from trading activity
    """
    """Manages the market environment and the simulation loop."""
    def __init__(self, initial_investors: List[Dict[str, Any]], initial_price: float = 100.0):
        self.initial_price = initial_price
        self.price = initial_price
        self.price_history = [initial_price]  # Track price history for volatility
        self.agents: List[Agent] = [Agent(data, initial_price) for data in initial_investors]
        self.time = 0

    def _calculate_aggregate_sentiment(self) -> float:
        """Calculates the average market sentiment."""
        return np.mean([a.sentiment for a in self.agents])

    def _calculate_net_order(self) -> int:
        """Calculates the Net Order Imbalance (total buyers - total sellers)."""
        return sum(a.current_position_value for a in self.agents)

    def run_time_step(self, public_info_signal: float, macro_shock: float) -> List[Dict[str, Any]]:
        """
        Runs one iteration of the ABM simulation (t -> t+1).
        This implements the Correction/Feedback Loop.
        """
        self.time += 1
        log_info(f"Time step t={self.time} starting")

        # 1. Aggregate State from t-1
        net_order = self._calculate_net_order()
        agg_sentiment = self._calculate_aggregate_sentiment()

        # 2. Price Correction (Price Impact + Price Noise)
        # Price Noise (epsilon_P) using a simple random walk model (approximation of GBM/Lévy)
        price_noise = np.random.normal(loc=0, scale=0.1) 
        
        # Price change is driven by the Net Order Imbalance (gamma=0.5) plus noise.
        # This is where the agents' actions affect the market.
        delta_price = (0.5 * net_order) + price_noise
        self.price += delta_price
        self.price_history.append(self.price)  # Update price history
        
        log_info(f"Market state - Net Order: {net_order}, Sentiment: {round(agg_sentiment, 4)}, Price Change: {round(delta_price, 4)}, New Price: {round(self.price, 4)}")

        # 3. Agent Update Loop (Individual Decisions)
        new_states = []
        for agent in self.agents:
            # a. Update Utility (P&L) based on the new price
            agent.calculate_pnl(self.price)
            
            # b. Recalculate Conviction (C_i) based on new market/info signals
            agent.conviction = agent.calculate_new_conviction(public_info_signal, macro_shock)
            
            # c. Recalculate Sentiment (S_i) based on P&L and Herding
            agent.sentiment = agent.calculate_new_sentiment(agg_sentiment)
            
            # d. Execute Trade (Determines new Position P_i)
            agent.execute_trade()
            
            new_states.append(agent.get_state())

        return new_states


def process_simulation_data(raw_simulation_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Processes raw simulation data through a two-phase market simulation pipeline.
    
    Phase 1: Agent-Based Market Simulation
    - Initializes investor agents from validated input data
    - Runs one market time step with example fundamental parameters
    - Models price discovery through investor interactions
    
    Phase 2: Stochastic Data Augmentation
    - Applies controlled noise to simulation outputs
    - Generates synthetic data points while preserving academic constraints
    - Ensures sentiment never exceeds conviction (rational agent principle)
    
    Args:
        raw_simulation_data: List of investor profile dictionaries. Each must contain:
            - profile: Investor identifier string
            - conviction: Numeric value between [-1.0, 1.0]
            - sentiment: Numeric value between [-1.0, 1.0]
            - position: "BULLISH", "BEARISH", or "NEUTRAL"
            
    Returns:
        List of processed investor states with:
            - Updated conviction/sentiment from market dynamics
            - Unique profile identifiers
            - Enforced academic constraints
            - Stochastic variations for robustness testing
            
    Note:
        Current implementation uses example parameters for market simulation:
        - public_info=0.6 (positive market signal)
        - macro_shock=-0.1 (negative macroeconomic event)
        These should be parameterized in future versions.
    """
    # Validate and transform input data
    processed_simulation_data = [
        {
            "profile": entry["profile"],
            "conviction": entry["conviction"],
            "sentiment": entry["sentiment"],
            "position": entry["position"]
        }
        for entry in raw_simulation_data
        if all(k in entry for k in ["profile", "conviction", "sentiment", "position"])
    ]
    
    if not processed_simulation_data:
        return []
    
    # 1. Run agent-based market simulation
    simulator = MarketSimulator(processed_simulation_data, initial_price=100.0)
    
    # Run one time step with example parameters
    public_info = 0.6  # Example: positive market signal
    macro_shock = -0.1  # Example: slight negative macro event
    simulated_states = simulator.run_time_step(public_info, macro_shock)
    
    # 2. Apply stochastic data augmentation
    final_states = update_simulation_with_stochastic(
        simulated_states,
        prices=simulator.price_history
    )
    
    return final_states

    
