"""
Tool handler service.
Receives a tool_name + arguments dict and returns a JSON-serialisable result.
This is called inside the OpenAI run polling loop whenever the assistant
requests a tool call.
"""

import json
import logging
from datetime import datetime, date

from django.utils import timezone
from django.contrib.auth import get_user_model

from apps.salon.models import (
    Chair,
    Salon,
    Service,
    Product,
    Booking,
    Customer,
    OpeningHours,
)
from apps.salon.choices import BookingStatus, ChairStatus, CustomerType
from apps.salon.utils import unique_booking_id_generator

# Import your CRM client request model — adjust path as needed
# from apps.crm.models import ClientRequest

logger = logging.getLogger(__name__)
User = get_user_model()


# ─────────────────────────────────────────────────────────────────────────────
# Helper
# ─────────────────────────────────────────────────────────────────────────────


def _err(msg: str) -> dict:
    return {"success": False, "error": msg}


def _ok(data: dict) -> dict:
    return {"success": True, **data}


# ─────────────────────────────────────────────────────────────────────────────
# Tool implementations
# ─────────────────────────────────────────────────────────────────────────────


def get_salon_info(salon: Salon) -> dict:
    hours = []
    for oh in salon.opening_hours.order_by("day"):
        hours.append(
            {
                "day": oh.day,
                "opening_time": str(oh.opening_time) if oh.opening_time else None,
                "closing_time": str(oh.closing_time) if oh.closing_time else None,
                "is_closed": oh.is_closed,
            }
        )

    return _ok(
        {
            "name": salon.name,
            "type": salon.salon_type,
            "category": salon.salon_category,
            "address": salon.formatted_address,
            "city": salon.city,
            "country": str(salon.country),
            "postal_code": salon.postal_code,
            "phone": str(salon.phone_number_one),
            "email": salon.email,
            "facebook": salon.facebook,
            "instagram": salon.instagram,
            "youtube": salon.youtube,
            "about": salon.about_salon,
            "opening_hours": hours,
        }
    )


def get_services_and_products(salon: Salon, gender_filter: str = None) -> dict:
    services_qs = salon.salon_services.select_related("category", "sub_category")
    if gender_filter:
        services_qs = services_qs.filter(gender_specific=gender_filter)

    services = []
    for s in services_qs:
        services.append(
            {
                "id": str(s.uid),
                "name": s.name,
                "category": s.category.name,
                "sub_category": s.sub_category.name if s.sub_category else None,
                "price": str(s.price),
                "final_price": str(s.final_price()),
                "discount_percentage": str(s.discount_percentage),
                "duration_minutes": int(s.service_duration.total_seconds() // 60),
                "description": s.description,
                "gender_specific": s.gender_specific,
                "available_time_slots": s.available_time_slots,
            }
        )

    products = []
    for p in salon.salon_products.select_related("category", "sub_category"):
        products.append(
            {
                "id": str(p.uid),
                "name": p.name,
                "category": p.category.name,
                "sub_category": p.sub_category.name if p.sub_category else None,
                "price": str(p.price),
                "description": p.description,
            }
        )

    return _ok({"services": services, "products": products})


def get_available_chairs(salon: Salon, booking_date: str, booking_time: str) -> dict:
    try:
        b_date = datetime.strptime(booking_date, "%Y-%m-%d").date()
        b_time = datetime.strptime(booking_time, "%H:%M").time()
    except ValueError as e:
        return _err(f"Invalid date/time format: {e}")

    # Get all chairs that are not occupied at the given date/time
    occupied_chairs = Booking.objects.filter(
        salon=salon,
        booking_date=b_date,
        booking_time=b_time,
        status__in=[
            BookingStatus.PLACED,
            BookingStatus.INPROGRESS,
            BookingStatus.RESCHEDULED,
        ],
    ).values_list("chair_id", flat=True)

    available_chairs = Chair.objects.filter(
        salon=salon, status=ChairStatus.AVAILABLE
    ).exclude(id__in=occupied_chairs)

    return _ok({"available_chairs": available_chairs})


def make_reservation(
    salon: Salon,
    customer: Customer,
    booking_date: str,
    booking_time: str,
    service_ids: list[str] = None,
    product_ids: list[str] = None,
    notes: str = "",
    payment_type: str = "CASH",
) -> dict:
    # Validate date/time
    try:
        b_date = datetime.strptime(booking_date, "%Y-%m-%d").date()
        b_time = datetime.strptime(booking_time, "%H:%M").time()
    except ValueError as e:
        return _err(f"Invalid date/time format: {e}")

    if b_date < date.today():
        return _err("Booking date cannot be in the past.")

    # Resolve services
    services = []
    total_duration = None
    if service_ids:
        services = list(salon.salon_services.filter(uid__in=service_ids))

        # Calculate total duration
        total_duration = sum(
            (s.service_duration for s in services),
            start=services[0].service_duration
            - services[0].service_duration,  # timedelta(0)
        )
        if not total_duration:
            from datetime import timedelta

            total_duration = timedelta(minutes=30)

    # Resolve products
    products = []
    if product_ids:
        products = list(salon.salon_products.filter(uid__in=product_ids))

    chairs = get_available_chairs(salon, booking_date, booking_time)
    if not chairs["success"] or not chairs["available_chairs"]:
        return _err("No available chairs for the selected date and time.")

    booking = Booking.objects.create(
        booking_date=b_date,
        booking_time=b_time,
        status=BookingStatus.PLACED,
        notes=notes,
        booking_duration=total_duration,
        payment_type=payment_type,
        account=salon.account,
        salon=salon,
        customer=customer,
        chair=chairs["available_chairs"][0] if chairs["available_chairs"] else None,
    )

    # Ensure customer is marked as CUSTOMER type (not just LEAD)
    customer.type = CustomerType.CUSTOMER
    customer.save(update_fields=["type"])

    if services:
        booking.services.set(services)
    if products:
        booking.products.set(products)

    return _ok(
        {
            "booking_id": booking.booking_id,
            "booking_uid": str(booking.uid),
            "booking_date": str(booking.booking_date),
            "booking_time": str(booking.booking_time),
            "status": booking.status,
            "services": [s.name for s in services],
            "products": [p.name for p in products],
            "payment_type": booking.payment_type,
            "duration_minutes": (
                int(total_duration.total_seconds() // 60) if total_duration else None
            ),
        }
    )


def cancel_reservation(
    salon: Salon,
    customer: Customer,
    booking_id: str,
    cancellation_reason: str,
) -> dict:
    try:
        booking = Booking.objects.get(
            booking_id=booking_id,
            salon=salon,
            customer=customer,
            status__in=[
                BookingStatus.PLACED,
                BookingStatus.INPROGRESS,
                BookingStatus.RESCHEDULED,
            ],
        )
    except Booking.DoesNotExist:
        return _err("Booking not found or it has already been completed/cancelled.")

    booking.status = BookingStatus.CANCELLED
    booking.cancellation_reason = cancellation_reason
    booking.save(update_fields=["status", "cancellation_reason"])

    return _ok(
        {
            "booking_id": booking.booking_id,
            "message": "Your booking has been successfully cancelled.",
        }
    )


def reschedule_reservation(
    salon: Salon,
    customer: Customer,
    booking_id: str,
    new_booking_date: str,
    new_booking_time: str,
) -> dict:
    try:
        b_date = datetime.strptime(new_booking_date, "%Y-%m-%d").date()
        b_time = datetime.strptime(new_booking_time, "%H:%M").time()
    except ValueError as e:
        return _err(f"Invalid date/time format: {e}")

    if b_date < date.today():
        return _err("New booking date cannot be in the past.")

    chairs = get_available_chairs(salon, new_booking_date, new_booking_time)
    if not chairs["success"] or not chairs["available_chairs"]:
        return _err("No available chairs for the new selected date and time.")

    try:
        booking = Booking.objects.get(
            booking_id=booking_id,
            salon=salon,
            customer=customer,
            status__in=[
                BookingStatus.PLACED,
                BookingStatus.INPROGRESS,
                BookingStatus.RESCHEDULED,
            ],
        )
    except Booking.DoesNotExist:
        return _err(
            "Booking not found or cannot be rescheduled (already completed/cancelled)."
        )

    booking.booking_date = b_date
    booking.booking_time = b_time
    booking.status = BookingStatus.PLACED  # reset to placed after reschedule
    booking.chair = (
        chairs["available_chairs"][0] if chairs["available_chairs"] else None,
    )
    booking.save(update_fields=["booking_date", "booking_time", "status"])

    return _ok(
        {
            "booking_id": booking.booking_id,
            "new_date": str(booking.booking_date),
            "new_time": str(booking.booking_time),
            "message": "Your booking has been successfully rescheduled.",
        }
    )


def get_customer_bookings(
    salon: Salon,
    customer: Customer,
    status_filter: str = "ALL",
) -> dict:
    qs = Booking.objects.filter(salon=salon, customer=customer).prefetch_related(
        "services", "products"
    )

    if status_filter != "ALL":
        qs = qs.filter(status=status_filter)
    else:
        # Default: show upcoming active bookings
        qs = qs.filter(
            status__in=[
                BookingStatus.PLACED,
                BookingStatus.INPROGRESS,
                BookingStatus.RESCHEDULED,
            ],
            booking_date__gte=date.today(),
        )

    bookings = []
    for b in qs.order_by("booking_date", "booking_time")[:10]:
        bookings.append(
            {
                "booking_id": b.booking_id,
                "date": str(b.booking_date),
                "time": str(b.booking_time),
                "status": b.status,
                "services": [s.name for s in b.services.all()],
                "products": [p.name for p in b.products.all()],
                "payment_type": b.payment_type,
            }
        )

    return _ok({"bookings": bookings, "total": len(bookings)})


def send_customer_request(
    salon: Salon,
    customer: Customer,
    request_type: str,
    message: str,
    related_booking_id: str = None,
) -> dict:
    """
    Save the customer's request/emergency to the CRM.
    Adjust the ClientRequest import/model to match your actual CRM app.
    """
    # ── Option A: if you have a CRM ClientRequest model ──────────────────────
    # from apps.crm.models import ClientRequest
    # ClientRequest.objects.create(
    #     salon=salon,
    #     account=salon.account,
    #     customer=customer,
    #     request_type=request_type,
    #     message=message,
    #     related_booking_id=related_booking_id,
    # )

    # ── Option B: fallback — log it and notify admin via WhatsApp/email ───────
    logger.info(
        "CLIENT REQUEST | salon=%s | customer=%s | type=%s | msg=%s | booking=%s",
        salon.name,
        customer.phone,
        request_type,
        message,
        related_booking_id,
    )

    # You could also trigger a Twilio message to the admin number here:
    # _notify_admin(salon, customer, request_type, message)

    return _ok(
        {
            "message": (
                "Your request has been sent to our team. "
                "We will get back to you as soon as possible."
            )
        }
    )


# ─────────────────────────────────────────────────────────────────────────────
# Dispatcher — called by the view after each tool_call
# ─────────────────────────────────────────────────────────────────────────────

TOOL_REGISTRY = {
    "get_salon_info": get_salon_info,
    "get_services_and_products": get_services_and_products,
    "make_reservation": make_reservation,
    "cancel_reservation": cancel_reservation,
    "reschedule_reservation": reschedule_reservation,
    "get_customer_bookings": get_customer_bookings,
    "send_customer_request": send_customer_request,
}


def dispatch_tool_call(
    tool_name: str,
    arguments: dict,
    salon: Salon,
    customer: Customer,
) -> str:
    """
    Route a tool call from the OpenAI assistant to the correct handler.
    Returns a JSON string to submit back as the tool result.
    """
    handler = TOOL_REGISTRY.get(tool_name)
    if not handler:
        result = _err(f"Unknown tool: {tool_name}")
        return json.dumps(result)

    try:
        # Inject salon & customer into every call (they are always needed)
        import inspect

        sig = inspect.signature(handler)
        kwargs = {k: v for k, v in arguments.items() if k in sig.parameters}
        if "salon" in sig.parameters:
            kwargs["salon"] = salon
        if "customer" in sig.parameters:
            kwargs["customer"] = customer

        result = handler(**kwargs)
    except Exception as exc:
        logger.exception("Tool %s raised an exception: %s", tool_name, exc)
        result = _err(f"An internal error occurred while processing your request.")

    return json.dumps(result, default=str)
