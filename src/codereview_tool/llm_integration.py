import google.generativeai as genai
import openai
from abc import ABC, abstractmethod
from rich import print

class LLMProvider(ABC):
    """Abstract base class for all LLM providers."""
    def __init__(self, api_key):
        self.api_key = api_key
        self.configure()

    @abstractmethod
    def configure(self):
        """Configure the provider with the API key."""
        pass

    @abstractmethod
    def get_models(self):
        """Get a list of available models for the provider."""
        pass

    @abstractmethod
    def generate_review(self, diff_content, prompt, model_name, debug_mode=False):
        """Generate a code review for the given diff content."""
        pass

class GeminiProvider(LLMProvider):
    """LLM Provider for Google Gemini."""
    def configure(self):
        try:
            genai.configure(api_key=self.api_key)
        except Exception as e:
            # The CLI will handle printing this, but we raise it to be caught
            raise ConnectionError(f"Failed to configure Gemini API: {e}") from e

    def get_models(self):
        try:
            all_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
            pro_models = sorted([m for m in all_models if 'pro' in m])
            flash_models = sorted([m for m in all_models if 'flash' in m])
            other_models = sorted([m for m in all_models if 'pro' not in m and 'flash' not in m])
            return pro_models + flash_models + other_models
        except Exception as e:
            print(f"[bold red]Could not fetch Gemini model list: {e}[/bold red]")
            return []

    def generate_review(self, diff_content, prompt, model_name, debug_mode=False):
        full_prompt = f"{prompt}\n\n---\n\n**Code Diff to Review:**\n\n```diff\n{diff_content}\n```"
        if debug_mode:
            print("--- DEBUG: Prompt for AI ---")
            print(full_prompt)
            print("--- END DEBUG ---")
            return "(Debug mode: AI call skipped)"
        
        try:
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(full_prompt)
            if not response.parts:
                return "(AI returned an empty response, possibly due to safety filters or other issues.)"
            return response.text
        except Exception as e:
            return f"(Error during API call: {e})"

class OpenAIProvider(LLMProvider):
    """LLM Provider for OpenAI."""
    def configure(self):
        try:
            self.client = openai.OpenAI(api_key=self.api_key)
        except Exception as e:
            raise ConnectionError(f"Failed to configure OpenAI API: {e}") from e

    def get_models(self):
        try:
            return sorted([model.id for model in self.client.models.list() if "gpt" in model.id])
        except Exception as e:
            print(f"[bold red]Could not fetch OpenAI model list: {e}[/bold red]")
            return []

    def generate_review(self, diff_content, prompt, model_name, debug_mode=False):
        full_prompt = f"{prompt}\n\n---\n\n**Code Diff to Review:**\n\n```diff\n{diff_content}\n```"
        if debug_mode:
            print("--- DEBUG: Prompt for AI ---")
            print(full_prompt)
            print("--- END DEBUG ---")
            return "(Debug mode: AI call skipped)"

        try:
            response = self.client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": f"Please review the following code diff:\n```diff\n{diff_content}\n```"}
                ]
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"(Error during API call: {e})"



SUPPORTED_PROVIDERS = {
    "Google": GeminiProvider,
    "OpenAI": OpenAIProvider,
}

def get_provider_from_name(provider_name, api_key):
    """Factory function to get a provider instance from its name."""
    provider_class = SUPPORTED_PROVIDERS.get(provider_name)
    if not provider_class:
        raise ValueError(f"Unsupported provider: {provider_name}")
    return provider_class(api_key)