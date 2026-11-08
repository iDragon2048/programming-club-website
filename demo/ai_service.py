import os
from google import genai
from django.conf import settings

def get_gemini_code_answer(question: str, code_snippet: str = "", file_name: str = "") -> str:
    """
    Sends the user's question and optional code context to Gemini.
    """
    # Initialize the client with the API key from settings
    client = genai.Client(api_key=settings.GEMINI_API_KEY)

    # Construct the prompt
    prompt = f"User Question: {question}\n\n"

    if file_name:
        prompt += f"Selected File Context ({file_name}):\n"
    if code_snippet:
        prompt += f"Code:\n```\n{code_snippet}\n```\n"

    try:
        response = client.models.generate_content(
            model='gemini-3.6-flash',
            contents=prompt,
            config={
                'system_instruction': (
                    'You are an expert Python and software engineering AI tutor for a Python Club. '
                    'Provide concise, accurate code explanations, debugging tips, and solutions. '
                    'Always format your code blocks clearly.'
                )
            }
        )
        return response.text
    except Exception as e:
        return f"Error communicating with AI: {str(e)}"