import os
import asyncio
import gc
import warnings
import threading

from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv

import vertexai
from google import adk
from google.genai import types as genai_types
from google.adk.agents.callback_context import CallbackContext
from google.adk.sessions import VertexAiSessionService
from toolbox_core import ToolboxSyncClient


load_dotenv()
warnings.filterwarnings("ignore")

app = Flask(__name__)

GOOGLE_CLOUD_PROJECT = os.environ["GOOGLE_CLOUD_PROJECT"]
GOOGLE_CLOUD_LOCATION = os.environ["GOOGLE_CLOUD_LOCATION"]
GOOGLE_GENAI_USE_VERTEXAI = os.environ["GOOGLE_GENAI_USE_VERTEXAI"]
TOOLBOX_SERVER = os.environ["TOOLBOX_SERVER"]
TOOLBOX_TOOLSET = os.environ["TOOLBOX_TOOLSET"]

PROJECT_ID = GOOGLE_CLOUD_PROJECT
APP_NAME = os.environ["REASONING_ENGINE_APP_NAME"]
USER_ID = "default_user"
AGENT_ENGINE_ID = os.environ["AGENT_ENGINE_ID"]

client = vertexai.Client(
    project=GOOGLE_CLOUD_PROJECT,
    location=GOOGLE_CLOUD_LOCATION
)

# --- ADK TOOLBOX CONFIGURATION ---
toolbox = ToolboxSyncClient(TOOLBOX_SERVER)
tools = toolbox.load_toolset(TOOLBOX_TOOLSET)

# --- ADK CALLBACKS (Narrative Engine) ---
execution_logs = []


async def trace_callback(context: CallbackContext):
    agent_name = context.agent.name
    event = {
        "agent": agent_name,
        "action": "Processing request steps...",
        "type": "orchestration_event"
    }
    execution_logs.append(event)
    return None


# --- AGENT DEFINITIONS ---
inventory_agent = adk.Agent(
    name="InventorySpecialist",
    model="gemini-2.5-flash",
    description="Specialist in product stock and warehouse data.",
    instruction="""
    Analyze inventory levels.
    1. Use 'search_products_by_context' or 'check_inventory_levels'.
    2. ALWAYS format results as a clean Markdown table.
    3. If there are many results, display only the TOP 10 most relevant ones.
    4. At the end, state: 'There are additional records available. Would you like to see more?'
    """,
    tools=tools
)

logistics_agent = adk.Agent(
    name="LogisticsManager",
    model="gemini-2.5-flash",
    description="Expert in global shipping routes and logistics tracking.",
    instruction="""
    Check shipment statuses.
    1. Use 'track_shipment_status' or 'analyze_supply_chain_risk'.
    2. ALWAYS format results as a clean Markdown table.
    3. Limit initial output to the top 10 shipments.
    4. Ask if the user needs the full manifest if more results exist.
    """,
    tools=tools
)

orchestrator = adk.Agent(
    name="GlobalOrchestrator",
    model="gemini-2.5-flash",
    description="Global Supply Chain Orchestrator root agent.",
    instruction="""
    You are the Global Supply Chain Brain. You are responsible for products, inventory and logistics.
    You also have access to the memory tool, remember to include all the information that the tool can provide you with about the user before you respond.
    1. Understand intent and delegate to specialists. As the Global Orchestrator, you have access to the full conversation history with the user.
    When you transfer a query to a specialist agent, sub agent or tool, share the important facts and information from your memory to them so they can operate with the full context.
    2. Ensure the final response is professional and uses Markdown tables for data.
    3. If a specialist provides a long list, ensure only the top 10 items are shown initially.
    4. Conclude with a brief, high-level executive summary of what the data implies.
    """,
    tools=[adk.tools.preload_memory_tool.PreloadMemoryTool()],
    sub_agents=[inventory_agent, logistics_agent],
)

session_service = VertexAiSessionService(
    project=PROJECT_ID,
    location=GOOGLE_CLOUD_LOCATION,
)

# Agent Engine was already created and updated earlier.
# Do not call create() or update() on every Cloud Run startup.
print("Using existing Agent Engine:")
print(APP_NAME)

try:
    memory_bank_service = adk.memory.VertexAiMemoryBankService(
        agent_engine_id=AGENT_ENGINE_ID,
        project=PROJECT_ID,
        location=GOOGLE_CLOUD_LOCATION,
    )
    print("Memory Bank Service initialized successfully.")
except Exception as e:
    print(f"Error initializing Memory Bank Service: {e}")
    memory_bank_service = None

runner = adk.Runner(
    agent=orchestrator,
    app_name=APP_NAME,
    session_service=session_service,
    memory_service=memory_bank_service,
)

session = None
session_lock = threading.Lock()


async def initialize_session():
    global session
    try:
        session = await session_service.create_session(
            app_name=APP_NAME,
            user_id=USER_ID
        )
        print(f"Session {session.id} created successfully.")
    except Exception as e:
        print(f"Error creating session: {e}")
        session = None


asyncio.run(initialize_session())

if hasattr(runner, "register_callback"):
    runner.register_callback(trace_callback)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/chat", methods=["POST"])
def chat():
    global session

    user_input = request.json.get("message")
    user_id = request.json.get("user_id", USER_ID)

    if session is None:
        return jsonify({
            "reply": "The system is initializing. Please wait and try again in a moment.",
            "narrative": []
        })

    session_id = session.id
    print(f"Session ID: {session_id}")

    content = genai_types.Content(
        role="user",
        parts=[genai_types.Part(text=user_input)]
    )

    print("****RESPONSE******")
    try:
        results = client.agent_engines.memories.retrieve(
            name=APP_NAME,
            scope={"app_name": APP_NAME, "user_id": USER_ID}
        )
        print(list(results))
    except Exception as e:
        print(f"Error retrieving memories: {e}")

    execution_logs.clear()
    execution_logs.append({
        "agent": "System",
        "action": "Establishing session context...",
        "type": "orchestration_event"
    })

    async def run_and_collect():
        final_text = ""
        try:
            async for event in runner.run_async(
                new_message=content,
                user_id=user_id,
                session_id=session_id
            ):
                if hasattr(event, "author") and event.author:
                    if not any(log["agent"] == event.author for log in execution_logs):
                        execution_logs.append({
                            "agent": event.author,
                            "action": "Analyzing data requirements...",
                            "type": "orchestration_event"
                        })

                if hasattr(event, "text") and event.text:
                    final_text = event.text
                elif hasattr(event, "content") and hasattr(event.content, "parts"):
                    for part in event.content.parts:
                        if hasattr(part, "text") and part.text:
                            final_text = part.text
        except Exception as e:
            print(f"Error during runner.run_async: {e}")
            raise
        finally:
            gc.collect()

        return final_text

    try:
        reply = asyncio.run(run_and_collect())

        session = asyncio.run(
            session_service.get_session(
                app_name=APP_NAME,
                user_id=USER_ID,
                session_id=session.id
            )
        )

        if memory_bank_service and session:
            try:
                asyncio.run(memory_bank_service.add_session_to_memory(session))
                print("Successfully added session to memory.")
                print(session.id)
            except Exception as e:
                print(f"Error adding session to memory: {e}")

        if not reply:
            reply = "The orchestrator completed the workflow but did not return a final summary."
    except Exception as e:
        reply = f"System Error: {str(e)}"

    return jsonify({
        "reply": reply,
        "narrative": list(execution_logs)
    })


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(
        debug=False,
        host="0.0.0.0",
        port=port,
        use_reloader=False,
    )