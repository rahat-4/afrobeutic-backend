"""
OpenAI Assistant Tool Definitions for Salon WhatsApp Chatbot.
"""

SALON_ASSISTANT_TOOLS = [
    # ─────────────────────────────────────────────
    # 1. Get basic salon information
    # ─────────────────────────────────────────────
    {
        "type": "function",
        "function": {
            "name": "get_salon_info",
            "description": (
                "Retrieve basic information about the salon including name, address, "
                "contact details, opening hours, services offered, and social links. "
                "Call this when the user asks about the salon, its location, timings, "
                "or what services/products are available."
            ),
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
    },
    # ─────────────────────────────────────────────
    # 2. List services (step before booking)
    # ─────────────────────────────────────────────
    {
        "type": "function",
        "function": {
            "name": "get_services_and_products",
            "description": (
                "Fetch all available services and products for this salon with their "
                "prices, durations, and descriptions. Always call this BEFORE making "
                "a reservation so the customer can choose what they want."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "gender_filter": {
                        "type": "string",
                        "enum": ["MALE_SALON", "FEMALE_SALON", "UNISEX_SALON"],
                        "description": "Optional filter by gender-specific services.",
                    }
                },
                "required": [],
            },
        },
    },
    # ─────────────────────────────────────────────
    # 3. Make a reservation
    # ─────────────────────────────────────────────
    {
        "type": "function",
        "function": {
            "name": "make_reservation",
            "description": (
                "Create a new booking for the customer. You MUST call "
                "get_services_and_products first and confirm the chosen services/products (if any) and the date/time"
                "with the customer before calling this function."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "booking_date": {
                        "type": "string",
                        "description": "Date for the booking in YYYY-MM-DD format.",
                    },
                    "booking_time": {
                        "type": "string",
                        "description": "Time for the booking in HH:MM (24-hour) format.",
                    },
                    "service_ids": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of service UIDs chosen by the customer (optional).",
                    },
                    "product_ids": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of product UIDs chosen by the customer (optional).",
                    },
                    "notes": {
                        "type": "string",
                        "description": "Any special notes or requests from the customer.",
                    },
                    "payment_type": {
                        "type": "string",
                        "enum": ["CASH", "CARD", "ONLINE"],
                        "description": "Preferred payment method.",
                    },
                },
                "required": ["booking_date", "booking_time"],
            },
        },
    },
    # ─────────────────────────────────────────────
    # 4. Cancel a reservation
    # ─────────────────────────────────────────────
    {
        "type": "function",
        "function": {
            "name": "cancel_reservation",
            "description": (
                "Cancel an existing booking for the customer. Ask for the booking ID "
                "or look it up via get_customer_bookings first if the customer doesn't know it."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "booking_id": {
                        "type": "string",
                        "description": "The 8-character booking ID to cancel.",
                    },
                    "cancellation_reason": {
                        "type": "string",
                        "description": "Reason provided by the customer for cancellation.",
                    },
                },
                "required": ["booking_id", "cancellation_reason"],
            },
        },
    },
    # ─────────────────────────────────────────────
    # 5. Reschedule a reservation
    # ─────────────────────────────────────────────
    {
        "type": "function",
        "function": {
            "name": "reschedule_reservation",
            "description": (
                "Reschedule an existing booking to a new date and/or time. "
                "Use get_customer_bookings first if needed to find the booking ID."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "booking_id": {
                        "type": "string",
                        "description": "The 8-character booking ID to reschedule.",
                    },
                    "new_booking_date": {
                        "type": "string",
                        "description": "New date in YYYY-MM-DD format.",
                    },
                    "new_booking_time": {
                        "type": "string",
                        "description": "New time in HH:MM (24-hour) format.",
                    },
                },
                "required": ["booking_id", "new_booking_date", "new_booking_time"],
            },
        },
    },
    # ─────────────────────────────────────────────
    # 6. Get customer's bookings
    # ─────────────────────────────────────────────
    {
        "type": "function",
        "function": {
            "name": "get_customer_bookings",
            "description": (
                "Retrieve the customer's upcoming or recent bookings. "
                "Useful before cancelling or rescheduling so the customer can pick the right booking."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "status_filter": {
                        "type": "string",
                        "enum": [
                            "PLACED",
                            "CONFIRMED",
                            "COMPLETED",
                            "CANCELLED",
                            "ALL",
                        ],
                        "description": "Filter bookings by status. Defaults to upcoming (PLACED/CONFIRMED).",
                    }
                },
                "required": [],
            },
        },
    },
    # ─────────────────────────────────────────────
    # 7. Send emergency/request to admin (CRM)
    # ─────────────────────────────────────────────
    {
        "type": "function",
        "function": {
            "name": "send_customer_request",
            "description": (
                "Send an emergency message or special request from the customer to the salon admin. "
                "This appears in the CRM's Client Request section. Use this when the customer "
                "reports an issue, has an urgent need, requests a callback, or asks for something "
                "that cannot be handled automatically."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "request_type": {
                        "type": "string",
                        "enum": [
                            "EMERGENCY",
                            "CALLBACK_REQUEST",
                            "COMPLAINT",
                            "GENERAL_INQUIRY",
                            "SPECIAL_REQUEST",
                        ],
                        "description": "Category of the request.",
                    },
                    "message": {
                        "type": "string",
                        "description": "The full message/request from the customer to pass to the admin.",
                    },
                    "related_booking_id": {
                        "type": "string",
                        "description": "Booking ID if this request is related to a specific booking (optional).",
                    },
                },
                "required": ["request_type", "message"],
            },
        },
    },
]
