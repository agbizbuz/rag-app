import os
import re
from openai import OpenAI, APIError as OpenAIAPIError
from anthropic import Anthropic, APIError as AnthropicAPIError


def get_llm_response(query_context: str, llm_model: str) -> str:
    """
    Queries the selected LLM provider using the provided context and prompt.

    Provider selection by model name prefix:
        groq:<model>         → Groq (API key: GROQ_API_KEY)
        ollama:<model>       → Ollama (local, no key; set OLLAMA_BASE_URL)
        lmstudio:<model>     → LM Studio (local, no key; set LM_STUDIO_BASE_URL)
        meta-llama/...       → HuggingFace Inference API (API key: HUGGINGFACE_API_KEY)
        gpt-*                → OpenAI
        claude-*             → Anthropic
        gemini-*             → Google Gemini
    """
    # We prepend a system-style instruction directly to the user prompt for simplicity
    prompt = f"""
You are a highly capable research assistant. Answer the user's query strictly based on the provided context.
If the context does not contain sufficient information to answer the question, respectfully state that the information is not found in the documents.

Provide the answer clearly and concisely.

=== PROVIDED CONTEXT ===
{query_context}

=== USER QUERY ===
"""

    model_lower = llm_model.lower().strip()

    # ---------------------------------------------------------------
    # 1. Groq (OpenAI-compatible API)
    # ---------------------------------------------------------------
    if model_lower.startswith("groq:"):
        if not os.environ.get("GROQ_API_KEY"):
            return "⚠️ Error: `GROQ_API_KEY` is missing in the environment."

        groq_client = OpenAI(
            api_key=os.environ["GROQ_API_KEY"],
            base_url="https://api.groq.com/openai/v1",
        )
        actual_model = llm_model[len("groq:"):]
        try:
            response = groq_client.chat.completions.create(
                model=actual_model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
            )
            return response.choices[0].message.content
        except OpenAIAPIError as e:
            return f"⚠️ Groq API Error: {e}"

    # ---------------------------------------------------------------
    # 2. Ollama (OpenAI-compatible local server)
    # ---------------------------------------------------------------
    elif model_lower.startswith("ollama:"):
        ollama_base_url = os.environ.get(
            "OLLAMA_BASE_URL", "http://localhost:11434/v1"
        )
        actual_model = llm_model[len("ollama:"):]
        try:
            ollama_client = OpenAI(
                api_key="ollama",
                base_url=ollama_base_url,
            )
            response = ollama_client.chat.completions.create(
                model=actual_model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
            )
            return response.choices[0].message.content
        except OpenAIAPIError as e:
            return f"⚠️ Ollama API Error: {e}"

    # ---------------------------------------------------------------
    # 3. LM Studio (OpenAI-compatible local server)
    # ---------------------------------------------------------------
    elif model_lower.startswith("lmstudio:") or model_lower.startswith("lm-studio:"):
        prefix_len = len("lmstudio:") if model_lower.startswith("lmstudio:") else len("lm-studio:")
        actual_model = llm_model[prefix_len:]
        lm_studio_base_url = os.environ.get(
            "LM_STUDIO_BASE_URL", "http://localhost:1234/v1"
        )
        try:
            lm_client = OpenAI(
                api_key="lm-studio",
                base_url=lm_studio_base_url,
            )
            response = lm_client.chat.completions.create(
                model=actual_model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
            )
            return response.choices[0].message.content
        except OpenAIAPIError as e:
            return f"⚠️ LM Studio API Error: {e}"

    # ---------------------------------------------------------------
    # 4. HuggingFace Inference API (REST)
    # ---------------------------------------------------------------
    elif re.match(r"^[\w-]+/[\w.-]+", llm_model.strip()) and not re.match(
        r"^(gpt|claude|gemini|ollama|groq|lmstudio|lm-studio)", model_lower
    ):
        # Looks like a HuggingFace Hub model ID (user/model format)
        if not os.environ.get("HUGGINGFACE_API_KEY"):
            return "⚠️ Error: `HUGGINGFACE_API_KEY` is missing in the environment."

        try:
            import requests

            response = requests.post(
                f"https://api-inference.huggingface.co/models/{llm_model.strip()}",
                headers={"Authorization": f"Bearer {os.environ['HUGGINGFACE_API_KEY']}"},
                json={"inputs": prompt, "parameters": {"max_new_tokens": 1024}},
            )
            response.raise_for_status()
            result = response.json()

            # HF returns either [{"generated_text": "..."}] or just the string
            if isinstance(result, list) and len(result) > 0:
                return result[0].get("generated_text", result[0])
            elif isinstance(result, str):
                return result
            else:
                return f"⚠️ Unexpected HuggingFace response format: {result}"
        except requests.exceptions.HTTPError as e:
            if e.response is not None and e.response.status_code == 429:
                return "⚠️ HuggingFace Inference API: rate limited. Try again later or use a self-hosted model."
            return f"⚠️ HuggingFace API Error: {e}"
        except requests.exceptions.RequestException as e:
            return f"⚠️ HuggingFace API Error: {e}"

    # ---------------------------------------------------------------
    # 5. OpenAI (existing)
    # ---------------------------------------------------------------
    if "gpt" in model_lower:
        if not os.environ.get("OPENAI_API_KEY"):
            return "⚠️ Error: `OPENAI_API_KEY` is missing in the environment."

        openai_client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
        try:
            response = openai_client.chat.completions.create(
                model=llm_model, messages=[{"role": "user", "content": prompt}], temperature=0.2
            )
            return response.choices[0].message.content
        except OpenAIAPIError as e:
            return f"⚠️ OpenAI API Error: {e}"

    # ---------------------------------------------------------------
    # 6. Anthropic (existing)
    # ---------------------------------------------------------------
    elif "claude" in model_lower:
        if not os.environ.get("ANTHROPIC_API_KEY"):
            return "⚠️ Error: `ANTHROPIC_API_KEY` is missing in the environment."

        anthropic_client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
        try:
            response = anthropic_client.messages.create(
                model=llm_model, max_tokens=1024, messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text
        except AnthropicAPIError as e:
            return f"⚠️ Anthropic API Error: {e}"

    # ---------------------------------------------------------------
    # 7. Google Gemini (existing)
    # ---------------------------------------------------------------
    elif "gemini" in model_lower:
        if not os.environ.get("GOOGLE_API_KEY"):
            return "⚠️ Error: `GOOGLE_API_KEY` is missing in the environment."

        try:
            import google.generativeai as genai

            genai.configure(api_key=os.environ["GOOGLE_API_KEY"])
            safety_settings = [
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
            ]
            model = genai.GenerativeModel(model_name=llm_model, safety_settings=safety_settings)
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"⚠️ Google Gemini API Error: {e}"

    else:
        return f"⚠️ Unsupported model provider: {llm_model}"
