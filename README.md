# 📅 NovaCal AI: Intelligent Google Calendar Assistant

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?logo=streamlit&logoColor=white)
![LangChain](https://img.shields.io/badge/LangChain-Agent-blueviolet?logo=langchain&logoColor=white)
![Google Gemini](https://img.shields.io/badge/Gemini%202.5%20Flash-8E75B2?logo=google&logoColor=white)
![Google Calendar](https://img.shields.io/badge/Google%20Calendar-API-4285F4?logo=googlecalendar&logoColor=white)
![Status](https://img.shields.io/badge/Status-Active-success)

## 📌 Overview
**NovaCal AI** is an advanced, AI-powered personal scheduling assistant built with **Google's Gemini 2.5 Flash** and the **LangChain Tool-Calling Agent** architecture.

Unlike standard chatbots that struggle with external APIs, NovaCal utilizes a deterministic reasoning engine. It understands your natural language requests, strategically selects the correct Google Calendar tools, and executes precise scheduling actions (Create, Read, Update, Delete). It features a dual-interface design, offering both a conversational AI chat and a fully interactive Visual Calendar dashboard.

> **🚀 COMING SOON:** This repository contains the **Streamlit (Web UI)** version of NovaCal AI. A fully integrated **Telegram Bot version** is currently in development. Stay tuned!

## ✨ Key Features

### 🧠 Tool-Calling Agent Architecture
Using `create_tool_calling_agent`, the system navigates a strict Standard Operating Procedure (SOP):
1.  **Analyze Intent:** Understands complex time-based requests relative to the current system time.
2.  **Execute Tools:** Uses custom-built, highly optimized tools like `get_id_of_schedules` (The Sniper) and `get_all_schedules` to reliably fetch data.
3.  **Self-Correction (Swap Method):** If an event update fails, the Agent seamlessly falls back to creating a new event and deleting the old one.

### 🗂️ Dual Navigation Interface
* **💬 Chat AI Mode:** A conversational interface where the Agent displays its step-by-step reasoning (Thought -> Action -> Observation) in real-time via `StreamlitCallbackHandler`.
* **📆 Visual Calendar Mode:** A dynamic frontend calendar (powered by `streamlit-calendar` & FullCalendar.js) that visualizes your schedule and automatically syncs with your Google Calendar data.

### 🛡️ Robust State & Memory Management
* **Persistent Conversational Memory:** The AI maintains context across interactions using `ConversationBufferMemory`.
* **Dual Reset Modes:**
    * `🧹 Clear Screen Only`: Clears the UI to declutter the screen, but the AI **retains its memory** of the conversation.
    * `🔄 Full System Reset`: Performs a "Hard Reset"—wiping memory, killing the agent executor, and clearing the UI.

## 🛠️ Tech Stack
* **LLM:** Google Gemini 2.5 Flash (via `ChatGoogleGenerativeAI`).
* **Framework:** Streamlit (Frontend & State Management).
* **Orchestration:** LangChain (Tool-Calling Agent & Memory).
* **Calendar Integration:** Google Calendar API (`google-api-python-client` & `CalendarToolkit`).
* **UI Components:** `streamlit-calendar`.

## ⚠️ Limitations & Disclaimers

### 1. Authentication Setup
* Requires a manual initial setup to generate a `token.json` file via the Google Cloud Console (OAuth 2.0 Client IDs) before the script can access your calendar.

### 2. Timezone Hardcoding
* The time boundary extraction in the custom fetcher tools currently uses a fixed `+07:00` (WIB/Jakarta) timezone offset for daily queries.

### 3. Native Tool Bypassing
* Native LangChain search tools (`CalendarSearchEvents`) are intentionally disabled/banned in the system prompt due to instability, replaced entirely by custom-built extraction functions for maximum reliability.

## 📦 Installation

1.  **Clone the Repository**
    ```bash
    git clone https://github.com/viochris/NovaCal-AI-Streamlit.git
    cd NovaCal-AI-Streamlit
    ```

2.  **Install Dependencies**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Setup Google Calendar Credentials**
    * Go to the [Google Cloud Console](https://console.cloud.google.com/).
    * Enable the **Google Calendar API**.
    * Create **OAuth client ID** credentials (Desktop App).
    * Download the credentials and run a local auth script once to generate your `token.json` file.
    * Place the `token.json` file directly in the root directory of this project.

4.  **Run the Application**
    ```bash
    streamlit run app.py
    ```

## 🚀 Usage Guide

1.  **Configuration (Sidebar):**
    * Enter your **Google Gemini API Key** (Required to ignite the AI engine).
    * View your immediate **Today's Agenda** directly in the sidebar panel.
2.  **Navigation:**
    * Use the dropdown menu to switch between **Chat AI** (for interacting) and **Visual Calendar** (for viewing).
3.  **Chat Interaction:**
    * Type your scheduling requests naturally (e.g., *"Schedule a 1-hour team sync tomorrow at 2 PM"* or *"When is my dentist appointment?"*).
    * The Agent will execute the required API calls and confirm the action.
4.  **Manage:**
    * If the AI encounters an unparseable error or you switch Google accounts, use the **"🔄 Full System Reset"** button to force a clean slate.

## 📷 Gallery

### 1. Landing Interface & Sidebar Configuration
![Home UI](assets/home_ui.png)  
*The clean landing interface featuring the dual-mode navigation, secure API key input, and an automatically updating "Today's Agenda" widget in the sidebar.*

### 2. Visual Calendar Dashboard
![Calendar View](assets/calendar_view.png)  
*The interactive Visual Calendar mode, retrieving real-time data from the Google Calendar API and rendering it cleanly using FullCalendar.js.*

### 3. Transparent AI Reasoning
![Reasoning Trace](assets/reasoning_thought_process.png)  
*In Chat Mode, users can monitor the Agent's internal logic as it invokes custom tools like `get_id_of_schedules` to snipe exact Event IDs before modifying the calendar.*

### 4. Successful Execution
![Result](assets/result.png)  
*The Agent finalizes the operation (e.g., booking a new event) and provides a clear, natural language confirmation back to the user.*

---
**Author:** [Silvio Christian, Joe](https://www.linkedin.com/in/silvio-christian-joe)
*"Automate your schedule. Experience intelligent time management."*
