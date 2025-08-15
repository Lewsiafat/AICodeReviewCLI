import os
import google.generativeai as genai

def get_code_review(diff: str, prompt: str, model_name: str) -> str:
    """
    Gets a code review from the Gemini API using a specified model.
    Assumes API key is already configured.
    """
    try:
        # ANSI escape codes for colors
        CYAN = '\033[96m'
        RESET = '\033[0m'
        print(f"Using model: {CYAN}{model_name}{RESET}")
        
        model = genai.GenerativeModel(model_name)
        
        full_prompt = f"{prompt}\n\n--- CODE DIFF ---\n{diff}"
        
        print("\n--- Sending to Gemini API for review ---")
        response = model.generate_content(full_prompt)
        print("--- Review received from Gemini API ---\n")
        
        return response.text
    except Exception as e:
        return f"Error calling Gemini API: {e}"
