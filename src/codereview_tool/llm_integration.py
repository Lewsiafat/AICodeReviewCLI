import google.generativeai as genai
import openai
import anthropic
from abc import ABC, abstractmethod
from rich import print

# --- Constants ---
SUPPORTED_PROVIDER_NAMES = ["Google", "OpenAI", "Anthropic (Claude)", "Grok"]
GROK_API_BASE_URL = "https://api.x.ai/v1"

# --- Base Class ---
class LLMProvider(ABC):
    """Abstract base class for all LLM providers."""
    def __init__(self, api_key):
        if not api_key:
            raise ValueError(f"API key for {self.__class__.__name__} is required.")
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

# --- Provider Implementations ---
class GeminiProvider(LLMProvider):
    def configure(self):
        try:
            genai.configure(api_key=self.api_key)
        except Exception as e:
            raise ConnectionError(f"Failed to configure Gemini API: {e}") from e

    def get_models(self):
        try:
            all_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
            return sorted([m.replace("models/", "") for m in all_models])
        except Exception as e:
            print(f"[bold red]Could not fetch Gemini model list: {e}[/bold red]")
            return []

    def generate_review(self, diff_content, prompt, model_name, debug_mode=False):
        full_prompt = f"{prompt}\n\n---\n\n**Code Diff to Review:**\n\n```diff\n{diff_content}\n```"
        if debug_mode:
            print("--- DEBUG: Prompt for AI ---", full_prompt, "--- END DEBUG ---", sep="\n")
            return "(Debug mode: AI call skipped)"
        try:
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(full_prompt)
            return response.text
        except Exception as e:
            return f"(Error during API call: {e})"

class OpenAIProvider(LLMProvider):
    def __init__(self, api_key, base_url=None):
        self.base_url = base_url
        super().__init__(api_key)

    def configure(self):
        self.client = openai.OpenAI(api_key=self.api_key, base_url=self.base_url)

    def get_models(self):
        try:
            model_list = self.client.models.list()
            # The model_list object is an iterable SyncPage
            return sorted([model.id for model in model_list])
        except Exception as e:
            print(f"[bold red]Could not fetch OpenAI/Grok model list: {e}[/bold red]")
            return []

    def generate_review(self, diff_content, prompt, model_name, debug_mode=False):
        if debug_mode:
            # ... (debug print logic) ...
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

class ClaudeProvider(LLMProvider):
    def configure(self):
        self.client = anthropic.Anthropic(api_key=self.api_key)

    def get_models(self):
        return sorted(["claude-3-opus-20240229", "claude-3-sonnet-20240229", "claude-3-haiku-20240307"])

    def generate_review(self, diff_content, prompt, model_name, debug_mode=False):
        if debug_mode:
            # ... (debug print logic) ...
            return "(Debug mode: AI call skipped)"
        try:
            response = self.client.messages.create(
                model=model_name,
                max_tokens=4096,
                system=prompt,
                messages=[{"role": "user", "content": f"Please review the following code diff:\n```diff\n{diff_content}\n```"}]
            )
            return response.content[0].text
        except Exception as e:
            return f"(Error during API call: {e})"

# --- Factory Function ---
def get_provider_from_name(provider_name, api_key):
    """Factory function to get a provider instance from its name."""
    if provider_name == "Google":
        return GeminiProvider(api_key)
    elif provider_name == "OpenAI":
        return OpenAIProvider(api_key)
    elif provider_name == "Anthropic (Claude)":
        return ClaudeProvider(api_key)
    elif provider_name == "Grok":
        return OpenAIProvider(api_key, base_url=GROK_API_BASE_URL)
    else:
        raise ValueError(f"Unsupported provider: {provider_name}")