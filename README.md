InsuranceGenAI | Intelligent Claims Adjuster (Technical PoC)
InsuranceGenAI is a proof-of-concept (PoC) platform designed to automate the triage and analysis of homeowners insurance claims. By orchestrating multiple specialized AI models via Amazon Bedrock, the system extracts claim data, validates it against policy documents using RAG (Retrieval-Augmented Generation), and drafts empathetic customer communications—all while enforcing enterprise-grade PII masking.

Note: This is a technical demonstration of implementation and AI orchestration. It is not a production-ready business solution and lacks persistent database storage and user authentication.

The Architecture
The system follows a "Team of Models" approach to ensure the highest accuracy for specific tasks:

Extraction: Claude 3.5 Sonnet extracts structured data from unstructured claim letters.

Logic & Analysis: Amazon Nova Micro performs the heavy lifting of policy cross-referencing.

Communication: Claude 3.5 Haiku generates customer-facing emails.

Security: Amazon Bedrock Guardrails masks PII (Emails, Phones) on both input and output.

Key Features
1. Robust Data Extraction
Converts messy, human-written claim letters into structured JSON. Includes a custom "Flood Gate" logic that identifies high-risk claims (Floods) and flags them for mandatory human review.

2. Retrieval-Augmented Generation (RAG)
Instead of relying on the model's general knowledge, InsurAI queries an Amazon Bedrock Knowledge Base populated with actual policy PDF documents to ensure decisions are grounded in real contract terms.

3. Privacy-First Design
Implemented PII Masking using Bedrock Guardrails. The system identifies sensitive entities like phone numbers and email addresses and masks them before they are processed by the LLM, ensuring data privacy by design.

4. Optimized Performance
Uses Python's ThreadPoolExecutor to handle S3 file uploads and AI model invocations in parallel, reducing the total processing time by approximately 30%.

🚀 Getting Started
Prerequisites
AWS Account with Amazon Bedrock model access (Claude 3.5 & Nova).

Python 3.9+

S3 Bucket and Bedrock Knowledge Base set up with policy documents.

Installation
Clone the repo:

Bash
git clone https://github.com/your-username/insurai-poc.git
cd insurai-poc
Install dependencies:

Bash
pip install -r requirements.txt
Configure Environment Variables:
Create a .env file in the root directory:

Code snippet
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret
S3_BUCKET_NAME=your_bucket
KNOWLEDGE_BASE_ID=your_kb_id
GUARDRAIL_ID=your_guardrail_id
GUARDRAIL_VERSION=3
🛠️ Technical Challenges Overcome
Handling PDF I/O: Solved "Closed File" errors by reading PDF bytes into memory buffers before passing them to the S3 uploader and the PDF parser simultaneously.

Guardrail False Positives: Tuned Amazon Bedrock Guardrail content filters to "Low" to allow professional insurance terminology (e.g., "destroyed," "loss," "water damage") to pass through while still masking personal contact info.

JSON Parsing: Built a custom "stripper" function to handle Claude's conversational output and isolate the raw JSON objects for the backend.