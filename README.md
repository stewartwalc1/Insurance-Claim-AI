# InsuranceGenAI | Intelligent Claims Adjuster (Technical PoC)

InsuranceGenAI is a proof-of-concept (PoC) platform designed to automate the triage and analysis of homeowners insurance claims. By orchestrating multiple specialized AI models via Amazon Bedrock, the system extracts claim data, validates it against policy documents using RAG (Retrieval-Augmented Generation), and drafts empathetic customer communications—all while enforcing enterprise-grade PII masking.

> **Disclaimer:** This project is a **Technical Proof of Concept**. It is designed to demonstrate AI orchestration, RAG implementation, and security guardrails. It is not a production-ready business solution and lacks persistent database storage (DynamoDB/PostgreSQL) and user authentication (AWS Cognito).

---

## Architecture & AI Orchestration

The system follows a "Team of Models" approach, leveraging the strengths of different LLMs for specific business tasks:

| Task | AI Model | Why this model? |
| :--- | :--- | :--- |
| **Data Extraction** | `Claude 3.5 Sonnet` | High reasoning capability for complex PDF parsing. |
| **Policy Analysis** | `Amazon Nova Micro` | Optimized for speed and cost-effective logic processing. |
| **Customer Email** | `Claude 3.5 Haiku` | Excellent at maintaining a specific, empathetic tone. |



---

## Key Features

### 1. Retrieval-Augmented Generation (RAG)
Rather than relying on pre-trained knowledge, the system queries an Amazon Bedrock Knowledge Base. It retrieves actual policy clauses from uploaded PDF contracts to ground the AI's decision in real legal text.

### 2. Privacy-First Security (Guardrails)
Implemented Amazon Bedrock Guardrails to provide:
* **PII Masking:** Automatically redacts phone numbers, emails, and addresses.
* **Content Filtering:** Ensures the model does not provide unauthorized legal advice or use inappropriate language.

### 3. "Flood Gate" Business Logic
A built-in safety valve that detects high-severity keywords (e.g., "Flood"). If a catastrophic event is detected, the AI automatically pauses the automation and flags the claim for Manual Human Intervention.

### 4. Parallel Performance
Uses Python's `ThreadPoolExecutor` to handle S3 file uploads and AI model invocations simultaneously, reducing user wait times by ~30%.

---

## Getting Started

### Prerequisites
* AWS Account with Bedrock Model access enabled.
* Python 3.9+
* Environment variables configured in a `.env` file.

### Installation & Setup
1. **Clone the repository:**
   ```bash
   git clone https://github.com/stewartwalc1/Insurance-Claim-AI.git 
   cd Insurance-Claim-AI

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt

3. **Configure Environment (.env):**
   ```bash
   S3_BUCKET_NAME=your-bucket-name
   KNOWLEDGE_BASE_ID=your-kb-id
   GUARDRAIL_ID=your-guardrail-id
   GUARDRAIL_VERSION=3

4. **Run the Application:**
   ```bash
   python app.py

---

## Technical Implementation Details

* Solved PDF I/O errors by using io.BytesIO buffers for simultaneous S3 uploading and text extraction.
* Implemented custom logic to isolate AI-generated JSON from conversational filler.
* Built with Tailwind CSS, featuring a real-time JavaScript loading state for a reactive user experience.
