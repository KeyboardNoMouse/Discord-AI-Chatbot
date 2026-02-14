# ☁️ Sky - AI Discord Companion

Sky is a smart, context-aware Discord chatbot powered by **Google's Gemini 2.5 Flash** model. Unlike basic bots, Sky maintains conversation history, understands context, and handles long responses by intelligently splitting messages.

Built with `discord.py` and the `google-generativeai` SDK.

## 🚀 Features
* **Persistent Memory:** Remembers previous messages in the current session.
* **Smart Chunking:** Automatically splits responses >2000 characters to fit Discord limits.
* **Low Latency:** Uses the Gemini 2.5 Flash model for near-instant replies.
* **Typing Indicators:** Simulates "thinking" while processing API requests.

## 🛠️ Installation

1.  **Clone the repository**
    ```bash
    git clone [https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git](https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git)
    cd YOUR_REPO_NAME
    ```

2.  **Install dependencies**
    ```bash
    pip install discord.py python-dotenv google-generativeai
    ```

## 🔑 Configuration (Important)

To run this bot, you need to create a `.env` file to store your private keys.

1.  **Create a file named `.env`** in the main folder.
2.  **Paste the following text inside it:**

    ```env
    DISCORD_TOKEN=paste_your_discord_token_here
    GEMINI_API_KEY=paste_your_gemini_api_key_here
    ```

### How to get the Keys:

#### 1. Get the Discord Token
1. Go to the [Discord Developer Portal](https://discord.com/developers/applications).
2. Click **New Application** and name it (e.g., Sky).
3. Go to the **Bot** tab on the left.
4. Click **Reset Token** to generate your `DISCORD_TOKEN`.
5. **CRITICAL:** Scroll down to "Privileged Gateway Intents" and toggle **ON** `Message Content Intent`. (The bot will not work without this!).

#### 2. Get the Gemini API Key
1. Go to [Google AI Studio](https://aistudio.google.com/app/apikey).
2. Click **Create API Key**.
3. Select "Create API key in new project".
4. Copy the key string starting with `AIza`.

## ⚡ Usage

Run the bot using Python:

```bash
python main.py
