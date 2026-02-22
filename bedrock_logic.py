import boto3
import json
import os

class ClaimProcessor:
    def __init__(self):
        self.bedrock = boto3.client('bedrock-runtime')
        self.kb_client = boto3.client('bedrock-agent-runtime')
    
        self.extraction_model = 'us.anthropic.claude-3-5-sonnet-20241022-v2:0'
        self.policy_analysis = 'us.amazon.nova-micro-v1:0'
        self.summary_model = 'us.anthropic.claude-3-5-haiku-20241022-v1:0'

        self.kb_id = os.getenv('KNOWLEDGE_BASE_ID')

        self.guardrail_id = os.getenv('GUARDRAIL_ID')
        self.guardrail_version = os.getenv('GUARDRAIL_VERSION', '1')
    
    def _invoke_claude(self, model_id, system_prompt, user_content):
        body = json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 1000,
            "system": system_prompt,
            "messages": [{"role": "user", "content": user_content}]
        })

        response = self.bedrock.invoke_model(
            modelId=model_id, 
            body=body,
            guardrailIdentifier=self.guardrail_id,
            guardrailVersion=self.guardrail_version
            )

        response_body = json.loads(response.get('body').read())

        if 'amazon-bedrock-guardrailAction' in response:
            if response['amazon-bedrock-guardrailAction'] == 'INTERVENED':
                return '{"error": "Content blocked by safety filters."}'

        return response_body['content'][0]['text']

    def _invoke_nova(self, model_id, system_prompt, user_content):
        full_prompt = f"{system_prompt}\n\nUser: {user_content}"
        
        body = json.dumps({
            "inferenceConfig": {
                "max_new_tokens": 500,
                "temperature": 0.1, 
                "topP": 0.9
            },
            "messages": [
                {
                    "role": "user",
                    "content": [{"text": full_prompt}]
                }
            ]
        })

        response = self.bedrock.invoke_model(modelId=model_id, body=body)
        response_body = json.loads(response.get('body').read())
        return response_body['output']['message']['content'][0]['text']

    def extract_info(self, document_text):
        system_prompt = """You are an expert Insurance Data Analyst. Your goal is to extract structured data from homeowners insurance claim documents. 
        <instructions> 
        1. Extract the information into the JSON schema provided. 
        2. If a value is masked or missing, use "null". 
        3. For 'cause_of_loss', choose only from: [Fire, Theft, Water, Wind, Liability, Flood, Other]. 
        4. Output ONLY the raw JSON. No introductory text. 
        Note: If the user mentions rising water from a body of water, overflowing rivers, or heavy rain flooding a basement, categorize this specifically as "Flood" . 
        </instructions> 
        <json_schema> 
        { "claimant": { "name": "string", "policy_number": "string" }, "incident": { "date": "YYYY-MM-DD", "cause_of_loss": "string", "description": "string", "estimated_cost": "number" } } 
        </json_schema>"""
        
     
        user_content = f"Please extract the data from this claim document: <claim_text> {document_text} </claim_text>"
        return self._invoke_claude(self.extraction_model, system_prompt, user_content)

    def retrieve_policy(self, query):
        if not query:
            return "No claim facts provided for policy lookup."
            
        response = self.kb_client.retrieve(
            knowledgeBaseId=self.kb_id,
            retrievalQuery={'text': str(query)} 
        )
        return " ".join([res['content']['text'] for res in response['retrievalResults']])

    def analyze_coverage(self, claim_data, policy_context):
        system_prompt = """You are a Senior Insurance Adjuster specializing in homeowners coverage..."""
        
        user_content = f"""<claim_facts> {claim_data} </claim_facts> 
        <policy_text> {policy_context} </policy_text> 
        Does the policy cover this claim? Provide a structured reasoning and cite the specific section name."""
        
        return self._invoke_nova(self.policy_analysis, system_prompt, user_content)

    def generate_summary(self, analysis_result, claimant_name="Customer"):
        system_prompt = "You are an empathetic Customer Service Assistant for an insurance company. Translate technical adjuster notes into a helpful, clear, and professional email. Always acknowledge the claimant's situation with empathy."
        
        user_content = f"""<adjuster_decision> {analysis_result} </adjuster_decision> 
        Write a short email to the customer ({claimant_name}) explaining the decision. 
        If covered, tell them the next steps. If denied, explain why gently and mention the appeal process."""
        
        return self._invoke_claude(self.summary_model, system_prompt, user_content)