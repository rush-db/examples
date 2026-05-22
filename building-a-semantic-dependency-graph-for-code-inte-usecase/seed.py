"""
seed.py - Generates a realistic code dependency graph for change impact analysis.

This script creates a mock microservice codebase with:
- Services (API endpoints)
- Utility functions (shared code)
- Business logic functions
- Test files
- Structural relationships (calls, depends_on, tests)

The scenario: a shared utility `format_currency` is modified.
We seed data so it has direct callers, transitive dependents, and tests.
"""

import os
import random
from dotenv import load_dotenv

load_dotenv()

from rushdb import RushDB

# Check for API key
API_KEY = os.getenv("RUSHDB_API_KEY")
if not API_KEY:
    print("ERROR: RUSHDB_API_KEY not found in environment")
    print("Copy .env.example to .env and fill in your API key")
    exit(1)

db = RushDB(API_KEY)

# Sample code snippets for realistic data
UTILITY_FUNCTIONS = [
    {
        "name": "format_currency",
        "signature": "format_currency(amount: float, currency: str = 'USD') -> str",
        "file_path": "src/utils/formatters.py",
        "description": "Formats a numeric amount as a currency string with locale-aware formatting",
        "body": "def format_currency(amount, currency='USD'): return f'{currency} {amount:.2f}'"
    },
    {
        "name": "parse_date",
        "signature": "parse_date(date_str: str, format: str = '%Y-%m-%d') -> datetime",
        "file_path": "src/utils/date_utils.py",
        "description": "Parses a date string into a datetime object with flexible format support",
        "body": "def parse_date(date_str, format='%Y-%m-%d'): from datetime import datetime; return datetime.strptime(date_str, format)"
    },
    {
        "name": "validate_email",
        "signature": "validate_email(email: str) -> bool",
        "file_path": "src/utils/validators.py",
        "description": "Validates email addresses using regex pattern matching",
        "body": "def validate_email(email): import re; return bool(re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$', email))"
    },
    {
        "name": "generate_id",
        "signature": "generate_id(prefix: str = '') -> str",
        "file_path": "src/utils/id_generator.py",
        "description": "Generates unique identifiers with optional prefix for namespacing",
        "body": "def generate_id(prefix=''): import uuid; return f'{prefix}{uuid.uuid4().hex[:12]}'"
    },
]

BUSINESS_LOGIC = [
    {
        "name": "calculate_order_total",
        "signature": "calculate_order_total(items: list[dict], tax_rate: float) -> float",
        "file_path": "src/services/pricing.py",
        "description": "Calculates the total price of an order including tax and discounts",
        "body": "def calculate_order_total(items, tax_rate): return sum(i['price'] * i['qty'] for i in items) * (1 + tax_rate)"
    },
    {
        "name": "apply_discount",
        "signature": "apply_discount(price: float, discount_percent: float) -> float",
        "file_path": "src/services/pricing.py",
        "description": "Applies a percentage discount to a price value",
        "body": "def apply_discount(price, discount_percent): return price * (1 - discount_percent / 100)"
    },
    {
        "name": "process_payment",
        "signature": "process_payment(amount: float, method: str, metadata: dict) -> dict",
        "file_path": "src/services/payment.py",
        "description": "Processes payment transactions through various payment methods",
        "body": "def process_payment(amount, method, metadata): return {'status': 'success', 'transaction_id': generate_id('txn_')}"
    },
    {
        "name": "send_invoice",
        "signature": "send_invoice(customer_id: str, invoice_data: dict) -> bool",
        "file_path": "src/services/invoicing.py",
        "description": "Sends invoice emails to customers with payment details",
        "body": "def send_invoice(customer_id, invoice_data): return True"
    },
    {
        "name": "calculate_shipping",
        "signature": "calculate_shipping(weight: float, destination: str) -> float",
        "file_path": "src/services/shipping.py",
        "description": "Calculates shipping costs based on package weight and destination",
        "body": "def calculate_shipping(weight, destination): return weight * 2.5 if destination == 'domestic' else weight * 5.0"
    },
    {
        "name": "generate_receipt",
        "signature": "generate_receipt(order_id: str, items: list[dict]) -> str",
        "file_path": "src/services/receipts.py",
        "description": "Generates a formatted receipt string for an order",
        "body": "def generate_receipt(order_id, items): return f'RECEIPT {order_id}'"
    },
    {
        "name": "estimate_delivery",
        "signature": "estimate_delivery(shipping_method: str, destination: str) -> int",
        "file_path": "src/services/shipping.py",
        "description": "Estimates delivery days based on shipping method and destination",
        "body": "def estimate_delivery(shipping_method, destination): return {'standard': 7, 'express': 2}[shipping_method]"
    },
    {
        "name": "format_invoice_number",
        "signature": "format_invoice_number(invoice_id: str) -> str",
        "file_path": "src/utils/formatters.py",
        "description": "Formats invoice IDs into human-readable invoice numbers",
        "body": "def format_invoice_number(invoice_id): return f'INV-{invoice_id.upper()}'"
    },
]

API_ENDPOINTS = [
    {
        "name": "checkout_endpoint",
        "signature": "POST /api/checkout",
        "file_path": "src/api/checkout.py",
        "description": "Handles checkout requests and processes payments",
        "body": "@app.post('/checkout')
def checkout(request): result = process_payment(request['amount'], request['method'], request['metadata']); return result"
    },
    {
        "name": "orders_endpoint",
        "signature": "GET /api/orders/{order_id}",
        "file_path": "src/api/orders.py",
        "description": "Retrieves order details including pricing and shipping info",
        "body": "@app.get('/orders/{order_id}')
def get_order(order_id): order = fetch_order(order_id); return format_currency(order['total'])"
    },
    {
        "name": "invoices_endpoint",
        "signature": "POST /api/invoices",
        "file_path": "src/api/invoices.py",
        "description": "Creates and sends invoices to customers",
        "body": "@app.post('/invoices')
def create_invoice(data): inv = create_invoice_record(data); return send_invoice(customer_id, inv)"
    },
    {
        "name": "shipping_quote_endpoint",
        "signature": "POST /api/shipping/quote",
        "file_path": "src/api/shipping.py",
        "description": "Returns shipping cost estimates for given parameters",
        "body": "@app.post('/shipping/quote')
def quote_shipping(data): cost = calculate_shipping(data['weight'], data['destination']); return {'cost': format_currency(cost)}"
    },
]

TESTS = [
    {
        "name": "test_format_currency",
        "signature": "test_format_currency()",
        "file_path": "tests/test_formatters.py",
        "description": "Unit tests for currency formatting function",
        "body": "def test_format_currency(): assert format_currency(100) == 'USD 100.00'; assert format_currency(99.99) == 'USD 99.99'"
    },
    {
        "name": "test_calculate_order_total",
        "signature": "test_calculate_order_total()",
        "file_path": "tests/test_pricing.py",
        "description": "Tests for order total calculation including tax",
        "body": "def test_calculate_order_total(): items = [{'price': 10, 'qty': 2}]; assert calculate_order_total(items, 0.1) == 22.0"
    },
    {
        "name": "test_checkout_flow",
        "signature": "test_checkout_flow()",
        "file_path": "tests/test_checkout.py",
        "description": "End-to-end checkout integration test",
        "body": "def test_checkout_flow(): result = checkout_endpoint({'amount': 50, 'method': 'card'}); assert result['status'] == 'success'"
    },
    {
        "name": "test_shipping_calculation",
        "signature": "test_shipping_calculation()",
        "file_path": "tests/test_shipping.py",
        "description": "Tests shipping cost calculations",
        "body": "def test_shipping_calculation(): assert calculate_shipping(5, 'domestic') == 12.5"
    },
    {
        "name": "test_receipt_generation",
        "signature": "test_receipt_generation()",
        "file_path": "tests/test_receipts.py",
        "description": "Tests receipt text generation",
        "body": "def test_receipt_generation(): receipt = generate_receipt('order123', []); assert 'order123' in receipt"
    },
]

def clear_existing_data():
    """Remove existing test data to make seeding idempotent."""
    print("Clearing existing code entity records...")
    for label in ["FUNCTION", "SERVICE", "TEST"]:
        db.records.delete_many({"labels": [label], "where": {}})
    print("  Cleared existing records.")


def create_records():
    """Create all code entities in RushDB."""
    all_records = {"utility": [], "business": [], "services": [], "tests": []}

    print("\nCreating utility functions...")
    for func in UTILITY_FUNCTIONS:
        record = db.records.create(
            label="FUNCTION",
            data={
                "name": func["name"],
                "signature": func["signature"],
                "file_path": func["file_path"],
                "description": func["description"],
                "type": "utility",
            },
        )
        all_records["utility"].append(record)
        print(f"  Created {func['name']}")

    print("\nCreating business logic functions...")
    for func in BUSINESS_LOGIC:
        record = db.records.create(
            label="FUNCTION",
            data={
                "name": func["name"],
                "signature": func["signature"],
                "file_path": func["file_path"],
                "description": func["description"],
                "type": "business_logic",
            },
        )
        all_records["business"].append(record)
        print(f"  Created {func['name']}")

    print("\nCreating API services...")
    for svc in API_ENDPOINTS:
        record = db.records.create(
            label="SERVICE",
            data={
                "name": svc["name"],
                "signature": svc["signature"],
                "file_path": svc["file_path"],
                "description": svc["description"],
            },
        )
        all_records["services"].append(record)
        print(f"  Created {svc['name']}")

    print("\nCreating test files...")
    for test in TESTS:
        record = db.records.create(
            label="TEST",
            data={
                "name": test["name"],
                "signature": test["signature"],
                "file_path": test["file_path"],
                "description": test["description"],
            },
        )
        all_records["tests"].append(record)
        print(f"  Created {test['name']}")

    return all_records


def create_relationships(records):
    """Create call dependencies and test coverage relationships."""
    print("\nCreating structural relationships...")

    # Find format_currency (utility function)
    format_currency = None
    for rec in records["utility"]:
        if rec["name"] == "format_currency":
            format_currency = rec
            break

    # Utility functions that format_currency doesn't call (by design)
    # These will be used to show naive approach limitations

    # Business logic -> Utility function dependencies
    # generate_receipt -> format_currency (direct caller)
    format_currency_rec = None
    generate_receipt_rec = None
    for rec in records["business"]:
        if rec["name"] == "format_currency":
            format_currency_rec = rec
        if rec["name"] == "generate_receipt":
            generate_receipt_rec = rec

    # create_receipt_calls format_currency to format line items
    if generate_receipt_rec and format_currency_rec:
        db.records.attach(
            source=generate_receipt_rec,
            target=format_currency_rec,
            options={"type": "CALLS"},
        )
        print("  generate_receipt -> format_currency (CALLS)")

    # send_invoice -> format_currency
    send_invoice_rec = None
    for rec in records["business"]:
        if rec["name"] == "send_invoice":
            send_invoice_rec = rec
    if send_invoice_rec and format_currency_rec:
        db.records.attach(
            source=send_invoice_rec,
            target=format_currency_rec,
            options={"type": "CALLS"},
        )
        print("  send_invoice -> format_currency (CALLS)")

    # calculate_shipping -> format_currency (for shipping quotes)
    calculate_shipping_rec = None
    for rec in records["business"]:
        if rec["name"] == "calculate_shipping":
            calculate_shipping_rec = rec
    if calculate_shipping_rec and format_currency_rec:
        db.records.attach(
            source=calculate_shipping_rec,
            target=format_currency_rec,
            options={"type": "CALLS"},
        )
        print("  calculate_shipping -> format_currency (CALLS)")

    # orders_endpoint -> format_currency (via business logic)
    orders_endpoint_rec = None
    for rec in records["services"]:
        if rec["name"] == "orders_endpoint":
            orders_endpoint_rec = rec
    if orders_endpoint_rec and generate_receipt_rec:
        db.records.attach(
            source=orders_endpoint_rec,
            target=generate_receipt_rec,
            options={"type": "CALLS"},
        )
        print("  orders_endpoint -> generate_receipt (CALLS)")

    # shipping_quote_endpoint -> calculate_shipping
    shipping_quote_rec = None
    for rec in records["services"]:
        if rec["name"] == "shipping_quote_endpoint":
            shipping_quote_rec = rec
    if shipping_quote_rec and calculate_shipping_rec:
        db.records.attach(
            source=shipping_quote_rec,
            target=calculate_shipping_rec,
            options={"type": "CALLS"},
        )
        print("  shipping_quote_endpoint -> calculate_shipping (CALLS)")

    # checkout_endpoint -> process_payment -> send_invoice
    checkout_rec = None
    process_payment_rec = None
    for rec in records["services"]:
        if rec["name"] == "checkout_endpoint":
            checkout_rec = rec
    for rec in records["business"]:
        if rec["name"] == "process_payment":
            process_payment_rec = rec
    if checkout_rec and process_payment_rec:
        db.records.attach(
            source=checkout_rec,
            target=process_payment_rec,
            options={"type": "CALLS"},
        )
        print("  checkout_endpoint -> process_payment (CALLS)")

    # invoices_endpoint -> send_invoice
    invoices_rec = None
    for rec in records["services"]:
        if rec["name"] == "invoices_endpoint":
            invoices_rec = rec
    if invoices_rec and send_invoice_rec:
        db.records.attach(
            source=invoices_rec,
            target=send_invoice_rec,
            options={"type": "CALLS"},
        )
        print("  invoices_endpoint -> send_invoice (CALLS)")

    # Test coverage relationships
    print("\nCreating test coverage relationships...")

    # test_format_currency -> format_currency
    test_format_currency_rec = None
    for rec in records["tests"]:
        if rec["name"] == "test_format_currency":
            test_format_currency_rec = rec
    if test_format_currency_rec and format_currency_rec:
        db.records.attach(
            source=test_format_currency_rec,
            target=format_currency_rec,
            options={"type": "TESTS"},
        )
        print("  test_format_currency -> format_currency (TESTS)")

    # test_calculate_order_total -> calculate_order_total
    test_calculate_rec = None
    calculate_order_total_rec = None
    for rec in records["tests"]:
        if rec["name"] == "test_calculate_order_total":
            test_calculate_rec = rec
    for rec in records["business"]:
        if rec["name"] == "calculate_order_total":
            calculate_order_total_rec = rec
    if test_calculate_rec and calculate_order_total_rec:
        db.records.attach(
            source=test_calculate_rec,
            target=calculate_order_total_rec,
            options={"type": "TESTS"},
        )
        print("  test_calculate_order_total -> calculate_order_total (TESTS)")

    # test_checkout_flow -> checkout_endpoint
    test_checkout_rec = None
    if test_checkout_rec and checkout_rec:
        db.records.attach(
            source=test_checkout_rec,
            target=checkout_rec,
            options={"type": "TESTS"},
        )
        print("  test_checkout_flow -> checkout_endpoint (TESTS)")

    # test_receipt_generation -> generate_receipt
    test_receipt_rec = None
    for rec in records["tests"]:
        if rec["name"] == "test_receipt_generation":
            test_receipt_rec = rec
    if test_receipt_rec and generate_receipt_rec:
        db.records.attach(
            source=test_receipt_rec,
            target=generate_receipt_rec,
            options={"type": "TESTS"},
        )
        print("  test_receipt_generation -> generate_receipt (TESTS)")


def setup_vector_index():
    """Create a vector index for semantic search on function descriptions."""
    print("\nSetting up vector index for semantic search...")

    # Check if index already exists
    existing = db.ai.indexes.find()
    if existing.data:
        for idx in existing.data:
            if idx["label"] == "FUNCTION" and idx["propertyName"] == "description":
                print("  Vector index already exists, skipping creation")
                return

    # Create index for function descriptions
    index = db.ai.indexes.create({
        "label": "FUNCTION",
        "propertyName": "description",
    })
    print(f"  Created vector index: {index.id}")


def main():
    print("=" * 60)
    print("RushDB Code Dependency Graph Seeder")
    print("=" * 60)

    # Check if data already exists (idempotent seeding)
    existing_functions = db.records.find({"labels": ["FUNCTION"], "limit": 1})
    if existing_functions.data:
        print("\n⚠️  Existing data detected. Skipping full seed.")
        print("   Run 'curl -X DELETE /api/clear' to reset, or run main.py directly.")
        print("\nTo reset and re-seed, run: python -c \"from seed import reset_data; reset_data()\"")
        return

    clear_existing_data()
    records = create_records()
    create_relationships(records)
    setup_vector_index()

    print("\n" + "=" * 60)
    print("Seeding complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
