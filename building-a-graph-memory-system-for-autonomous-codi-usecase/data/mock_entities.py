"""
Mock code entities for demonstrating the graph memory system.

This represents a simplified but realistic code graph with:
- Files and directories (code modules)
- Functions/methods defined in files
- Bugs with known root causes
- Investigation records showing what was already checked
"""

# A realistic codebase structure for a web application
DIRECTORIES = [
    {"path": "/auth", "description": "Authentication and authorization modules"},
    {"path": "/auth/middleware", "description": "Express middleware for auth"},
    {"path": "/auth/jwt", "description": "JWT token handling"},
    {"path": "/api", "description": "API route handlers"},
    {"path": "/api/users", "description": "User management endpoints"},
    {"path": "/api/orders", "description": "Order management endpoints"},
    {"path": "/services", "description": "Business logic services"},
    {"path": "/services/billing", "description": "Billing and payment services"},
    {"path": "/db", "description": "Database access layer"},
    {"path": "/utils", "description": "Utility functions"},
]

FILES = [
    # Auth files
    {"path": "/auth/middleware/authMiddleware.ts", "type": "typescript", "dir": "/auth/middleware"},
    {"path": "/auth/jwt/tokenValidator.ts", "type": "typescript", "dir": "/auth/jwt"},
    {"path": "/auth/jwt/jwtService.ts", "type": "typescript", "dir": "/auth/jwt"},
    {"path": "/auth/session/sessionManager.ts", "type": "typescript", "dir": "/auth"},
    # API files
    {"path": "/api/users/userController.ts", "type": "typescript", "dir": "/api/users"},
    {"path": "/api/users/userService.ts", "type": "typescript", "dir": "/api/users"},
    {"path": "/api/orders/orderController.ts", "type": "typescript", "dir": "/api/orders"},
    {"path": "/api/orders/orderService.ts", "type": "typescript", "dir": "/api/orders"},
    {"path": "/api/baseApi.ts", "type": "typescript", "dir": "/api"},
    # Service files
    {"path": "/services/billing/billingService.ts", "type": "typescript", "dir": "/services/billing"},
    {"path": "/services/billing/paymentProcessor.ts", "type": "typescript", "dir": "/services/billing"},
    # DB files
    {"path": "/db/queryBuilder.ts", "type": "typescript", "dir": "/db"},
    {"path": "/db/migrations/runMigrations.ts", "type": "typescript", "dir": "/db"},
    # Utils
    {"path": "/utils/logger.ts", "type": "typescript", "dir": "/utils"},
    {"path": "/utils/validator.ts", "type": "typescript", "dir": "/utils"},
]

# Functions with their defining files and dependencies
FUNCTIONS = [
    {
        "name": "validateToken",
        "file": "/auth/jwt/tokenValidator.ts",
        "summary": "Validates JWT token signature and expiration",
        "calls": ["verifySignature", "checkExpiration"],
    },
    {
        "name": "verifySignature",
        "file": "/auth/jwt/jwtService.ts",
        "summary": "Verifies the cryptographic signature of a JWT",
        "calls": ["decodeHeader"],
    },
    {
        "name": "checkExpiration",
        "file": "/auth/jwt/tokenValidator.ts",
        "summary": "Checks if token has expired based on exp claim",
        "calls": [],
    },
    {
        "name": "authenticateRequest",
        "file": "/auth/middleware/authMiddleware.ts",
        "summary": "Express middleware that authenticates incoming requests",
        "calls": ["validateToken", "getUserFromToken"],
    },
    {
        "name": "getUserFromToken",
        "file": "/auth/jwt/jwtService.ts",
        "summary": "Extracts user info from a validated JWT token",
        "calls": [],
    },
    {
        "name": "createSession",
        "file": "/auth/session/sessionManager.ts",
        "summary": "Creates a new user session after successful login",
        "calls": ["hashSessionId"],
    },
    {
        "name": "getUser",
        "file": "/api/users/userService.ts",
        "summary": "Retrieves user data from database by ID",
        "calls": ["executeQuery"],
    },
    {
        "name": "updateUser",
        "file": "/api/users/userService.ts",
        "summary": "Updates user data in the database",
        "calls": ["executeQuery", "validateUserData"],
    },
    {
        "name": "processOrder",
        "file": "/api/orders/orderService.ts",
        "summary": "Processes a new order, including payment and inventory",
        "calls": ["chargePayment", "reserveInventory"],
    },
    {
        "name": "chargePayment",
        "file": "/services/billing/paymentProcessor.ts",
        "summary": "Charges the customer's payment method",
        "calls": ["validateToken", "callPaymentGateway"],
    },
    {
        "name": "callPaymentGateway",
        "file": "/services/billing/billingService.ts",
        "summary": "Makes API call to external payment processor",
        "calls": [],
    },
    {
        "name": "executeQuery",
        "file": "/db/queryBuilder.ts",
        "summary": "Executes a SQL query against the database",
        "calls": [],
    },
]

# Bugs with their root causes and investigation trails
BUGS = [
    {
        "id": "BUG-1001",
        "title": "Authentication fails for expired tokens even when refresh token is valid",
        "severity": "high",
        "description": "Users with expired access tokens cannot refresh their session even when they have a valid refresh token. The system should automatically refresh but instead shows 'Authentication failed'.",
        "root_cause": {
            "file": "/auth/jwt/tokenValidator.ts",
            "function": "validateToken",
            "line": 47,
            "issue": "The validateToken function returns false for expired tokens without checking if a refresh token is available. It should return a special 'expired but refreshable' status instead of failing outright.",
        },
        "investigation_trail": [
            {"file": "/auth/middleware/authMiddleware.ts", "result": "ruled_out", "reason": "Middleware correctly passes tokens to validator - issue not here"},
            {"file": "/auth/jwt/jwtService.ts", "result": "ruled_out", "reason": "getUserFromToken works correctly when given valid token"},
            {"file": "/auth/session/sessionManager.ts", "result": "ruled_out", "reason": "Session creation works fine for new sessions"},
            {"file": "/api/baseApi.ts", "result": "ruled_out", "reason": "Base API handler doesn't interact with tokens directly"},
            {"file": "/auth/jwt/tokenValidator.ts", "result": "root_cause", "reason": "validateToken doesn't handle refresh flow"},
        ],
    },
    {
        "id": "BUG-1002",
        "title": "Order processing fails silently when payment gateway times out",
        "severity": "critical",
        "description": "When the external payment gateway doesn't respond within 30 seconds, the order is marked as 'processing' but never completes or rolls back. Money is charged but order remains in limbo.",
        "root_cause": {
            "file": "/services/billing/paymentProcessor.ts",
            "function": "chargePayment",
            "line": 89,
            "issue": "The chargePayment function catches gateway timeouts but doesn't implement a retry mechanism or transaction rollback. It returns a partial success status, leaving the order in an inconsistent state.",
        },
        "investigation_trail": [
            {"file": "/api/orders/orderService.ts", "result": "ruled_out", "reason": "processOrder correctly handles the return from chargePayment"},
            {"file": "/services/billing/billingService.ts", "result": "ruled_out", "reason": "callPaymentGateway correctly propagates timeout error"},
            {"file": "/services/billing/paymentProcessor.ts", "result": "root_cause", "reason": "Missing rollback/retry logic for timeout handling"},
        ],
    },
    {
        "id": "BUG-1003",
        "title": "User profile updates don't persist after page refresh",
        "severity": "medium",
        "description": "After updating their profile (name, email, etc.), users see the changes immediately but after refreshing the page, the old values return. The database shows the updated values.",
        "root_cause": {
            "file": "/api/users/userController.ts",
            "function": "getUser",
            "line": 23,
            "issue": "The getUser function reads from cache instead of database when the cache entry hasn't expired. After updateUser modifies the database, the stale cache entry (TTL: 1 hour) is still served.",
        },
        "investigation_trail": [
            {"file": "/api/users/userService.ts", "result": "ruled_out", "reason": "updateUser correctly writes to database"},
            {"file": "/db/queryBuilder.ts", "result": "ruled_out", "reason": "Query execution works correctly"},
            {"file": "/auth/session/sessionManager.ts", "result": "ruled_out", "reason": "Session management unrelated to user data"},
            {"file": "/api/users/userController.ts", "result": "root_cause", "reason": "Cache invalidation not triggered on updates"},
        ],
    },
]

# Historical investigation patterns (for demonstrating learning)
HISTORICAL_INVESTIGATIONS = [
    {
        "bug_id": "BUG-999",
        "title": "Similar to BUG-1001 - Token validation issue",
        "root_cause_file": "/auth/jwt/tokenValidator.ts",
        "time_to_fix": "2 hours",
        "files_investigated": 5,
    },
    {
        "bug_id": "BUG-888",
        "title": "Payment timeout in order flow",
        "root_cause_file": "/services/billing/paymentProcessor.ts",
        "time_to_fix": "4 hours",
        "files_investigated": 8,
    },
    {
        "bug_id": "BUG-777",
        "title": "Stale cache on user data",
        "root_cause_file": "/api/users/userController.ts",
        "time_to_fix": "1 hour",
        "files_investigated": 3,
    },
]
