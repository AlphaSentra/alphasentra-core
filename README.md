# AlphaSentra
![screenshot](img/banner.png)

AlphaSentra is an agentic AI that leverages generative intelligence to convert market, economic, and sentiment data into insights, opinions, and recommendations. It autonomously tests, adapts, and executes strategies to capture patterns driven by collective sentiment.

## Install Packages
To run this script, you need to make sure of the requirements:

`pip install -r requirements.txt`


## Usage

Run the application interactively:
```bash
python main.py
```

Or run in batch processing mode directly:
```bash
python main.py -batch
```

Reset all datasets:
```bash
python main.py -reset
```

Enforce database size limit (optional MB value):
```bash
python main.py -dblimit [MB]
```

The `-batch` flag executes `run_batch_processing()` without showing the menu interface.
The `-reset` flag executes `reset_all()` to reset document statuses and clean up one-time records.
The `-dblimit` flag executes `purge_insights_collection()` to delete all documents in the insights collection.

## Environment Variables
Create a `.env` file in the root of the project. This file should include sensitive configuration such as database connections, API keys, and the encryption secret.

### Database Configuration
Add the following database settings to your `.env`:
If `USE_MONGODB_SRV` is `true` the connection string `MONGODB_SRV` will be used, otherwise `MONGODB_HOST`, `MONGO_PORT`, `MONGODB_DATABASE`, `MONGODB_USERNAME`, `MONGODB_PASSWORD`, and `MONGODB_AUTH_SOURCE` will be used.

<pre>
USE_MONGODB_SRV=true
MONGODB_HOST=localhost
MONGODB_PORT=27017
MONGODB_DATABASE=alphasentra
MONGODB_USERNAME=username
MONGODB_PASSWORD=password
MONGODB_AUTH_SOURCE=admin
MONGODB_SRV='mongodb+srv://alphasentra_db_user:{db_password}@cluster0.9x59erc.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0'
</pre>

### Google Gemini API
Include your Google Gemini API credentials and encryption secret:

<pre>
GEMINI_API_KEY='gemini_api_key_1, gemini_api_key_2'
GEMINI_DEFAULT=gemini-2.5-pro
GEMINI_FLASH_MODEL=gemini-2.5-flash
GEMINI_FLASH_LITE_MODEL=gemini-2.5-flash-lite
GEMINI_PRO_MODEL=gemini-2.5-pro
ENCRYPTION_SECRET=encryption-secret
</pre>

1. **Gemini API Key**: Provide your Gemini API key using the ```GEMINI_API_KEY``` constant from [Google AI Studio](https://aistudio.google.com). 
2. **Gemini Model**: You can select which Gemini model to use. By default, we are using gemini-2.5-pro: ```GEMINI_PRO_MODEL=gemini-2.5-pro```.
3. **Encryption**: The ```ENCRYPTION_SECRET``` constant is used as the key for encrypting and decrypting our proprietary prompt designs.

Note: To create your own prompt, use the `crypt.py` script to encrypt it with your `ENCRYPTION_SECRET`.

## AI Prompt Variables and Output

### Prompt input variables

**Model [prompt] contain some of the following variables:**

- Tickers: `{ticker_str}`,
- Instrument Name: `{instrument_name}`,
- Current date: `{current_date}`,
- Sector Region: `{sector_region_str}`,
- Regional Region: `{regional_region_str}`,
- FX Region: `{fx_regions_str}`,
- Geopolitical: `{geopolitical_weight}`,
- Macroeconomic: `{macroeconomic_weight}`,
- Technical/Sentiment: `{technical_sentiment_weight}`,
- Liquidity: `{liquidity_weight}`,
- Earnings: `{earnings_weight}`,
- Business Cycle: `{business_cycle_weight}`,
- Sentiment Surveys: `{sentiment_surveys_weight}`

**Model Validation:**

```
{
  $jsonSchema: {
    bsonType: 'object',
    required: [
      'email',
      'passcode',
      'first_name',
      'etoro_username',
      'number_of_analysis',
      'country',
      'stocks',
      'forex',
      'crypto',
      'commodities',
      'last_login',
      'created_at',
      'expiry_subscription'
    ],
    properties: {
      email: {
        bsonType: 'string'
      },
      passcode: {
        bsonType: 'int'
      },
      first_name: {
        bsonType: 'string'
      },
      etoro_username: {
        bsonType: ['string', 'null']
      },
      country: {
        bsonType: 'string'
      },
      stocks: {
        bsonType: 'bool'
      },
      forex: {
        bsonType: 'bool'
      },
      crypto: {
        bsonType: 'bool'
      },
      commodities: {
        bsonType: 'bool'
      },
      number_of_analysis: {
        bsonType: 'int'
      },
      created_at: {
        bsonType: 'date'
      },
      last_login: {
        bsonType: ['date', 'null']
      },
      expiry_subscription: {
        bsonType: ['date', 'null']
      }
    }
  }
}
```

### Tickers Validation (tickers collection):

```javascript
{
  $jsonSchema: {
    bsonType: 'object',
    required: [
      'ticker',
      'ticker_tradingview',
      'ticker_etoro',
      'name',
      'region',
      'prompt',
      'model_function'
    ],
    properties: {
      ticker: {
        bsonType: 'string'
      },
      ticker_tradingview: {
        bsonType: 'string'
      },
      ticker_etoro: {
        bsonType: 'string'
      },
      name: {
        bsonType: 'string'
      },
      region: {},
      prompt: {
        bsonType: 'string'
      },
      factor: {
        bsonType: 'string'
      },
      model_function: {
        bsonType: 'string'
      },
      model_name: {
        bsonType: 'string'
      },
      asset_class: {},
      importance: {
        bsonType: 'int',
        minimum: 1,
        maximum: 5
      },
      sector: {
        bsonType: 'string'
      },
      description: {
        bsonType: 'string'
      },
      '1y': {
        bsonType: 'double'
      },
      '6m': {
        bsonType: 'double'
      },
      '3m': {
        bsonType: 'double'
      },
      '1m': {
        bsonType: 'double'
      },
      '1d': {
        bsonType: 'double'
      },
      cashflow_health: {
        bsonType: 'string'
      },
      profit_health: {
        bsonType: 'string'
      },
      price_momentum: {
        bsonType: 'string'
      },
      growth_health: {
        bsonType: 'string'
      },
      dividend_yield: {},
      recurrence: {
        bsonType: 'string'
      },
      decimal: {
        bsonType: 'int'
      },
      document_generated: {
        bsonType: 'bool'
      },
      screener_flag: {
        bsonType: 'int'
      }
    }
  }
}
```

### Regions Validation (regions collection):

```javascript
{
  $jsonSchema: {
    bsonType: 'object',
    required: [
      'region',
      'etoro_exchangeID',
      'exchange_name'
    ],
    properties: {
      region: {
        bsonType: 'string'
      },
      etoro_exchangeID: {
        bsonType: 'int'
      },
      exchange_name: {
        bsonType: 'string'
      }
    }
  }
}
```

### Asset Classes Validation (asset_classes collection):

```javascript
{
  $jsonSchema: {
    bsonType: 'object',
    required: [
      'Code',
      'Description'
    ],
    properties: {
      Code: {
        bsonType: 'string'
      },
      etoro_instrumentTypeID: {
        bsonType: 'int'
      },
      Description: {
        bsonType: 'string'
      }
    }
  }
}
```

Importance represents how we classify the significance of the information, where 1 is most important and 5 is least important:

1. Thematic market research coverage
2. Major economic data releases
3. Earnings reports and trending topics in the equity market
4. Daily coverage of popular instruments
5. Daily coverage of other or exotic instruments

We categorise asset classes as follows:

- **FX**: Forex
- **EQ**: Equities
- **ETF**: ETFs
- **IX**: Indices
- **CO**: Energy
- **CR**: Crypto

### Prompt output

The prompt should return the JSON object, including the following structure:
<pre>
 **JSON Output format**: YOUR RESPONSE MUST BE A VALID JSON OBJECT. DO NOT INCLUDE ANY ADDITIONAL TEXT OR EXPLANATIONS. With this exact structure: [title] as a string, [market_outlook_narrative] as an array of strings. [rationale] as a string. [analysis] as a string in HTML format. [key_takeaways] as a string in HTML format. [sources] as an array of objects, where each object has, [source_name] as strong, [source_title] as a string, and [source_url] as a string. On the same level as [sources], [recommendations] as an array of objects, where each object has, [ticker] as a string, [trade_direction] as string, [bull_bear_score] as integer.
</pre>

The JSON output will be interpreted by the AlphaSentra engine, which will then process, transform, and securely store the data for further analysis and use within the system.