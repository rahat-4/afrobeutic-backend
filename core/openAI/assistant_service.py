import logging
import time
import pytz
from datetime import datetime
from timezonefinder import TimezoneFinder

from openai import OpenAI

from apps.salon.models import Salon, Customer
from openAI.assistant_instructions import SALON_ASSISTANT_INSTRUCTIONS
from openAI.assistant_tools import SALON_ASSISTANT_TOOLS
from openAI.tools_handlers import dispatch_tool_call

logger = logging.getLogger(__name__)

client = OpenAI()  # reads OPENAI_API_KEY from environment


def get_runtime_context(salon: Salon) -> str:
    """
    Returns a formatted runtime context string for the salon,
    including current date, time, and timezone based on its location.
    This can be sent as a system message or additional_instructions
    to the OpenAI assistant.
    """

    # Default timezone in case location fails
    default_timezone = "Asia/Dubai"

    try:
        # Get latitude and longitude from salon location PointField
        lat = salon.location.y
        lng = salon.location.x

        tf = TimezoneFinder()
        timezone_str = tf.timezone_at(lat=lat, lng=lng)

        if timezone_str is None:
            timezone_str = default_timezone

    except Exception:
        timezone_str = default_timezone

    # Current date and time in the salon's timezone
    tz = pytz.timezone(timezone_str)
    now = datetime.now(tz)
    current_date = now.strftime("%Y-%m-%d")
    current_time = now.strftime("%H:%M")

    # Build runtime context string
    runtime_context = f"""
        ## Runtime Context (Auto-Generated)
        Current Date: {current_date}
        Current Time: {current_time}
        Timezone: {timezone_str}
        Salon Location: {salon.city}, {salon.country.name}

        Rules:
        - Interpret "today", "tomorrow", etc using Current Date.
        - Never assume static or outdated dates.
        - All bookings must use this timezone.
        """

    return runtime_context


# ─────────────────────────────────────────────────────────────────────────────
# Assistant bootstrap (run once, e.g. from a management command)
# ─────────────────────────────────────────────────────────────────────────────


def get_or_create_assistant(salon: Salon) -> str:
    """
    Return the OpenAI assistant_id stored in WhatsappChatbotConfig.
    If not yet created, create it and persist the ID.
    """
    print("==========================>", get_runtime_context(salon))
    config = salon.salon_chatbot_config
    assistant_id = config.assistant_id.get("id") if config.assistant_id else None

    instructions = SALON_ASSISTANT_INSTRUCTIONS.replace("{salon_name}", salon.name)

    if assistant_id:
        # Keep tools/instructions in sync whenever the app restarts
        client.beta.assistants.update(
            assistant_id=assistant_id,
            instructions=f"{instructions}\n\n{get_runtime_context(salon)}",
            tools=SALON_ASSISTANT_TOOLS,
        )
        return assistant_id

    assistant = client.beta.assistants.create(
        name=f"{salon.name} WhatsApp Bot",
        instructions=f"{instructions}\n\n{get_runtime_context(salon)}",
        tools=SALON_ASSISTANT_TOOLS,
        model="gpt-4o",
    )
    config.assistant_id = {"id": assistant.id}
    config.save(update_fields=["assistant_id"])
    return assistant.id


# ─────────────────────────────────────────────────────────────────────────────
# Thread helpers
# ─────────────────────────────────────────────────────────────────────────────


def get_or_create_thread(customer: Customer, salon: Salon) -> str:
    """
    One OpenAI thread per (customer, salon) pair.
    We store the thread_id in the DB using a lightweight JSON field on Customer,
    or look it up from the message log if you prefer no schema change.
    """

    thread_id = customer.thread_id
    if thread_id:
        return thread_id

    # If no thread_id exists, create a new one
    thread = client.beta.threads.create()
    customer.thread_id = thread.id
    customer.save(update_fields=["thread_id"])

    return customer.thread_id


# ─────────────────────────────────────────────────────────────────────────────
# Core: send a message and get the assistant's reply
# ─────────────────────────────────────────────────────────────────────────────

MAX_POLL_SECONDS = 60
POLL_INTERVAL = 1  # seconds between status checks


def run_assistant(
    salon: Salon,
    customer: Customer,
    user_message: str,
) -> str:
    """
    1. Ensure an assistant exists for this salon.
    2. Get/create a conversation thread for this customer.
    3. Add the user's message to the thread.
    4. Create a run and poll until completion, handling tool calls.
    5. Return the final assistant text reply.
    """

    assistant_id = get_or_create_assistant(salon)
    thread_id = get_or_create_thread(customer, salon)

    # Add incoming user message
    client.beta.threads.messages.create(
        thread_id=thread_id,
        role="user",
        content=user_message,
    )

    # Create the run
    run = client.beta.threads.runs.create(
        thread_id=thread_id,
        assistant_id=assistant_id,
    )

    # Poll loop
    elapsed = 0
    while elapsed < MAX_POLL_SECONDS:
        run = client.beta.threads.runs.retrieve(
            thread_id=thread_id,
            run_id=run.id,
        )

        if run.status == "completed":
            break

        if run.status == "requires_action":
            run = _handle_tool_calls(run, thread_id, salon, customer)
            continue

        if run.status in ("failed", "cancelled", "expired"):
            logger.error(
                "Run %s ended with status %s: %s",
                run.id,
                run.status,
                getattr(run, "last_error", ""),
            )
            return "I'm sorry, something went wrong. Please try again in a moment."

        time.sleep(POLL_INTERVAL)
        elapsed += POLL_INTERVAL

    if run.status != "completed":
        return "I'm sorry, I took too long to respond. Please try again."

    # Extract last assistant message
    messages = client.beta.threads.messages.list(
        thread_id=thread_id,
        order="desc",
        limit=1,
    )
    for msg in messages.data:
        if msg.role == "assistant":
            # Concatenate all text content blocks
            return "\n".join(
                block.text.value for block in msg.content if block.type == "text"
            )

    return "I'm sorry, I couldn't generate a response."


def _handle_tool_calls(run, thread_id: str, salon: Salon, customer: Customer):
    """
    Submit all tool outputs for a requires_action run.
    """
    tool_outputs = []

    for tool_call in run.required_action.submit_tool_outputs.tool_calls:
        import json

        tool_name = tool_call.function.name
        try:
            arguments = json.loads(tool_call.function.arguments)
        except (json.JSONDecodeError, TypeError):
            arguments = {}

        logger.info("Tool call: %s | args: %s", tool_name, arguments)

        output = dispatch_tool_call(
            tool_name=tool_name,
            arguments=arguments,
            salon=salon,
            customer=customer,
        )
        tool_outputs.append(
            {
                "tool_call_id": tool_call.id,
                "output": output,
            }
        )

    # Submit all tool outputs in one call
    run = client.beta.threads.runs.submit_tool_outputs(
        thread_id=thread_id,
        run_id=run.id,
        tool_outputs=tool_outputs,
    )
    return run
