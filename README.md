# Alphagora
Alphagora is a hybrid trading system that combines ETF sector rotation with mean-reversion strategies in gold and indices, aiming to capture growth while limiting volatility through asymmetric returns.

## Install Packages
To run this script, you need to install the following packages: yfinance pandas numpy pykalman.

### 📌 Step 1: Make sure Python is installed via Homebrew
brew install python

### 📌 Step 2: Create and activate a virtual environment
python3 -m venv yenv
source yenv/bin/activate

### 📌 Step 3: Install required packages
pip install yfinance pandas numpy pykalman python-dotenv statsmodels

## Google Gemini API
Create an .env in the root of the directory

with the following lines:

<pre> '''GEMINI_API_KEY=your_actual_gemini_api_key''' </pre>
<pre> '''ANOTHER_SECRET=value123'''<pre>
<pre> '''DEBUG_MODE=true'''<pre>