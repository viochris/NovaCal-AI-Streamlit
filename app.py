import datetime
import streamlit as st

# --- LangChain & Generative AI Libraries ---
from langchain_google_community import CalendarToolkit
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.callbacks.streamlit import StreamlitCallbackHandler
from langchain_classic.agents import AgentExecutor, create_tool_calling_agent
from langchain_classic.memory import ConversationBufferMemory
from langchain_classic import hub
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.tools import tool

# --- Third-Party UI Components ---
from streamlit_calendar import calendar

# --- Custom Application Modules ---
from function import (
    init_state, 
    change_on_api_key, 
    reset_state, 
    reset_chat_display, 
    get_schedules, 
    get_id_of_schedules, 
    get_all_schedules
)

# ==========================================
# APPLICATION CONFIGURATION & INITIALIZATION
# ==========================================

# Defines browser tab properties, layout dimensions, and initial sidebar state.
# Must remain the first Streamlit command executed in the script.
st.set_page_config(
    page_title="NovaCal AI",
    page_icon="📅",
    layout="centered",
    initial_sidebar_state="expanded"
)

# Bootstraps essential session variables (message history, LLM instances, toolkits).
# Prevents KeyError exceptions during Streamlit's reactive re-runs.
init_state()


# ==========================================
# MAIN USER INTERFACE
# ==========================================
st.title("📅 NovaCal AI")

# Renders the introductory UI text detailing the application's capabilities.
# Utilizes inline CSS for precise alignment and styling of the subtitle container.
st.markdown(
    """
    <div style="text-align: center; color: #666; font-size: 1.1rem; margin-bottom: 30px;">
        <b>Automate your schedule. Experience intelligent time management.</b>
    </div>
    
    Welcome to **NovaCal AI**. Powered by an advanced **Tool-Calling Agent Architecture**, this assistant moves beyond basic chatbot capabilities. 
    It provides full **transparency** by showcasing its reasoning process—analyzing your intent, strategically selecting Google Calendar tools, and executing scheduling actions (Create, Read, Update, Delete) step-by-step for seamless calendar management.
    
    ---
    """, 
    unsafe_allow_html=True
)

with st.sidebar:
    # ==========================================
    # SIDEBAR CONFIGURATION & DASHBOARD
    # ==========================================
    # Renders the primary configuration header for the sidebar dashboard.
    st.header("⚙️ Configuration & Overview")
    st.divider()

    # ==========================================
    # NAVIGATION MENU
    # ==========================================
    # Dictionary mapping internal state names to UI-friendly labels with emojis.
    mode_icons = {
        "Chat AI": "💬 AI Assistant",
        "Calendar": "📆 Visual Calendar"
    }

    # Defines the application's primary navigation mode using a dropdown menu.
    # Uses 'format_func' to render the aesthetic label while returning the clean key to the variable.
    options = st.selectbox(
        "🗂️ Navigation Mode",
        options=list(mode_icons.keys()),
        format_func=lambda option: mode_icons.get(option),
        index=0,
        help="Select the module you want to access to manage your schedule."
    )

    # Captures the Google Gemini API Key securely.
    st.text_input(
        "🔑 Google API Key",
        type="password",
        key="google_api_key",
        on_change=change_on_api_key,
        help="Provide your Google Gemini API Key to authenticate and power the NovaCal AI agent."
    )

    st.divider()

    # ==========================================
    # DAILY SCHEDULE WIDGET
    # ==========================================
    # Renders a clear visual hierarchy for the agenda section.
    st.subheader("📋 Today's Agenda") # <-- KITA TAMBAHIN HEADER KHUSUS JADWAL!
    
    # Automatically fetches and renders today's agenda upon sidebar load.
    today_date = datetime.date.today().strftime("%Y-%m-%d")
    
    try: 
        today_schedules = get_all_schedules.invoke({
            "start_date": today_date,
            "end_date": today_date
        })
        st.info(today_schedules)
    except Exception as e:
        # Added warning icon to the error state for better UX.
        st.error(f"⚠️ Failed to load today's schedule: {e}") # <-- ERRORNYA JUGA KITA KASIH ICON

    st.divider()

    # ==========================================
    # SESSION MANAGEMENT CONTROLS
    # ==========================================
    # Instantiates the UI clearing mechanism.
    st.button(
        "🧹 Clear Screen Only",
        on_click=reset_chat_display,
        use_container_width=True,
        help="Clears the chat interface to declutter the screen, while preserving the AI's conversation memory."
    )

    # Triggers a comprehensive application state reset.
    st.button(
        "🔄 Full System Reset",
        on_click=reset_state,
        type="primary",
        use_container_width=True,
        help="Executes a complete system wipe: clears chat history, AI memory, and tool connections."
    )

    st.markdown("---")
    
    # ==========================================
    # DEVELOPER ATTRIBUTION FOOTER
    # ==========================================
    # Renders the author attribution and contact links via raw HTML styling.
    st.markdown(
        """
        <div style="text-align: center; font-size: 0.85rem; color: #888;">
            © 2026 <b>Silvio Christian, Joe</b><br>
            Powered by <b>Google Gemini</b> 🚀<br><br>
            <a href="https://www.linkedin.com/in/silvio-christian-joe/" target="_blank" style="text-decoration: none; margin-right: 10px;">🔗 LinkedIn</a>
            <a href="mailto:viochristian12@gmail.com" style="text-decoration: none;">📧 Email</a>
        </div>
        """, 
        unsafe_allow_html=True
    )

# ==========================================
# AI ENGINE & MEMORY INITIALIZATION
# ==========================================

# 1. Verify if the user has securely provided a Google Gemini API Key
if st.session_state.google_api_key:
    
    # 2. Implement a Singleton-like pattern: Initialize the LLM only if it doesn't already exist.
    # This prevents redundant re-instantiation during Streamlit's reactive UI re-runs, optimizing performance.
    if st.session_state.llm is None:
        st.session_state.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash", 
            google_api_key=st.session_state.google_api_key,
            # A low temperature (0.3) ensures the model's outputs are deterministic and precise.
            # This strictness is CRITICAL for reliable JSON generation during Google Calendar tool execution.
            temperature=0.3 
        )
        # Provide subtle visual feedback that the backend AI is primed and ready
        st.toast("AI Engine initialized successfully!", icon="🧠")
        
else:
    # Display a clear warning to halt interaction until authentication is provided
    st.warning("Please enter your Google API Key in the sidebar to proceed.", icon="⚠️")

# 3. Initialize the Agent's Conversational Memory
# Proceed strictly if the LLM has been successfully authenticated and instantiated
if st.session_state.llm is not None:
    
    # Check if the memory buffer is uninitialized (None). 
    # By skipping creation if it already exists, we preserve the user's ongoing chat history and contextual flow.
    if st.session_state.agent_memory is None:
        st.session_state.agent_memory = ConversationBufferMemory(
            memory_key="chat_history", 
            return_messages=True
        )

# ==========================================
# AGENT INITIALIZATION & PROMPT ENGINEERING
# ==========================================
# Only initialize the Agent Executor if it doesn't exist, AND the core dependencies (LLM, Memory) are ready.
if "agent_executor" not in st.session_state \
    and st.session_state.llm is not None \
    and st.session_state.agent_memory is not None:

    try:
        # 1. Initialize the Google Calendar Toolkit
        toolkit = CalendarToolkit()
        calendar_tools = toolkit.get_tools()

        # Filter out native LangChain search tools (they are buggy/broken for our use case)
        used_tools = [t for t in calendar_tools if "search" not in t.name.lower() and "get" not in t.name.lower()]
        
        # Inject our custom, highly-optimized tools
        tools = used_tools + [get_id_of_schedules, get_all_schedules]

        st.toast("✅ Successfully connected to Google Calendar API!", icon="🗓️")
        
    except Exception as e:
        # Halt execution if the toolkit fails to authenticate
        st.error(f"❌ Calendar Connection Failed: {e}")
        st.stop()
    
    try:
        # 2. Capture the Exact Current System Time for Contextual Accuracy
        current_datetime = datetime.datetime.now().strftime("%A, %d %B %Y %H:%M:%S")

        # 3. Construct the Custom Hybrid Tool-Calling Prompt
        # This serves as the core "Brain" of the agent, defining strict Standard Operating Procedures (SOP) for Calendar management.
        prompt = ChatPromptTemplate.from_messages([
            ("system", f"""You are an elite, highly capable Personal Assistant managing the user's Google Calendar.
            CURRENT SYSTEM TIME: {current_datetime}
            
            CRITICAL RULES:
            1. CALENDAR ID: Whenever a tool requires 'calendar_id', ALWAYS use exactly the string 'primary'.
            2. TIME CONTEXT: Base all date and time calculations strictly on the CURRENT SYSTEM TIME.
            3. LANGUAGE: Always respond naturally in the EXACT SAME language the user typed.
            4. CONVERSATIONAL MEMORY: You have access to the user's previous messages in 'chat_history'. ALWAYS check this history first to find missing details (like event title, date, or time). DO NOT ask the user for information they have already provided in previous messages.
            5. PARAMETER SAFETY:
                - If required parameters are STILL missing after checking chat_history, ask the user for clarification before calling any tool.
                - Never invent dates or times.
                - Do not assume default values unless explicitly provided by the user.
            6. BANNED TOOLS: NEVER use 'CalendarSearchEvents', 'search_events', or 'get_events'. They are broken.
            
            STANDARD OPERATING PROCEDURES (SOP) FOR CALENDAR ACTIONS:
            
            A. CREATING AN EVENT:
            - Use the 'CalendarCreateEvent' tool directly with the details provided.
            
            B. DELETING AN EVENT:
            - Step 1: You MUST FIRST use the 'get_id_of_schedules' tool (search by keyword) or 'get_all_schedules' tool (search by date. ALWAYS provide BOTH 'start_date' and 'end_date' in YYYY-MM-DD) to find the event.
            - Step 2: Extract the 'EVENT_ID' from the tool's response.
            - Step 3: Use the 'CalendarDeleteEvent' tool using that 'EVENT_ID'.
            
            C. EDITING/UPDATING AN EVENT:
            - Step 1: Use 'get_id_of_schedules' or 'get_all_schedules' (ALWAYS provide BOTH 'start_date' and 'end_date' in YYYY-MM-DD) to get the 'EVENT_ID' and the FULL original details.
            - Step 2 (The Priority): Try to use 'CalendarUpdateEvent' using the 'EVENT_ID'. You MUST pass the updated fields AND keep the unchanged fields from Step 1.
            - Step 3 (The Fallback): IF Step 2 fails (due to error or missing data), use the "Swap Method": 
                a. Create a NEW event with 'CalendarCreateEvent'.
                b. Delete the OLD event with 'CalendarDeleteEvent' using the 'EVENT_ID'.
            
            D. READING/DISPLAYING SCHEDULES (e.g., "What is my schedule today?"):
            - Use the 'get_all_schedules' tool.
            - You MUST provide BOTH 'start_date' and 'end_date' in YYYY-MM-DD format (e.g., '{current_datetime[:10]}'). If asking for a single day, use the same date for both.
            - Summarize the results naturally for the user. IMPORTANT: If 'get_all_schedules' returns holidays or all-day events, make sure to mention them clearly to the user.
            
            E. SEARCHING SPECIFIC EVENTS (e.g., "When is my 'Team Sync' meeting?"):
            - Use the 'get_id_of_schedules' tool with the keyword (e.g., "Team Sync").
            """),
            
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])

        # 4. Bind the Reasoning Engine (The Brain)
        agent_brain = create_tool_calling_agent(
            llm=st.session_state.llm,
            tools=tools,
            prompt=prompt
        )

        # 5. Initialize the Runtime Executor (The Body)
        st.session_state.agent_executor = AgentExecutor(
            agent=agent_brain,
            tools=tools,
            # Inject persistent memory to maintain conversational context
            memory=st.session_state.agent_memory,
            # Enable robust error handling to prevent application crashes from LLM hallucinations
            handle_parsing_errors=True,
        )

    except Exception as e:
        # --- Engine Initialization Error Handling ---
        error_msg = str(e).lower()
        answer = "" 

        # 1. Handle API Quota Limits (Common with Gemini Free Tier)
        if "429" in error_msg or "quota" in error_msg or "resource exhausted" in error_msg:
            answer = "🚨 **API Quota Exceeded**\n\nThe AI Engine is temporarily busy. Google Gemini's limits have been reached. Please wait a minute and try again."
            
        # 2. Handle Invalid API Key (Authentication failed)
        elif "api_key" in error_msg or "403" in error_msg or "permission denied" in error_msg:
             answer = "🔑 **Invalid API Key**\n\nAuthentication failed. Please check the **'🔑 Google API Key'** provided in the sidebar. Ensure it is active and has permissions."

        # 3. Handle Prompt/Template Construction Errors
        elif "template" in error_msg or "placeholder" in error_msg:
             answer = "🧩 **Prompt Template Error**\n\nFailed to construct the Agent's reasoning prompt. Please check the prompt structure."

        # 4. Handle Toolkit Authentication Issues (Replaced Database error)
        elif "credentials" in error_msg or "token" in error_msg or "oauth" in error_msg:
             answer = "🔐 **Google Calendar Auth Error**\n\nThe system could not authenticate with your Google Calendar. Please verify your 'token.json' file."

        # 5. Handle General/Unknown Errors (Catch-all)
        else:
            answer = f"❌ **System Initialization Failed**\n\nAn unexpected error occurred while building the Agent Engine.\n\n**Technical Details:** `{error_msg}`"

        # Display the structured error message
        st.error(answer, icon="⚠️")

# ==========================================
# VISUAL CALENDAR TAB / VIEW MODE
# ==========================================
if options == "Calendar":
    # 1. Render the main header for the Calendar interface
    st.subheader("📆 My Schedule & Events")

    # 2. Provide a manual synchronization button
    # Forces a Streamlit rerun to fetch the latest state from the Google Calendar API
    st.button(
        "🔄 Refresh Calendar",
        on_click=st.rerun,
        help="Click to synchronize and fetch the latest events from your Google Calendar."
    )

    # 3. Retrieve the parsed event payload formatted for FullCalendar.js
    my_schedules = get_schedules()

    # 4. Conditionally render the calendar based on the data type returned
    if isinstance(my_schedules, list):
        
        # Check if the list contains actual events (evaluates to True if not empty)
        if my_schedules:    
            # Define the FullCalendar UI configuration dictionary
            calendar_options = {
                "headerToolbar": {
                    "left": "today prev,next",
                    "center": "title",
                    "right": "dayGridMonth,timeGridWeek,timeGridDay",
                },
                # Set the default view to the daily time-grid for granular schedule visibility
                "initialView": "timeGridDay", 
            }

            # Render the interactive calendar component
            calendar(events=my_schedules, options=calendar_options)
            
        else:
            # Handle the state where the API call succeeds, but the calendar has no events
            st.info("📭 No upcoming events found. Your calendar is currently empty.", icon="ℹ️")
            
    else:
        # 5. Handle the API Error State 
        # If my_schedules is NOT a list, it means get_schedules() returned an error string.
        error_msg = my_schedules
        
        # Display the specific API error clearly to the user
        st.error(f"⚠️ Calendar unavailable due to a system error: {error_msg}", icon="🚨")

# ==========================================
# CHAT INTERFACE & AGENT EXECUTION
# ==========================================
if options == "Chat AI":
    # 1. Render the Conversational History
    # Iterate through the 'messages' array in the session state to persist the conversation 
    # visually across Streamlit's reactive re-runs.
    for msg in st.session_state.messages:
        st.chat_message(msg["role"]).write(msg["content"])

    # 2. Capture User Input
    # The walrus operator (:=) assigns the input to 'prompt_text' and evaluates to True if input exists.
    if prompt_text := st.chat_input("Ask NovaCal AI to check or manage your schedule..."):
        
        # --- Pre-flight Diagnostics (Guardrails) ---
        # Ensure all backend components (LLM, Calendar Toolkit, Agent Executor) are fully primed.
        if st.session_state.llm is None:
            st.warning("⚠️ AI Engine is offline. Please authenticate with your API Key in the sidebar.", icon="🚫")
            
        elif not st.session_state.agent_executor:
            st.warning("⚠️ Agent pipeline is not initialized. Please perform a Full System Reset.", icon="🤖")

        else:
            # --- Process Valid Input ---
            # 3. Append and Display the User's Prompt
            st.session_state.messages.append({"role": "human", "content": prompt_text})
            st.chat_message("human").write(prompt_text)

            # 4. Generate and Stream the AI's Response
            with st.chat_message("ai"):
                try:
                    # Initialize the StreamlitCallbackHandler
                    # Creates an interactive UI container to expose the Agent's "Thought Process" 
                    # (Tool selection, Calendar API execution, and Observation) in real-time.
                    st_callback = StreamlitCallbackHandler(st.container())

                    # Invoke the Calendar Tool-Calling Agent
                    # Passes 'st_callback' so intermediate reasoning steps are rendered dynamically.
                    response = st.session_state.agent_executor.invoke(
                        {"input": prompt_text},
                        {"callbacks": [st_callback]}
                    )

                    # 5. Extract, Validate, and Render the Final Output
                    if "output" in response and len(response["output"]) > 0:
                        # Provide a graceful fallback string if the output is malformed
                        final_answer = response.get("output", "Sorry, I am unable to process that scheduling request right now.")
                        
                        # Type-check and flatten the response if the LLM returns a chunked list
                        if isinstance(final_answer, list):
                            cleaned_text = ""
                            for part in final_answer:
                                if isinstance(part, dict) and "text" in part:
                                    cleaned_text += part["text"]
                                elif isinstance(part, str):
                                    cleaned_text += part
                            final_answer = cleaned_text
                            
                        # Render the final synthesized natural language response
                        st.markdown(final_answer)

                    # 6. Commit the AI's response to the session state memory
                    st.session_state.messages.append({"role": "ai", "content": final_answer})

                except Exception as e:
                    # --- Comprehensive Runtime Error Handling ---
                    error_str = str(e).lower()

                    if "429" in error_str or "resource" in error_str:
                        # Handle Google API rate limits or quota exhaustion
                        st.error("⏳ API Quota Exceeded. Please wait a moment or verify your Google Cloud billing status.", icon="🛑")

                    elif "api_key" in error_str or "400" in error_str:
                        # Handle authentication failures
                        st.error("🔑 Authentication Failed. Please verify your Google Gemini API Key in the sidebar.", icon="🚫")

                    elif "parsing" in error_str:
                        # Handle Agent reasoning loops or unparseable LLM formats
                        st.error("🧩 Reasoning Error. The AI encountered an issue structuring its response. Please rephrase.", icon="😵‍💫")

                    elif "invalid_grant" in error_str or "token" in error_str:
                        # Replaced SQL 'operationalerror' with Calendar OAuth Token Error
                        st.error("🔐 OAuth Token Expired. Please re-authenticate your token.json file with Google Calendar.", icon="📉")

                    else:
                        # Fallback for unexpected system or API errors
                        st.error(f"❌ An unexpected system error occurred: {str(e)}", icon="🚨")