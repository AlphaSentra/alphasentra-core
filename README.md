# Alphagora
![screenshot](img/banner.png)

Alphagora is an agentic AI that leverages generative intelligence to convert market, economic, and sentiment data into insights, opinions, and recommendations. It autonomously tests, adapts, and executes strategies to capture patterns driven by collective sentiment.

## Install Packages
To run this script, you need to make sure of the requirements:

`pip install -r requirements.txt`


## Environment Variables
Create a `.env` file in the root of the project. This file should include sensitive configuration such as database connections, API keys, and the encryption secret.

### Database Configuration
Add the following database settings to your `.env`:
If `USE_MONGODB_SRV` is `true` the connection string `MONGODB_SRV` will be used, otherwise `MONGODB_HOST`, `MONGO_PORT`, `MONGODB_DATABASE`, `MONGODB_USERNAME`, `MONGODB_PASSWORD`, and `MONGODB_AUTH_SOURCE` will be used.

<pre>
USE_MONGODB_SRV=true
MONGODB_HOST=localhost
MONGODB_PORT=27017
MONGODB_DATABASE=alphagora
MONGODB_USERNAME=username
MONGODB_PASSWORD=password
MONGODB_AUTH_SOURCE=admin
MONGODB_SRV='mongodb+srv://alphagora_db_user:{db_password}@cluster0.9x59erc.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0'
</pre>

### Google Gemini API
Include your Google Gemini API credentials and encryption secret:

<pre>
GEMINI_API_KEY=['gemini_api_key_1','gemini_api_key_2']
GEMINI_DEFAULT=gemini-2.5-pro
GEMINI_FLASH_MODEL=gemini-2.5-flash
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
      'title',
      'market_outlook_narrative',
      'rationale',
      'analysis',
      'recommendations',
      'sentiment_score',
      'market_impact',
      'timestamp_gmt',
      'language_code'
    ],
    properties: {
      title: {
        bsonType: 'string'
      },
      market_outlook_narrative: {
        bsonType: 'array',
        items: {
          bsonType: 'string'
        }
      },
      rationale: {
        bsonType: 'string'
      },
      analysis: {
        bsonType: 'string'
      },
      key_takeaways: {},
      sources: {
        bsonType: 'array',
        items: {
          bsonType: 'object',
          required: [
            'source_name',
            'source_title'
          ],
          properties: {
            source_name: {
              bsonType: 'string'
            },
            source_title: {
              bsonType: 'string'
            }
          }
        }
      },
      recommendations: {
        bsonType: 'array',
        items: {
          bsonType: 'object',
          required: [
            'ticker',
            'trade_direction',
            'bull_bear_score',
            'stop_loss',
            'target_price',
            'entry_price',
            'price'
          ],
          properties: {
            ticker: {
              bsonType: 'string'
            },
            trade_direction: {
              bsonType: 'string'
            },
            bull_bear_score: {
              bsonType: 'int',
              minimum: 1,
              maximum: 10
            },
            stop_loss: {
              bsonType: 'double'
            },
            target_price: {
              bsonType: 'double'
            },
            entry_price: {
              bsonType: 'double'
            },
            price: {
              bsonType: 'double'
            }
          }
        }
      },
      sentiment_score: {
        bsonType: 'double',
        minimum: 0,
        maximum: 1
      },
      market_impact: {
        bsonType: 'int',
        minimum: 1,
        maximum: 10
      },
      factors: {},
      timestamp_gmt: {
        bsonType: 'string',
        pattern: '^\\d{4}-\\d{2}-\\d{2}T\\d{2}:\\d{2}:\\d{2}(\\.\\d+)?Z$'
      },
      language_code: {
        bsonType: 'string',
        pattern: '^[a-z]{2}(-[A-Z]{2})?$'
      },
      importance: {
        bsonType: 'int',
        minimum: 1,
        maximum: 5
      },
      asset_class: {},
      region: {},
      tag: {
        'bsonType': 'string'
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

- FX: Foreign Exchange pairs
- IX: Indices
- EQ: Equities
- EN: Energy
- ME: Metals
- AG: Agriculture
- CR: Crypto

### Prompt output

The prompt should return the JSON object, including the following structure:
<pre>
 **JSON Output format**: YOUR RESPONSE MUST BE A VALID JSON OBJECT. DO NOT INCLUDE ANY ADDITIONAL TEXT OR EXPLANATIONS. With this exact structure: [title] as a string, [market_outlook_narrative] as an array of strings. [rationale] as a string. [market_impact] as an integer. [analysis] as a string in HTML format. [key_takeaways] as a string in HTML format. [sources] as an array of objects, where each object has, [source_name] as strong, [source_title] as a string, and [source_url] as a string. On the same level as [sources], [recommendations] as an array of objects, where each object has, [ticker] as a string, [trade_direction] as string, [bull_bear_score] as integer.
</pre>

The JSON output will be interpreted by the Alphagora engine, which will then process, transform, and securely store the data for further analysis and use within the system.