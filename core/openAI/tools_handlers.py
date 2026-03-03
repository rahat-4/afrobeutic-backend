"""
Tool handler service.
Receives a tool_name + arguments dict and returns a JSON-serialisable result.
This is called inside the OpenAI run polling loop whenever the assistant
requests a tool call.
"""

import random
import json
import logging
from datetime import datetime, date, timedelta

from django.utils import timezone
from django.contrib.auth import get_user_model

from apps.support.models import AccountSupportTicket
from apps.salon.models import (
    Chair,
    Salon,
    Employee,
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


def get_available_employees(
    salon: Salon,
    booking_date: str,
    booking_time: str,
    service_ids: list[str] = None,
) -> dict:
    """
    Return a shuffled list of employees who are free at the given date/time.

    Availability rules:
      1. Employee must belong to this salon.
      2. If service_ids are provided, the employee must be assigned to ALL
         of those services — ensuring they can actually perform the booking.
      3. Employee must NOT already have an active booking (PLACED / INPROGRESS
         / RESCHEDULED) that starts at the exact same date + time.

    The result list is shuffled with random.shuffle() so that every call
    produces a different ordering. The caller always picks index [0], which
    means every available employee has an equal chance of being assigned —
    no single employee gets overloaded by always being "first".
    """
    try:
        b_date = datetime.strptime(booking_date, "%Y-%m-%d").date()
        b_time = datetime.strptime(booking_time, "%H:%M").time()
    except ValueError as e:
        return _err(f"Invalid date/time format: {e}")

    # Step 1 — employees already booked at this exact slot
    busy_employee_ids = Booking.objects.filter(
        salon=salon,
        booking_date=b_date,
        booking_time=b_time,
        status__in=[
            BookingStatus.PLACED,
            BookingStatus.INPROGRESS,
            BookingStatus.RESCHEDULED,
        ],
        employee__isnull=False,
    ).values_list("employee_id", flat=True)

    # Step 2 — salon employees not in the busy list
    employees_qs = Employee.objects.filter(salon=salon).exclude(
        id__in=busy_employee_ids
    )

    # Step 3 — if services are requested, keep only employees assigned to ALL of them
    # (chaining one filter per service_id guarantees AND semantics, not OR)
    if service_ids:
        for sid in service_ids:
            employees_qs = employees_qs.filter(employee_services__uid=sid)
        employees_qs = employees_qs.distinct()

    # Step 4 — materialise, then shuffle to distribute workload evenly
    available = list(
        employees_qs.select_related("designation").values(
            "id", "name", "designation__name"
        )
    )
    random.shuffle(available)

    return _ok({"available_employees": available})


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

    # ── Resolve services & compute total duration ─────────────────────────────
    services = []
    total_duration = timedelta(minutes=30)  # sensible default
    if service_ids:
        services = list(salon.salon_services.filter(uid__in=service_ids))
        if not services:
            return _err("No valid services found for the provided IDs.")
        total_duration = sum(
            (s.service_duration for s in services), start=timedelta(0)
        ) or timedelta(minutes=30)

    # ── Resolve products ──────────────────────────────────────────────────────
    products = []
    if product_ids:
        products = list(salon.salon_products.filter(uid__in=product_ids))
        if not products:
            return _err("No valid products found for the provided IDs.")

    # ── Check chair availability ──────────────────────────────────────────────
    chairs_result = get_available_chairs(salon, booking_date, booking_time)
    if not chairs_result["success"] or not chairs_result["available_chairs"]:
        return _err("No available chairs for the selected date and time.")
    assigned_chair = chairs_result["available_chairs"][0]

    # ── Auto-assign employee via shuffled pool ────────────────────────────────
    # get_available_employees returns a pre-shuffled list; picking index [0]
    # gives a uniformly random assignment across all qualified free employees.
    employees_result = get_available_employees(
        salon=salon,
        booking_date=booking_date,
        booking_time=booking_time,
        service_ids=service_ids if service_ids else None,
    )
    assigned_employee = None
    if employees_result["success"] and employees_result["available_employees"]:
        assigned_employee = Employee.objects.get(
            id=employees_result["available_employees"][0]["id"]
        )

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
        chair=assigned_chair,
        employee=assigned_employee,
    )

    # ── Upgrade lead → customer ───────────────────────────────────────────────
    if customer.type != CustomerType.CUSTOMER:
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
            "duration_minutes": int(total_duration.total_seconds() // 60),
            "assigned_employee": assigned_employee.name if assigned_employee else None,
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

    # ── Chair check for new slot ──────────────────────────────────────────────
    chairs_result = get_available_chairs(salon, new_booking_date, new_booking_time)
    if not chairs_result["success"] or not chairs_result["available_chairs"]:
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

    # ── Re-assign employee for the new slot (shuffle again) ───────────────────
    service_uids = [str(uid) for uid in booking.services.values_list("uid", flat=True)]
    employees_result = get_available_employees(
        salon=salon,
        booking_date=new_booking_date,
        booking_time=new_booking_time,
        service_ids=service_uids if service_uids else None,
    )
    new_employee = booking.employee  # keep existing as fallback
    if employees_result["success"] and employees_result["available_employees"]:
        new_employee = Employee.objects.get(
            id=employees_result["available_employees"][0]["id"]
        )

    booking.booking_date = b_date
    booking.booking_time = b_time
    booking.status = BookingStatus.RESCHEDULED
    booking.chair = chairs_result["available_chairs"][0]
    booking.employee = new_employee
    booking.save(
        update_fields=["booking_date", "booking_time", "status", "chair", "employee"]
    )

    return _ok(
        {
            "booking_id": booking.booking_id,
            "new_date": str(booking.booking_date),
            "new_time": str(booking.booking_time),
            "assigned_employee": new_employee.name if new_employee else None,
            "message": "Your booking has been successfully rescheduled.",
        }
    )


def get_customer_bookings(
    salon: Salon,
    customer: Customer,
    status_filter: str = "ALL",
) -> dict:
    qs = (
        Booking.objects.filter(salon=salon, customer=customer)
        .prefetch_related("services", "products")
        .select_related("employee", "chair")
    )

    if status_filter != "ALL":
        qs = qs.filter(status=status_filter)
    else:
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
                "employee": b.employee.name if b.employee else None,
                "chair": b.chair.name if b.chair else None,
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
    Save the customer's request to AccountSupportTicket (CRM).
    """

    try:
        ticket = AccountSupportTicket.objects.create(
            account=salon.account,
            salon=salon,
            customer=customer,
            type=request_type,
            summary=(
                f"{message}\n\nRelated Booking ID: {related_booking_id}"
                if related_booking_id
                else message
            ),
        )

        # 2️⃣ Send Email to Salon Owner
        owner_email = salon.account.owner.email

        # send_mail(
        #     subject=f"New Client Request - {request_type}",
        #     message=(
        #         f"Salon: {salon.name}\n"
        #         f"Customer: {customer.full_name}\n"
        #         f"Phone: {customer.phone}\n"
        #         f"Type: {request_type}\n\n"
        #         f"Message:\n{message}\n\n"
        #         f"Ticket ID: {ticket.uid}"
        #     ),
        #     from_email=settings.DEFAULT_FROM_EMAIL,
        #     recipient_list=[owner_email],
        #     fail_silently=True,  # Important: don't break chatbot if email fails
        # )

        return _ok(
            {
                "ticket_id": str(ticket.uid),
                "status": ticket.status,
                "message": (
                    "Your request has been sent to our team. "
                    "We will contact you shortly."
                ),
            }
        )

    except Exception as exc:
        logger.exception("Failed to create support ticket: %s", exc)
        return _err("We couldn't submit your request at the moment. Please try again.")


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
