"""
Seed data for the tool definitions and agents.
This module defines the tools and agents used in the multi-agent demo.
"""

# Tool definitions with rich metadata
TOOLS = [
    {
        "name": "get_weather",
        "description": "Fetch current weather conditions for a given location including temperature, humidity, and forecast",
        "parameters": {
            "location": "string (required) - City name or coordinates",
            "units": "string (optional) - 'celsius' or 'fahrenheit', defaults to 'celsius'"
        },
        "category": "weather",
        "version": "1.0"
    },
    {
        "name": "format_weather_response",
        "description": "Format weather data into a human-readable message with emojis and styling",
        "parameters": {
            "weather_data": "object (required) - Output from get_weather",
            "style": "string (optional) - 'casual', 'formal', or 'detailed'"
        },
        "category": "formatting",
        "version": "1.0"
    },
    {
        "name": "send_notification",
        "description": "Send a notification to a user through multiple channels (email, SMS, push)",
        "parameters": {
            "user_id": "string (required) - Target user identifier",
            "message": "string (required) - Notification content",
            "channels": "array (required) - List of channels: ['email', 'sms', 'push']"
        },
        "category": "communication",
        "version": "1.0"
    },
    {
        "name": "fetch_stock_price",
        "description": "Get real-time stock price and trading volume for a given symbol",
        "parameters": {
            "symbol": "string (required) - Stock ticker symbol (e.g., AAPL, GOOGL)",
            "market": "string (optional) - 'NYSE', 'NASDAQ', defaults to 'NASDAQ'"
        },
        "category": "finance",
        "version": "1.0"
    },
    {
        "name": "fetch_news",
        "description": "Fetch latest news articles related to a topic or company",
        "parameters": {
            "query": "string (required) - Search query or company name",
            "max_results": "integer (optional) - Max articles to return, defaults to 5"
        },
        "category": "information",
        "version": "1.0"
    },
    {
        "name": "process_payment",
        "description": "Process a payment transaction through the payment gateway",
        "parameters": {
            "amount": "number (required) - Transaction amount",
            "currency": "string (required) - ISO currency code",
            "payment_method": "string (required) - 'credit_card', 'debit_card', 'paypal'"
        },
        "category": "commerce",
        "version": "1.0"
    },
    {
        "name": "validate_inventory",
        "description": "Check product availability in warehouse inventory",
        "parameters": {
            "product_id": "string (required) - Product identifier",
            "quantity": "integer (required) - Requested quantity"
        },
        "category": "commerce",
        "version": "1.0"
    },
    {
        "name": "calculate_shipping",
        "description": "Calculate shipping cost and estimated delivery time based on destination and weight",
        "parameters": {
            "destination": "string (required) - Shipping address or zone",
            "weight": "number (required) - Package weight in kg",
            "carrier": "string (optional) - 'fedex', 'ups', 'usps', defaults to 'best_price'"
        },
        "category": "commerce",
        "version": "1.0"
    },
    {
        "name": "send_email",
        "description": "Send an email to a user with subject and body",
        "parameters": {
            "to": "string (required) - Recipient email address",
            "subject": "string (required) - Email subject line",
            "body": "string (required) - Email content in plain text or HTML"
        },
        "category": "communication",
        "version": "1.0"
    },
    {
        "name": "send_sms",
        "description": "Send SMS notification to a phone number",
        "parameters": {
            "phone_number": "string (required) - Recipient phone number",
            "message": "string (required) - SMS content (max 160 chars)"
        },
        "category": "communication",
        "version": "1.0"
    },
    {
        "name": "slack_message",
        "description": "Post a message to a Slack channel",
        "parameters": {
            "channel": "string (required) - Slack channel name or ID",
            "message": "string (required) - Message content",
            "thread_ts": "string (optional) - Reply in thread"
        },
        "category": "communication",
        "version": "1.0"
    },
    {
        "name": "push_notification",
        "description": "Send push notification to mobile app user",
        "parameters": {
            "user_id": "string (required) - User device token",
            "title": "string (required) - Notification title",
            "body": "string (required) - Notification body"
        },
        "category": "communication",
        "version": "1.0"
    }
]

# Agent definitions
AGENTS = [
    {
        "name": "orchestrator",
        "role": "coordinator",
        "capabilities": ["weather", "communication", "information"],
        "description": "Main orchestration agent that coordinates sub-agents and tools"
    },
    {
        "name": "finance_agent",
        "role": "specialist",
        "capabilities": ["finance", "commerce"],
        "description": "Specialized agent for financial operations and transactions"
    },
    {
        "name": "notification_agent",
        "role": "specialist",
        "capabilities": ["communication"],
        "description": "Specialized agent for multi-channel user notifications"
    }
]

# Simulated execution chains for demo
EXECUTION_SCENARIOS = [
    {
        "scenario": "weather_inquiry",
        "description": "User asks about weather - chained execution",
        "agent": "orchestrator",
        "executions": [
            {
                "tool_name": "get_weather",
                "input": {"location": "San Francisco, CA", "units": "celsius"},
                "output": {"temp": 18, "humidity": 65, "condition": "partly_cloudy"},
                "status": "success",
                "next_tool": "format_weather_response"
            },
            {
                "tool_name": "format_weather_response",
                "input": {"weather_data": {"temp": 18, "humidity": 65}},
                "output": {"message": "Partly cloudy, 18°C with 65% humidity"},
                "status": "success",
                "next_tool": "send_notification",
                "is_chain_child": True
            },
            {
                "tool_name": "send_notification",
                "input": {"user_id": "user_123", "message": "Weather update", "channels": ["push"]},
                "output": {"delivered": True},
                "status": "success",
                "is_chain_child": True
            }
        ]
    },
    {
        "scenario": "multi_source_data",
        "description": "Fetch data from multiple sources in parallel",
        "agent": "orchestrator",
        "executions": [
            {
                "tool_name": "fetch_stock_price",
                "input": {"symbol": "AAPL"},
                "output": {"price": 178.50, "change": 2.3},
                "status": "success",
                "is_parallel": True,
                "parallel_with": "fetch_news"
            },
            {
                "tool_name": "fetch_news",
                "input": {"query": "Apple Inc"},
                "output": {"articles": [{"title": "Apple announces new product"}]},
                "status": "success",
                "is_parallel": True,
                "parallel_with": "fetch_stock_price"
            }
        ]
    },
    {
        "scenario": "checkout_failure",
        "description": "Checkout flow with simulated payment failure",
        "agent": "finance_agent",
        "executions": [
            {
                "tool_name": "validate_inventory",
                "input": {"product_id": "prod_456", "quantity": 2},
                "output": {"available": True, "stock": 15},
                "status": "success",
                "is_parallel": True,
                "parallel_with": "calculate_shipping"
            },
            {
                "tool_name": "calculate_shipping",
                "input": {"destination": "New York, NY", "weight": 1.5},
                "output": {"cost": 12.99, "days": 3},
                "status": "success",
                "is_parallel": True,
                "parallel_with": "validate_inventory"
            },
            {
                "tool_name": "process_payment",
                "input": {"amount": 125.99, "currency": "USD", "payment_method": "credit_card"},
                "output": None,
                "status": "failed",
                "error": "Card declined: insufficient funds",
                "is_parallel": True,
                "parallel_with": "calculate_shipping"
            }
        ]
    },
    {
        "scenario": "notification_discovery",
        "description": "Find similar communication tools",
        "agent": "notification_agent",
        "executions": [
            {
                "tool_name": "send_email",
                "input": {"to": "user@example.com", "subject": "Hello", "body": "Test message"},
                "output": {"sent": True, "message_id": "msg_123"},
                "status": "success"
            }
        ]
    }
]
