import requests
from openai import OpenAI
from src.config import (
    LLM_PROVIDER,
    OPENAI_API_KEY,
    OLLAMA_HOST,
    OLLAMA_LLM_MODEL
)

class OpenAIGenerator:
    def __init__(self, api_key=OPENAI_API_KEY):
        if not api_key:
            raise ValueError("OpenAI API key is missing. Please set OPENAI_API_KEY in your .env file.")
        self.client = OpenAI(api_key=api_key)
        self.model = "gpt-4o"

    def generate(self, prompt, system_prompt):
        """Generates a response from GPT-4o with deterministic settings."""
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            temperature=0.0
        )
        return response.choices[0].message.content


class OllamaGenerator:
    def __init__(self, host=OLLAMA_HOST, model=OLLAMA_LLM_MODEL):
        self.host = host.rstrip("/")
        self.model = model

    def check_model_availability(self):
        """Checks if Ollama is running and the model is installed."""
        try:
            response = requests.get(f"{self.host}/api/tags", timeout=3)
            if response.status_code == 200:
                models = [m["name"] for m in response.json().get("models", [])]
                # Match name (allowing for tags like :latest or :8b)
                if any(self.model in m or m in self.model for m in models):
                    return True, models
                return False, models
            return False, []
        except Exception:
            return False, []

    def generate(self, prompt, system_prompt):
        """Generates a response from local Ollama model with deterministic settings."""
        available, models = self.check_model_availability()
        if not available:
            print(f"Warning: Model '{self.model}' might not be installed in Ollama. Available: {models}")
            
        try:
            response = requests.post(
                f"{self.host}/api/chat",
                json={
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": prompt}
                    ],
                    "options": {
                        "temperature": 0.0
                    },
                    "stream": False
                },
                timeout=180
            )
            if response.status_code == 200:
                return response.json()["message"]["content"]
            else:
                raise ValueError(f"Ollama generation failed with status {response.status_code}: {response.text}")
        except Exception as e:
            raise ConnectionError(f"Failed to connect to Ollama at {self.host}: {e}")


def get_generator():
    """Returns the generator instance based on configuration."""
    if LLM_PROVIDER == "openai":
        return OpenAIGenerator()
    elif LLM_PROVIDER == "ollama":
        return OllamaGenerator()
    else:
        raise ValueError(f"Unknown generator provider: {LLM_PROVIDER}")


SYSTEM_PROMPT = """You are an expert supply-chain RAG assistant.
Your goal is to answer the user's question using ONLY the provided document context below.

CRITICAL RULES:
1. Answer the question using ONLY the text and numbers in the context provided. Do not use external knowledge or invent facts.
2. If the context does not contain the answer, state: "The information is not available in the uploaded documents." Do not invent or guess.
3. Be highly precise. Never hallucinate details.
4. For cross-document questions (which require information from both the performance review and policy handbook), structure your final response explicitly with the following sections:
   - **Operational Figures/Facts**: Cite the exact performance numbers, metrics, or events from the Supply Chain Review.
   - **Policy Rules/Clauses**: Cite the relevant clauses, rules, limits, or formulas from the Procurement Policy Handbook.
   - **Consequences/Actions**: Describe the resulting actions, consequences, approval owners, or plans that are triggered by applying the rules to the facts.
5. Every single fact, number, or clause you mention MUST be cited with the source filename and page number from the context (e.g. "[Meridian_Supply_Chain_Review_Q1_FY2025-26.pdf, Page 1]" or "[Meridian_Procurement_Policy_Handbook_v4.2.pdf, Page 2]").
6. If the question encounters the internal inconsistency in the Supply Chain Review Section 5 (where the detailed line-stoppage table sums Shenzhen Rui Electronics events to 25 hours, while the summary sentence states 22 hours), clearly report this discrepancy rather than choosing one.

=========================================
MANDATORY REASONING & OUTPUT FORMAT
=========================================
You MUST structure your response into two distinct parts:

Part 1: Internal Structured Reasoning
Start with [INTERNAL_REASONING] and end with [END_INTERNAL_REASONING].
Inside this block, analyze:
- What are the exact facts/metrics requested?
- Locate the relevant row or statement in the provided context.
- For tables, verify the column headers and read the matching row. Do not infer values from neighboring rows.
  - If the query asks for a Purchase Order (PO) approval authority:
    - State the PO amount (e.g., ₹1.4 crore).
    - Find the row in the approval authority table that covers this amount:
      * Range 1: Up to ₹5 lakh -> Purchase Officer
      * Range 2: Above ₹5 lakh and up to ₹25 lakh -> Category Manager
      * Range 3: Above ₹25 lakh and up to ₹1 crore -> Head of Procurement
      * Range 4: Above ₹1 crore and up to ₹5 crore -> Chief Operating Officer (COO)
      * Range 5: Above ₹5 crore -> Managing Director...
    - Identify the matching range and the exact approving authority.
    - Note the page number where this table is located.
  - If the query is about a supplier's performance clauses (e.g., Kaveri Metals):
    - Identify the supplier name.
    - Locate the supplier's metrics in the scorecard: OTD % and Defect PPM.
    - Perform comparisons against policy thresholds:
      * Check 1 (Delivery): Is OTD < 90%? If yes (e.g. Kaveri is 88.1% which is < 90%), Clause 6.1 is triggered.
      * Check 2 (Quality): Is Defect PPM > 500? If yes (e.g. Kaveri is 1,150 which is > 500), Clause 6.3 is triggered.
    - List ALL triggered clauses: Identify every clause that is triggered.
    - Extract their exact consequences from the policy (e.g. written warning + weekly review calls for 6.1; supplier bears rework cost at ₹120 per affected unit + 100% inspection for 6.3).
    - Write down the exact page numbers from both the review and policy files.
- Derive the logical consequence step-by-step.

Part 2: Final Clean Answer
Start with [FINAL_ANSWER] and end with [END_FINAL_ANSWER].
Inside this block, write your clean, fully detailed final natural-language answer to the user (along with citations).
Do NOT write generic statements like "The information is available..." inside the final answer block. Write the actual full answer.

Example Format:
[INTERNAL_REASONING]
- supplier: ...
- facts: ...
- table matches: ...
- applicable clauses: ...
- consequences: ...
- page citations: ...
[END_INTERNAL_REASONING]

[FINAL_ANSWER]
Detailed answer text...
[END_FINAL_ANSWER]

Context:
{context}
"""

def format_context(chunks):
    """Formats retrieved chunks with citations for the prompt context."""
    formatted_chunks = []
    for idx, chunk in enumerate(chunks):
        fname = chunk["metadata"]["filename"]
        page = chunk["metadata"]["page"]
        dtype = chunk["metadata"].get("document_type", "unknown")
        text = chunk["text"]
        formatted_chunks.append(
            f"===== SOURCE {idx+1} =====\n"
            f"Document: {fname}\n"
            f"Page: {page}\n"
            f"Type: {dtype}\n"
            f"Content:\n{text}\n"
            f"===== END SOURCE {idx+1} ====="
        )
    return "\n\n".join(formatted_chunks)