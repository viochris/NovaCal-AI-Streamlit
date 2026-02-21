import os
import json
import streamlit as st
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from langchain.tools import tool

# ==========================================
# SESSION STATE MANAGEMENT
# ==========================================
def init_state():
    """
    Initializes essential session state variables required for the application's lifecycle.
    Ensures that variables exist before they are called, preventing KeyError exceptions
    during Streamlit's reactive UI re-runs.
    """

    # ==========================================
    # DYNAMIC CREDENTIAL GENERATOR FOR STREAMLIT
    # ==========================================
    # LangChain's CalendarToolkit strictly requires physical 'credentials.json' and 'token.json' files.
    # Since we cannot upload these to GitHub, we store their raw JSON strings in st.secrets
    # and dynamically write them to temporary physical files on the server upon startup.

    # 1. Generate 'credentials.json' from st.secrets if it doesn't exist
    if not os.path.exists("credentials.json"):
        if "files" in st.secrets and "google_calendar_credentials" in st.secrets["files"]:
            with open("credentials.json", "w") as f:
                f.write(st.secrets["files"]["google_calendar_credentials"])

    # 2. Generate 'token.json' from st.secrets if it doesn't exist
    if not os.path.exists("token.json"):
        if "files" in st.secrets and "google_calendar_token" in st.secrets["files"]:
            with open("token.json", "w") as f:
                f.write(st.secrets["files"]["google_calendar_token"])

    # ==========================================
    # CORE SESSION STATE VARIABLES
    # ==========================================
    # 1. Initialize the chat history array to store user and AI messages
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # 2. Initialize the Language Model (LLM) instance placeholder
    if "llm" not in st.session_state:
        st.session_state.llm = None

    # 3. Initialize the Google Calendar Toolkit placeholder
    if "toolkit" not in st.session_state:
        st.session_state.toolkit = None

    # 4. Initialize the AI's conversational memory buffer
    # This allows the agent to remember context from previous prompts
    if "agent_memory" not in st.session_state:
        st.session_state.agent_memory = None

# ==========================================
# SYSTEM RESET CALLBACKS
# ==========================================
def change_on_api_key():
    """
    Callback function triggered when the user modifies the API Key input.
    Executes a 'Hard Reset' of the environment to ensure the newly provided credential 
    is properly applied to all future LLM and agent instances.
    """
    # 1. Clear the UI chat history to prevent contextual mismatches with the new key
    st.session_state.messages = []
    
    # 2. Nullify the LLM and memory instances to force a fresh initialization
    st.session_state.llm = None
    st.session_state.agent_memory = None
    
    # 3. Purge the existing Agent Executor from the session state completely.
    # Using .pop() guarantees the key is removed, forcing the app to rebuild the AI pipeline.
    st.session_state.pop("agent_executor", None)
    
    # 4. Display a brief confirmation notification to the user
    st.toast("API Key updated! System environment reset.", icon="🔄")

def reset_state():
    """
    Callback function triggered by the 'Full System Reset' UI button.
    Executes a comprehensive 'Hard Reset': purges the Chat UI, destroys the Agent's conversational memory, 
    and severs any active Google Calendar tool context. 
    Utilize this to return the application to a pure 'Tabula Rasa' (blank slate) state.
    """
    # 1. Purge the visible chat history at the UI level
    st.session_state.messages = []
    
    # 2. Reset core AI components to enforce re-instantiation on the next user interaction
    st.session_state.llm = None
    st.session_state.agent_memory = None 
    
    # 3. Terminate the active Agent Executor process
    st.session_state.pop("agent_executor", None)
    
    # 4. Provide visual feedback of the successful reset operation
    st.toast("System fully reset. AI memory and context wiped!", icon="🔄")

def reset_chat_display():
    """
    Callback function triggered by the 'Clear Screen Only' UI button.
    Executes a UI-level reset by purging the visible chat messages from the Streamlit interface.
    Crucially, the underlying LLM conversational memory ('agent_memory') is PRESERVED, 
    allowing the AI to retain contextual awareness of prior interactions despite the blank screen.
    """
    # 1. Purge the message history array to clear the graphical user interface (GUI)
    st.session_state.messages = []
    
    # 2. NOTE: We intentionally bypass nullifying 'st.session_state.agent_memory' here.
    # This design choice ensures the LangChain memory buffer remains intact for continuity.
    
    # 3. Display a brief confirmation notification to assure the user that context is safe
    st.toast("Screen cleared! AI context retained.", icon="🧹")

# ==========================================
# VISUAL CALENDAR DATA FETCHER (FRONTEND)
# ==========================================
def get_schedules():
    """
    Fetches schedule data from the user's primary Google Calendar to populate the 
    frontend visual calendar component (streamlit_calendar).
    Transforms the raw Google API JSON response into the specific dictionary format 
    required by the frontend library.
    """
    try:
        # 1. Authenticate using the stored OAuth token with full read/write scope
        creds = Credentials.from_authorized_user_file('token.json', ['https://www.googleapis.com/auth/calendar'])
        service = build('calendar', 'v3', credentials=creds)

        # 2. Query the Google Calendar API
        # Fetches up to 2500 events from the primary calendar, ensuring recurring events 
        # are expanded into single instances (singleEvents=True).
        result = service.events().list(
            calendarId="primary",
            maxResults=2500,
            singleEvents=True,
            orderBy='startTime'
        ).execute()

        # 3. Extract the array of event items from the API payload
        raw_events_results = result.get("items", [])

        # 4. Process and format the raw data for the GUI component
        events_for_ui = []
        for event in raw_events_results:
            # Safely extract start and end times, falling back to 'date' for all-day events
            start = event['start'].get('dateTime', event['start'].get('date'))
            end = event['end'].get('dateTime', event['end'].get('date'))
            
            # Construct the event dictionary conforming to the FullCalendar.js standard
            events_for_ui.append({
                "title": event.get('summary', 'Untitled Event'), # Translated fallback title
                "start": start,
                "end": end,
                "backgroundColor": "#FF4B4B", # Streamlit's primary brand red color
                "borderColor": "#FF4B4B"
            })
            
        return events_for_ui

    except Exception as e:
        # 5. Handle and display API or network failures gracefully in the UI
        return f"Failed to fetch visual calendar events: {e}"
        

# ==========================================
# AI TOOL: EVENT ID SEARCHER (THE SNIPER)
# ==========================================
@tool
def get_id_of_schedules(keyword: str) -> str:
    """
    USE THIS TOOL TO FIND THE 'EVENT_ID' BEFORE DELETING OR EDITING AN EVENT. 
    Provide a specific keyword or the name of the event (e.g., 'Meeting' or 'Dentist').
    It searches the primary calendar and returns a list of matching events with their dates, times, and unique IDs.
    """
    try:
        # 1. Authenticate with the Google Calendar API using the predefined scopes
        creds = Credentials.from_authorized_user_file('token.json', ['https://www.googleapis.com/auth/calendar'])
        service = build('calendar', 'v3', credentials=creds)

        # 2. Execute a free-text search query ('q') against the primary calendar
        result = service.events().list(
            calendarId="primary",
            q=keyword,          # The search keyword provided by the AI
            maxResults=10,      # Limit the results to prevent token overflow
            singleEvents=True,  # Expand recurring events into single instances
            orderBy='startTime'
        ).execute()

        # 3. Extract the array of events from the API payload
        events = result.get("items", [])
        
        # 4. Handle the edge case where no events match the search query
        if not events:
            return f"No events found matching the keyword: '{keyword}'."

        # 5. Format the output string so the LLM can easily read the Date, Title, Time, and ID
        response = f"Matching Events Found for '{keyword}':\n"
        
        for e in events:
            title = e.get('summary', 'Untitled Event')
            event_id = e.get('id', 'NO_ID_FOUND')
            
            # Extract raw date/time strings from the API payload
            start_raw = e['start'].get('dateTime', e['start'].get('date'))
            end_raw = e['end'].get('dateTime', e['end'].get('date'))

            # Extract just the 'YYYY-MM-DD' portion for AI context
            event_date = start_raw[:10]

            # Determine if the event is time-bound or an all-day occurrence
            if "T" in start_raw:
                start_time = start_raw[11:16] # Extract HH:MM
                end_time = end_raw[11:16]
                time_str = f"{start_time} - {end_time}"
            else:
                time_str = "All-day"

            # Append the fully formatted event entry (Date, Title, Time, and ID in one single line)
            response += f"- [{event_date}] '{title}' ({time_str}) | EVENT_ID: {event_id}\n"
            
        return response

    except Exception as e:
        # 6. Return a graceful error message back to the AI agent if the API call fails
        return f"Error executing search tool: {str(e)}"

# ==========================================
# AI TOOL: DATE RANGE SCHEDULE FETCHER
# ==========================================
@tool
def get_all_schedules(start_date: str, end_date: str) -> str:
    """
    USE THIS TOOL TO RETRIEVE ALL SCHEDULED EVENTS AND HOLIDAYS WITHIN A SPECIFIC DATE RANGE.
    The 'start_date' and 'end_date' inputs MUST be strictly in 'YYYY-MM-DD' format.
    If the user asks for a single day's schedule (e.g., "today"), provide the exact same date for both inputs.
    """
    try:
        # 1. Authenticate with the Google Calendar API using the predefined scopes.
        creds = Credentials.from_authorized_user_file('token.json', ['https://www.googleapis.com/auth/calendar'])
        service = build('calendar', 'v3', credentials=creds)

        
        # 2. Format the time boundaries (Appending +07:00 for WIB/Jakarta Timezone)
        timeMin = f"{start_date}T00:00:00+07:00"
        timeMax = f"{end_date}T23:59:59+07:00"

        # 3. Define the list of target calendars (Primary user calendar & Indonesian Holidays)
        target_calendars = ['primary', 'id.indonesian#holiday@group.v.calendar.google.com']
        all_events = []

        # 4. Iterate through each calendar and aggregate the matching events
        for calendar_id in target_calendars:
            try: 
                result = service.events().list(
                    calendarId=calendar_id,
                    timeMin=timeMin,
                    timeMax=timeMax,
                    maxResults=50,      # Increased limit to accommodate multi-day ranges
                    singleEvents=True,  # Expand recurring events into single instances
                    orderBy='startTime'
                ).execute()
                all_events.extend(result.get("items", []))
            except:
                # Silently skip if a specific calendar is inaccessible or fails
                continue

        # 5. Handle the edge case where no events are found in the given timeframe
        if not all_events:
            return f"No events scheduled from {start_date} to {end_date}."

        # 6. Format the aggregated events into a clean, readable string for both UI and AI context
        response = f"Schedule from {start_date} to {end_date}:\n"
        
        for e in all_events:
            title = e.get('summary', 'Untitled Event')
            
            # Extract raw date/time strings from the API payload
            start_raw = e['start'].get('dateTime', e['start'].get('date'))
            end_raw = e['end'].get('dateTime', e['end'].get('date'))

            # Extract just the 'YYYY-MM-DD' portion for clear visual grouping
            event_date = start_raw[:10]

            # Determine if the event is time-bound or an all-day occurrence
            if "T" in start_raw:
                start_time = start_raw[11:16] # Extract HH:MM
                end_time = end_raw[11:16]
                time_str = f"{start_time} - {end_time}"
            else:
                time_str = "All-day"

            # Append the formatted event entry (Notice: NO EVENT_ID here to keep UI clean)
            response += f"- [{event_date}] {title} ({time_str})\n"
            
        return response

    except Exception as e:
        # 7. Gracefully return the error back to the AI agent
        return f"Error executing schedule fetcher: {str(e)}"