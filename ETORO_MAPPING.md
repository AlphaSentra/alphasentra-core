# eToro Data Mapping Documentation

This document describes how eToro instrument metadata is mapped to asset classes, regions, exchanges, and external platforms (Yahoo Finance and TradingView) within the AlphaSentra-core system.

## Data Flow Overview

```mermaid
graph TD
    subgraph "Ingestion"
        A[eToro API] -->|Fetch Metadata| B(db/etoro_instruments.py)
        B -->|Populate| C[(etoro_instruments collection)]
    end

    subgraph "Processing & Transformation"
        C --> D{Asset-Specific Scripts}
        D --> E[db/equities_data.py]
        D --> F[db/fx_data.py]
        D --> G[db/crypto_data.py]
        D --> H[db/commodities_data.py]
        
        E & F & G & H --> I[Filter & Deduplicate]
        I --> J[Region & Asset Mapping]
        J --> K[Symbol Translation]
        K --> L[Config Enrichment]
    end

    subgraph "Reference Data"
        M[(asset_classes)] -.-> J
        N[(regions)] -.-> J
        N -.-> K
        O[(_config.py)] -.-> L
    end

    subgraph "Result"
        L --> P[(tickers collection)]
        K --> Q[Yahoo Finance Symbol]
        K --> R[TradingView Symbol]
    end
```

## eToro Asset Class Identification

When pulling data from the eToro API, the `etoro_instrumentTypeId` is used to identify the instrument's asset class. The `asset_classes` collection stores this mapping.

### Collection: `asset_classes`

| etoro_instrumentTypeId | code | description |
|:---:|:---:|:---|
| 1 | FX | Forex |
| 5 | EQ | Equities |
| 6 | ETF | ETFs |
| 4 | IX | Indices |
| 2 | CO | Commodities |
| 10 | CR | Crypto |

**Usage:** Join the `etoro_instruments` collection with `asset_classes` using the `etoro_instrumentTypeId` field to determine the asset category.

---

## eToro Exchange & Region Mapping

The `regions` collection is used to map eToro's `etoro_exchangeID` to specific geographical regions, exchange names, and symbol formatting requirements for external platforms.

### Collection: `regions`

| eToro exchangeID | Region | Exchange Name | Yahoo Code | TradingView Code |
|:---:|:---|:---|:---:|:---|
| 1 | Global | FX | `=X` | |
| 2 | Global | Commodity | | |
| 3 | Global | Indices (CFD) | `^` | `INDEX:` |
| 4 | US | Nasdaq | | `NASDAQ:` |
| 5 | US | NYSE | | `NYSE:` |
| 6 | Germany | Frankfurt (Xetra) | `.DE` | `XETR:` |
| 7 | UK | London | `.L` | `LSE:` |
| 8 | Global | Crypto | `-USD` | `USD` |
| 9 | France | Paris | `.PA` | `EURONEXT:` |
| 10 | Spain | Madrid | `.MC` | `BME:` |
| 11 | Italy | Borsa Italiana | `.MI` | `MIL:` |
| 12 | Switzerland | Zurich | `.SW` | `SIX:` |
| 14 | Norway | Oslo | `.OL` | `OSL:` |
| 15 | Sweden | Stockholm | `.ST` | `OMXSTO:` |
| 16 | Denmark | Copenhagen | `.CO` | `OMXCOP:` |
| 17 | Finland | Helsinki | `.HE` | `OMXHEX:` |
| 20 | US | Chicago (CME/CBOT) | | `CME:` |
| 21 | Hong Kong | Hong Kong | `.HK` | `HKEX:` |
| 22 | Portugal | Lisbon | `.LS` | `EURONEXT:` |
| 23 | Belgium | Brussels | `.BR` | `EURONEXT:` |
| 24 | Saudi Arabia | Tadawul | `.SR` | `TADAWUL:` |
| 30 | Netherlands | Amsterdam | `.AS` | `EURONEXT:` |
| 31 | Australia | ASX (Sydney) | `.AX` | `ASX:` |
| 32 | Austria | Vienna | `.VI` | `VIE:` |
| 33 | Ireland | Dublin | `.IR` | `EURONEXT:` |
| 34 | Global | ETFs (CFD) | | `AMEX:` |
| 38 | Germany | Xetra ETFs | `.DE` | `XETR:` |
| 39 | UAE | Dubai | `.DU` | `DFM:` |
| 40 | Global | Commodities | `=F` | `COMEX:` |
| 41 | UAE | Abu Dhabi | `.AD` | `ADX:` |
| 42 | UK | LSE AIM | `.L` | `LSE:` |
| 56 | Japan | Tokyo | `.T` | `TSE:` |

---

## eToro Instruments Import Process

The `db/etoro_instruments.py` script orchestrates the full lifecycle of importing eToro instrument metadata into the database. The process involves fetching data from the eToro API, staging it in the `etoro_instruments` collection, identifying instruments not yet in the main `tickers` collection, and presenting them for review.

### Import Workflow

```mermaid
graph TD
    A[Start: run_import_etoro_instruments_with_confirmation] --> B{Connect to MongoDB?};
    B-- Yes --> C[Get DatabaseManager and DB instance];
    B-- No --> C;
    C --> D[Call import_etoro_instruments];
    D --> E[Fetch instruments from ETORO_API_INSTRUMENTS_METADATA];
    E --> F{Parse API Response: List or Dict?};
    F --> G{No instruments found?};
    G-- Yes --> H[Log Error and Return False];
    G-- No --> I[Log Success: Fetched X instruments];
    I --> J[Clear existing data from 'etoro_instruments' collection];
    J --> K[Insert fetched instruments into 'etoro_instruments' collection in batches of 1000];
    K --> L[Call create_excluded_etoro_instruments_collection];
    L --> M[Fetch existing 'ticker_etoro' from 'tickers' collection];
    M --> N[Fetch existing 'SymbolFull' from 'etoro_instruments_excluded' collection];
    N --> O{Find instruments in 'etoro_instruments' that are NOT in 'tickers' AND NOT already in 'etoro_instruments_excluded'};
    O --> P[Add 'excluded: False' to new instruments];
    P --> Q[Insert new excluded instruments into 'etoro_instruments_excluded' collection in batches];
    Q --> R[Call display_non_excluded_instruments];
    R --> S[Display table of non-excluded instruments to user];
    S --> T{User selects action: 1/2/3/4};
    T -- 1: Exclude --> U[Call set_etoro_instrument_excluded_status excluded=True];
    T -- 2: Remove --> V[Delete instruments with excluded=False from 'etoro_instruments_excluded'];
    T -- 3: Keep --> W[Log: Keeping instruments];
    T -- 4: Export JSON --> X[Call export_non_excluded_to_json];
    U --> Y[End Process];
    V --> Y;
    W --> Y;
    X --> Y;
    H --> Y;
```

### Step-by-Step Explanation

1. **Fetch from eToro API**: The script calls `import_etoro_instruments()` which sends an HTTP GET request to the eToro API endpoint configured in `_config.py` (`ETORO_API_INSTRUMENTS_METADATA`). The response is parsed to extract a list of instruments.

2. **Populate `etoro_instruments` collection**: All existing documents in the `etoro_instruments` collection are deleted, and the freshly fetched instruments are inserted in batches of 1000. This collection serves as the raw source of truth for all available eToro instruments.

3. **Build `etoro_instruments_excluded` collection**: The `create_excluded_etoro_instruments_collection()` function identifies instruments that exist in `etoro_instruments` but are **not** yet present in the `tickers` collection. These are instruments that are candidates for promotion to `tickers`. They are inserted into the `etoro_instruments_excluded` collection with `excluded: False` to mark them as pending review. Already existing entries are skipped to avoid duplicates.

4. **Review and Action**: The `display_non_excluded_instruments()` function shows the user a formatted table of all instruments currently pending review (`excluded: False`). The user is then prompted with four options:

   **1. Exclude them (set `excluded = True`)**
   - What it does: Marks all displayed instruments as `excluded: True` in the `etoro_instruments_excluded` collection.
   - Effect: These instruments will **not** appear in future review cycles.
   - Use when: You want to permanently ignore these instruments and never import them into `tickers`.

   **2. Remove them (delete from excluded collection)**
   - What it does: Deletes the displayed instruments from `etoro_instruments_excluded` entirely.
   - Effect: On the next import run, these instruments will **reappear** in the review list (with `excluded: False`) as long as they still exist in `etoro_instruments` and remain absent from `tickers`.
   - Use when: You accidentally included them, or you want to "undo" their staging to reconsider later. **Does not import them into `tickers`.**

   **3. Keep them (do nothing)**
   - What it does: Takes no action. The instruments remain in `etoro_instruments_excluded` with `excluded: False`.
   - Effect: They will appear again in the next review cycle for you to decide.
   - Use when: You are not ready to make a decision yet and want to review them again later. **Does not import them into `tickers`.**

   **4. Download Importable JSON**
   - What it does: Exports all non-excluded instruments to a file named `etoro_importable.json`. Each instrument is enriched with:
     - `ticker`, `ticker_tradingview`, `ticker_etoro`
     - `asset_class`, `region`
     - `prompt`, `factors`, `model_function`, `model_name`
   - Effect: Creates a ready-to-import JSON file.
   - Use when: You want to **import these instruments into the `tickers` collection**. After generating the JSON, you must import it using the appropriate asset-specific script or manually into MongoDB.

5. **How to import into `tickers`**: The `etoro_importable.json` file produced by option 4 is the **only path to import instruments into `tickers`** from this workflow.
   - After choosing option 4, run the relevant asset-specific import script (e.g., `equities_data.py`, `fx_data.py`, `crypto_data.py`, `commodities_data.py`) which will read from `etoro_importable.json` or directly insert into `tickers` with proper validation, deduplication, and region/symbol resolution.
   - Alternatively, you can manually import the JSON contents into the `tickers` collection in MongoDB.

### Important Notes

- **Options 1, 2, and 3 do NOT import instruments into `tickers`.** They only manage the staging collection (`etoro_instruments_excluded`).
- **Option 4 is the only action that prepares instruments for import into `tickers`.** It generates the structured JSON file that can then be imported by the asset-specific scripts.
- **Removing from `etoro_instruments_excluded` (option 2) does not automatically import to `tickers`.** If you remove an instrument, it will reappear in the next import cycle (with `excluded: False`) as long as it still exists in `etoro_instruments` and remains absent from `tickers`.

## Ticker Import Process

The system automates the promotion of instruments from the raw `etoro_instruments` collection to the active `tickers` collection using specialized scripts for each asset class.

### 1. Raw Data Ingestion
The `db/etoro_instruments.py` script fetches the latest metadata from the eToro API and overwrites the `etoro_instruments` collection.

### 2. Transformation & Filtering
Specific scripts (e.g., `db/equities_data.py`, `db/fx_data.py`, etc.) perform the following transformations to populate the `tickers` collection:

- **Filtering:** Only non-internal instruments (`isInternalInstrument: false`) matching the relevant `instrumenttypeID` are processed.
- **Deduplication:** The script checks if `ticker_etoro` already exists in the `tickers` collection before inserting.
- **Region Resolution:** The `exchangeID` from the eToro document is cross-referenced with the `regions` collection to assign a geographical region.
- **Symbol Translation:** The `helpers.get_ticker_exchange_mapping()` function is called to generate platform-specific symbols for Yahoo Finance and TradingView based on the exchange mapping.
- **Config Enrichment:** Prompts, factor models, and model functions are assigned based on the asset class (defined in `_config.py`).

### Asset-Specific Scripts
| Asset Class | Script | Key Logic |
|:---|:---|:---|
| Equities/ETFs | `db/equities_data.py` | Maps exchange IDs to regions; handles both EQ and ETF types. |
| FX | `db/fx_data.py` | Sets 4 decimal places; assigns `run_fx_model`. |
| Crypto | `db/crypto_data.py` | Sets Global region; uses suffix mapping for TradingView. |
| Commodities | `db/commodities_data.py` | Categorizes into Energy (EN), Agriculture (AG), or Metals (ME) based on keywords in the symbol name. |

---

## Symbol Construction Logic

The `regions` collection enables the translation of eToro base symbols to other platforms via the `get_ticker_exchange_mapping` helper:

### 1. Yahoo Finance (yfinance)
- **Forex:** `SYMBOL + yahoo_finance_exchange_code` (e.g., `EURUSD=X`)
- **Indices:** `yahoo_finance_exchange_code + SYMBOL` (e.g., `^GSPC`)
- **Commodities:** `SYMBOL + yahoo_finance_exchange_code` (e.g., `GC=F`)
- **Equities:** `SYMBOL + yahoo_finance_exchange_code` (e.g., `SAP.DE`, `BP.L`)
- **Crypto:** `SYMBOL + yahoo_finance_exchange_code` (e.g., `BTC-USD`)

### 2. TradingView
- **Equities/Indices:** `tradingview_exchange_code + SYMBOL` (e.g., `NASDAQ:AAPL`, `INDEX:SPX`)
- **Crypto:** `SYMBOL + tradingview_exchange_code` (e.g., `BTCUSD`)

## Implementation Details
The source of truth for the initial mapping data is defined in [`db/create_mongodb_db.py`](db/create_mongodb_db.py). The orchestration of the import process is managed by the `create_alphasentra_database` function in the same file.
