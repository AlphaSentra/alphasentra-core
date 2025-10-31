import numpy as np
import random
from typing import List, Dict, Any
from logging_utils import log_error, log_warning, log_info

def apply_stochastic_noise(value: float, scale: float = 0.15) -> float:
    """
    Applies Gaussian (Normal) noise to a base value and clamps the result between -1.0 and 1.0.
    This simulates the random, unpredictable deviations in an individual's assessment.
    """
    noise = np.random.normal(loc=0, scale=scale)
    return np.clip(value + noise, -1.0, 1.0)

def update_simulation_with_stochastic(
    simulation_data: List[Dict[str, Any]], 
    num_additional_points: int = 1000,
    base_c_scale: float = 0.12,
    base_s_scale: float = 0.18,
    extrapolate_c_scale: float = 0.25,
    extrapolate_s_scale: float = 0.3
) -> List[Dict[str, Any]]:
    """
    Processes simulation data and generates additional synthetic points by:
    1. Applying stochastic noise to original conviction/sentiment values
    2. Generating new points by extrapolating from initial profiles
    3. Enforcing academic constraints and determining positions
    """
    processed_data = []

    # 1. First process the original data points
    for entry in simulation_data:
        # Extract base name without any existing numbers
        base_name = entry['profile'].split('#')[0].strip()
        
        # Generate random ID between 1 and 1 million
        random_id = random.randint(1, 1000000)
        unique_profile_name = f"{base_name} #{random_id}"
        
        stochastic_c = apply_stochastic_noise(entry['conviction'], base_c_scale)
        stochastic_s = apply_stochastic_noise(entry['sentiment'], base_s_scale)

        # Enforce academic constraint
        if abs(stochastic_s) > abs(stochastic_c):
            stochastic_s = np.sign(stochastic_s) * abs(stochastic_c)

        # Determine position
        if stochastic_c > 0.3:
            final_position = "BULLISH"
        elif stochastic_c < -0.3:
            final_position = "BEARISH"
        else:
            final_position = "NEUTRAL"

        processed_data.append({
            "profile": unique_profile_name,
            "conviction": round(stochastic_c, 4),
            "sentiment": round(stochastic_s, 4),
            "position": final_position
        })

    # 2. Generate additional synthetic points if we have initial data
    if simulation_data:
        for _ in range(num_additional_points):
            # Randomly select a base profile to extrapolate from
            base_profile = simulation_data[np.random.randint(0, len(simulation_data))]
            
            # Apply more aggressive noise for variation in synthetic points
            new_c = apply_stochastic_noise(base_profile['conviction'], extrapolate_c_scale)
            new_s = apply_stochastic_noise(base_profile['sentiment'], extrapolate_s_scale)

            # Enforce academic constraint
            if abs(new_s) > abs(new_c):
                new_s = np.sign(new_s) * abs(new_c)

            # Determine position
            if new_c > 0.3:
                new_position = "BULLISH"
            elif new_c < -0.3:
                new_position = "BEARISH"
            else:
                new_position = "NEUTRAL"

            # Create unique profile name with random ID
            base_name = base_profile['profile'].split('#')[0].strip()
            random_id = random.randint(1, 1000000)
            unique_profile_name = f"{base_name} #{random_id}"
            
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
    """Manages the market environment and the simulation loop."""
    def __init__(self, initial_investors: List[Dict[str, Any]], initial_price: float = 100.0):
        self.initial_price = initial_price
        self.price = initial_price
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
    """Processes simulation data through market simulation and stochastic updates."""
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
    
    # 1. First run agent-based market simulation
    simulator = MarketSimulator(processed_simulation_data, initial_price=100.0)
    
    # Run one time step with example parameters
    public_info = 0.6  # Example: positive market signal
    macro_shock = -0.1  # Example: slight negative macro event
    simulated_states = simulator.run_time_step(public_info, macro_shock)
    
    # 2. Then update with stochastic noise
    final_states = update_simulation_with_stochastic(simulated_states)
    
    return final_states

if __name__ == "__main__":
    
    def process_simulation_data(raw_simulation_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Processes simulation data through market simulation and stochastic updates."""
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
        
        # 1. First run agent-based market simulation
        simulator = MarketSimulator(processed_simulation_data, initial_price=100.0)
        
        # Run one time step with example parameters
        public_info = 0.6  # Example: positive market signal
        macro_shock = -0.1  # Example: slight negative macro event
        simulated_states = simulator.run_time_step(public_info, macro_shock)
        
        # 2. Then update with stochastic noise
        final_states = update_simulation_with_stochastic(simulated_states)
        
        return final_states
    
    if __name__ == "__main__":
        # Generate initial investor data using stochastic function
        base_profiles = [
            {"profile": f"Growth Investor #{random.randint(1, 1000000)}", "conviction": 0.7, "sentiment": 0.6, "position": "BULLISH"},
            {"profile": f"Value Investor #{random.randint(1, 1000000)}", "conviction": -0.5, "sentiment": -0.35, "position": "BEARISH"},
            {"profile": f"Momentum Trader #{random.randint(1, 1000000)}", "conviction": 0.3, "sentiment": 0.25, "position": "BULLISH"}
        ]
        
        initial_investors = update_simulation_with_stochastic(base_profiles)
        
        if not initial_investors:
            raise ValueError("No initial investor data generated")
            
        # Initialize the Market
        INITIAL_PRICE = 100.0
        simulator = MarketSimulator(initial_investors, INITIAL_PRICE)

        # Log Initial (t=0) State
        log_info(f"Initial state (t=0) - Price: {INITIAL_PRICE}")
        initial_states = [a.get_state() for a in simulator.agents]
        for state in initial_states:
            log_info(f"Agent {state['profile']} - Conviction: {state['conviction']:.4f}, Sentiment: {state['sentiment']:.4f}, Position: {state['position']}, Bias: {state['Recency_Bias']:.4f}")

        # Run Simulation for t=1
        PUBLIC_INFO_SIGNAL = 0.6
        MACRO_SHOCK = -0.1
        log_info(f"External inputs for t=1 - Public Info: {PUBLIC_INFO_SIGNAL}, Macro Shock: {MACRO_SHOCK}")
        
        # Run the simulation step
        final_states_t1 = simulator.run_time_step(PUBLIC_INFO_SIGNAL, MACRO_SHOCK)

        # Log Final (t=1) State
        log_info("Resulting state (t=1):")
        for state in final_states_t1:
            log_info(f"Agent {state['profile']} - Conviction: {state['conviction']:.4f}, Sentiment: {state['sentiment']:.4f}, Position: {state['position']}, P&L: {state['P&L']:.4f}")

        log_info("t=1 values calculated based on market feedback and agent parameters")
