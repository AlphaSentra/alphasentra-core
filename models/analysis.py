import os
import re
import json
from genAI.ai_prompt import get_gen_ai_response
from _config import INSTRUMENT_DESCRIPTION_PROMPT
from crypt import decrypt_string
from logging_utils import log_error
from helpers import DatabaseManager
from data.price import calculate_performance_metrics


def run_analysis(ticker, instrument_name):
    """
    Analyze instrument using AI to extract description and sector.
    Returns JSON with 'description' and 'sector' fields.
    """
    # Decrypt and format the prompt
    decrypted_prompt = decrypt_string(INSTRUMENT_DESCRIPTION_PROMPT)
    if not decrypted_prompt:
        return {
            "description": "Prompt decryption failed",
            "sector": ""
        }
    
    # Format prompt with instrument details
    full_prompt = decrypted_prompt.format(
        tickers_str=ticker,
        instrument_name=instrument_name
    )
    
    # Get AI response
    response_text = get_gen_ai_response(
        tickers=[ticker],
        model_strategy="Analysis",
        prompt=full_prompt,
        gemini_model="gemini-2.5-flash"
    )
    
    try:
        # Extract JSON from markdown code block if present
        json_match = re.search(r'```json\s*({.*?})\s*```', response_text, re.DOTALL)
        if json_match:
            response_text = json_match.group(1)

        # Parse cleaned JSON response
        response_data = json.loads(response_text)
        description = response_data.get("description", "")
        sector = response_data.get("sector", "")
        valid_grades = {'A', 'B', 'C', 'D', 'E', 'F'}
        
        cashflow_health = response_data.get("cashflow_health", "")
        if cashflow_health not in valid_grades:
            cashflow_health = "-"
            
        profit_health = response_data.get("profit_health", "")
        if profit_health not in valid_grades:
            profit_health = "-"
            
        price_momentum = response_data.get("price_momentum", "")
        if price_momentum not in valid_grades:
            price_momentum = "-"
            
        growth_health = response_data.get("growth_health", "")
        if growth_health not in valid_grades:
            growth_health = "-"
        dividend_yield = response_data.get("dividend_yield", "")

        # Growth and Profitability bar and line chart
        gpc_chart_key = "growth_profitability_chart"
        gpc_chart = response_data.get(gpc_chart_key, {})
        gpc_title = gpc_chart.get("title", "")
        gpc_x_label = gpc_chart.get("xAxis", {}).get("label", "")
        gpc_x_categories = gpc_chart.get("xAxis", {}).get("categories", [])
        gpc_y_axes = gpc_chart.get("yAxes", [])
        gpc_y_axis_amount = gpc_y_axes[0].get("label", "") if len(gpc_y_axes) > 0 else ""
        gpc_y_axis_margin = gpc_y_axes[1].get("label", "") if len(gpc_y_axes) > 1 else ""
        gpc_series_list = gpc_chart.get("series", [])
        gpc_revenue_series = gpc_series_list[0] if len(gpc_series_list) > 0 else {}
        gpc_net_income_series = gpc_series_list[1] if len(gpc_series_list) > 1 else {}
        gpc_net_margin_series = gpc_series_list[2] if len(gpc_series_list) > 2 else {}
        gpc_revenue_name = gpc_revenue_series.get("name", "")
        gpc_revenue_type = gpc_revenue_series.get("type", "")
        gpc_revenue_axis = gpc_revenue_series.get("yAxisId", "")
        gpc_revenue_data = gpc_revenue_series.get("data", [])
        gpc_net_income_name = gpc_net_income_series.get("name", "")
        gpc_net_income_type = gpc_net_income_series.get("type", "")
        gpc_net_income_axis = gpc_net_income_series.get("yAxisId", "")
        gpc_net_income_data = gpc_net_income_series.get("data", [])
        gpc_net_margin_name = gpc_net_margin_series.get("name", "")
        gpc_net_margin_type = gpc_net_margin_series.get("type", "")
        gpc_net_margin_axis = gpc_net_margin_series.get("yAxisId", "")
        gpc_net_margin_data = gpc_net_margin_series.get("data", [])

        # Financial Health bar chart
        fhc_chart_key = "financial_health_chart"
        fhc_chart = response_data.get(fhc_chart_key, {})
        fhc_title = fhc_chart.get("title", "")
        fhc_x_label = fhc_chart.get("xAxis", {}).get("label", "")
        fhc_x_categories = fhc_chart.get("xAxis", {}).get("categories", [])
        fhc_y_axis = fhc_chart.get("yAxis", {})
        fhc_y_axis_label = fhc_y_axis.get("label", "")
        fhc_y_axis_type = fhc_y_axis.get("type", "")
        fhc_series_list = fhc_chart.get("series", [])
        fhc_debt_series = fhc_series_list[0] if len(fhc_series_list) > 0 else {}
        fhc_free_cash_flow_series = fhc_series_list[1] if len(fhc_series_list) > 1 else {}
        fhc_cash_equivalents_series = fhc_series_list[2] if len(fhc_series_list) > 2 else {}
        fhc_debt_name = fhc_debt_series.get("name", "")
        fhc_debt_type = fhc_debt_series.get("type", "")
        fhc_debt_data = fhc_debt_series.get("data", [])
        fhc_free_cash_flow_name = fhc_free_cash_flow_series.get("name", "")
        fhc_free_cash_flow_type = fhc_free_cash_flow_series.get("type", "")
        fhc_free_cash_flow_data = fhc_free_cash_flow_series.get("data", [])
        fhc_cash_equivalents_name = fhc_cash_equivalents_series.get("name", "")
        fhc_cash_equivalents_type = fhc_cash_equivalents_series.get("type", "")
        fhc_cash_equivalents_data = fhc_cash_equivalents_series.get("data", [])

        # Capital Structure pie chart
        csc_chart_key = "capital_structure_chart"
        csc_chart = response_data.get(csc_chart_key, {})
        csc_title = csc_chart.get("title", "")
        csc_chart_type = csc_chart.get("type", "")
        csc_series_list = csc_chart.get("series", [])
        csc_equity_series = csc_series_list[0] if len(csc_series_list) > 0 else {}
        csc_debt_series = csc_series_list[1] if len(csc_series_list) > 1 else {}
        csc_current_assets_series = csc_series_list[2] if len(csc_series_list) > 2 else {}
        csc_equity_name = csc_equity_series.get("name", "")
        csc_equity_value = csc_equity_series.get("value", 0)
        csc_debt_name = csc_debt_series.get("name", "")
        csc_debt_value = csc_debt_series.get("value", 0)
        csc_current_assets_name = csc_current_assets_series.get("name", "")
        csc_current_assets_value = csc_current_assets_series.get("value", 0)
        
        # Dividend History bar and line chart
        dhc_chart_key = "dividend_history_chart"
        dhc_chart = response_data.get(dhc_chart_key, {})
        dhc_title = dhc_chart.get("title", "")
        dhc_x_label = dhc_chart.get("xAxis", {}).get("label", "")
        dhc_x_categories = dhc_chart.get("xAxis", {}).get("categories", [])
        dhc_y_axes = dhc_chart.get("yAxes", [])
        dhc_y_axis_dividend = dhc_y_axes[0].get("label", "") if len(dhc_y_axes) > 0 else ""
        dhc_y_axis_dividend_type = dhc_y_axes[0].get("type", "") if len(dhc_y_axes) > 0 else ""
        dhc_y_axis_yield = dhc_y_axes[1].get("label", "") if len(dhc_y_axes) > 1 else ""
        dhc_y_axis_yield_type = dhc_y_axes[1].get("type", "") if len(dhc_y_axes) > 1 else ""
        dhc_series_list = dhc_chart.get("series", [])
        dhc_dividend_series = dhc_series_list[0] if len(dhc_series_list) > 0 else {}
        dhc_yield_series = dhc_series_list[1] if len(dhc_series_list) > 1 else {}
        dhc_dividend_name = dhc_dividend_series.get("name", "")
        dhc_dividend_type = dhc_dividend_series.get("type", "")
        dhc_dividend_axis = dhc_dividend_series.get("yAxisId", "")
        dhc_dividend_data = dhc_dividend_series.get("data", [])
        dhc_yield_name = dhc_yield_series.get("name", "")
        dhc_yield_type = dhc_yield_series.get("type", "")
        dhc_yield_axis = dhc_yield_series.get("yAxisId", "")
        dhc_yield_data = dhc_yield_series.get("data", [])

        # Update tickers collection in MongoDB with description, sector and performance
        try:            
            # Get performance data first
            # Ensure we pass a single ticker string
            ticker_str = ticker[0] if isinstance(ticker, list) else ticker
            performance_data = calculate_performance_metrics(ticker_str)
            
            client = DatabaseManager().get_client()
            db = client[os.getenv("MONGODB_DATABASE", "alphagora")]
            tickers_coll = db['tickers']
            
            # Combine both updates into a single operation
            tickers_coll.update_one(
                {"ticker": ticker},
                {"$set": {
                    "description": description,
                    "sector": sector,
                    "1y": performance_data.get('1y', 0.0),
                    "6m": performance_data.get('6m', 0.0),
                    "3m": performance_data.get('3m', 0.0),
                    "1m": performance_data.get('1m', 0.0),
                    "1d": performance_data.get('1d', 0.0),
                    "cashflow_health": cashflow_health,
                    "profit_health": profit_health,
                    "price_momentum": price_momentum,
                    "growth_health": growth_health,
                    "dividend_yield": dividend_yield,
                    "financial_health_chart": {
                        "title": fhc_title,
                        "xAxis": {
                            "label": fhc_x_label,
                            "categories": fhc_x_categories
                        },
                        "yAxis": {
                            "label": fhc_y_axis_label,
                            "type": fhc_y_axis_type
                        },
                        "series": [
                            {
                                "name": fhc_debt_name,
                                "type": fhc_debt_type,
                                "data": fhc_debt_data
                            },
                            {
                                "name": fhc_free_cash_flow_name,
                                "type": fhc_free_cash_flow_type,
                                "data": fhc_free_cash_flow_data
                            },
                            {
                                "name": fhc_cash_equivalents_name,
                                "type": fhc_cash_equivalents_type,
                                "data": fhc_cash_equivalents_data
                            }
                        ]
                    },
                    "growth_profitability_chart": {
                        "title": gpc_title,
                        "xAxis": {
                            "label": gpc_x_label,
                            "categories": gpc_x_categories
                        },
                        "yAxes": [
                            {
                                "label": gpc_y_axis_amount
                            },
                            {
                                "label": gpc_y_axis_margin
                            }
                        ],
                        "series": [
                            {
                                "name": gpc_revenue_name,
                                "type": gpc_revenue_type,
                                "yAxisId": gpc_revenue_axis,
                                "data": gpc_revenue_data
                            },
                            {
                                "name": gpc_net_income_name,
                                "type": gpc_net_income_type,
                                "yAxisId": gpc_net_income_axis,
                                "data": gpc_net_income_data
                            },
                            {
                                "name": gpc_net_margin_name,
                                "type": gpc_net_margin_type,
                                "yAxisId": gpc_net_margin_axis,
                                "data": gpc_net_margin_data
                            }
                        ]
                    },
                    "capital_structure_chart": {
                        "title": csc_title,
                        "type": csc_chart_type,
                        "series": [
                            {
                                "name": csc_equity_name,
                                "value": csc_equity_value
                            },
                            {
                                "name": csc_debt_name,
                                "value": csc_debt_value
                            },
                            {
                                "name": csc_current_assets_name,
                                "value": csc_current_assets_value
                            }
                        ]
                    },
                    "dividend_history_chart": {
                        "title": dhc_title,
                        "xAxis": {
                            "label": dhc_x_label,
                            "categories": dhc_x_categories
                        },
                        "yAxes": [
                            {
                                "label": dhc_y_axis_dividend,
                                "type": dhc_y_axis_dividend_type
                            },
                            {
                                "label": dhc_y_axis_yield,
                                "type": dhc_y_axis_yield_type
                            }
                        ],
                        "series": [
                            {
                                "name": dhc_dividend_name,
                                "type": dhc_dividend_type,
                                "yAxisId": dhc_dividend_axis,
                                "data": dhc_dividend_data
                            },
                            {
                                "name": dhc_yield_name,
                                "type": dhc_yield_type,
                                "yAxisId": dhc_yield_axis,
                                "data": dhc_yield_data
                            }
                        ]
                    }
                }}
            )

        except Exception as e:
            log_error(f"Error updating ticker document: {str(e)}", "DB_UPDATE", e)

        return {
            "description": description,
            "sector": sector
        }
    
    except json.JSONDecodeError as e:
        log_error(f"Failed to parse AI response: {response_text}", "JSON_PARSE", e)
        return
