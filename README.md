🚀 Supply Chain AI Agent (Vertex AI + Cloud Run)

An AI-powered supply chain assistant built using Google Cloud Platform. This project leverages large language models via Vertex AI and is deployed as a scalable API using Cloud Run.

📌 Overview

This project demonstrates how to build and deploy a real-world AI agent that can process supply chain-related queries and generate intelligent responses.

The system integrates:

Generative AI (Vertex AI)
Scalable backend (Cloud Run)
Cloud-native deployment
🧠 Key Features
🤖 AI-powered query handling using Vertex AI (LLMs)
📦 Supply chain insights and responses
⚡ Serverless deployment using Cloud Run
🔄 REST API-based interaction
☁️ Fully deployed on Google Cloud
🏗️ Architecture
User Request
     ↓
Cloud Run API (Python Backend)
     ↓
Vertex AI (LLM - Gemini / PaLM)
     ↓
Response Generation
     ↓
User Output
🛠️ Tech Stack
Google Cloud Platform (GCP)
Vertex AI (Generative AI)
Cloud Run (Serverless Deployment)
Python
REST APIs
🚀 Deployment Details
Platform: Google Cloud Run
Region: us-central1
Backend: Python-based API service
AI Model: Vertex AI (Gemini / PaLM)
🧪 Sample Prompts (for testing)

Use these prompts to test the system:

“Analyze supply chain risks for a retail company”
“What are the common bottlenecks in logistics?”
“Suggest ways to optimize inventory management”
“How can AI improve demand forecasting?”
“Explain supply chain disruptions and mitigation strategies”
📸 Screenshots (Add these)

Include screenshots of:

✅ Cloud Run deployment logs
✅ Successful API response
✅ Prompt → AI-generated output
✅ Google Cloud console (service running)
⚙️ How to Run Locally
# Clone repo
git clone https://github.com/shabbeersyed/scm-memory-agent.git

# Navigate
cd scm-memory-agent

# Install dependencies
pip install -r requirements.txt

# Run app
python app.py
🔐 Environment Setup

Make sure to configure:

Google Cloud credentials
Vertex AI access
Required environment variables
📈 Future Improvements
Add frontend UI (React / Streamlit)
Integrate real-time supply chain datasets
Implement RAG (Retrieval-Augmented Generation)
Add authentication & monitoring
💼 Resume Impact

Built and deployed a Supply Chain AI Agent using Google Cloud Vertex AI and Cloud Run, enabling intelligent query processing and scalable API-based AI interactions.

👤 Author

Shabbeer Basha Syed
Master’s in Information Systems & Technology
University of North Texas
