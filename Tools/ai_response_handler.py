import os
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI
from anthropic import Anthropic
import json

# Load environment variables
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

class AIResponseHandler:
    def __init__(self):
        self.openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.anthropic_client = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
        self.current_model = "gpt-4"  # Default model
        
        # Load conversation history from file if it exists
        self.history_file = Path(__file__).parent / 'conversation_history.json'
        self.conversation_history = self.load_history()
    
    def load_history(self):
        """Load conversation history from file"""
        if self.history_file.exists():
            try:
                with open(self.history_file, 'r') as f:
                    return json.load(f)
            except:
                return []
        return []
    
    def save_history(self):
        """Save conversation history to file"""
        with open(self.history_file, 'w') as f:
            json.dump(self.conversation_history, f)
    
    def add_to_history(self, role, content):
        """Add a message to conversation history"""
        self.conversation_history.append({
            "role": role,
            "content": content
        })
        # Keep only last 10 messages to avoid token limits
        if len(self.conversation_history) > 10:
            self.conversation_history = self.conversation_history[-10:]
        self.save_history()
    
    def get_ai_response(self, user_input, model=None):
        """Get AI response using specified model"""
        try:
            if model:
                self.current_model = model
                
            # Add user input to history
            self.add_to_history("user", user_input)
            
            if "gpt" in self.current_model:
                response = self.openai_client.chat.completions.create(
                    model=self.current_model,
                    messages=[
                        {"role": "system", "content": "You are a helpful assistant for the RABCDAsm project, "
                         "focusing on Flash/ActionScript analysis and decompilation."},
                        *[{"role": msg["role"], "content": msg["content"]} 
                          for msg in self.conversation_history]
                    ],
                    temperature=0.7,
                    max_tokens=150
                )
                ai_response = response.choices[0].message.content
                
            elif "claude" in self.current_model:
                messages = [
                    {
                        "role": "assistant" if msg["role"] == "assistant" else "user",
                        "content": msg["content"]
                    }
                    for msg in self.conversation_history
                ]
                response = self.anthropic_client.messages.create(
                    model=self.current_model,
                    max_tokens=150,
                    temperature=0.7,
                    messages=messages,
                    system="You are a helpful assistant for the RABCDAsm project, "
                           "focusing on Flash/ActionScript analysis and decompilation."
                )
                ai_response = response.content[0].text
            
            # Add AI response to history
            self.add_to_history("assistant", ai_response)
            return ai_response
            
        except Exception as e:
            error_msg = f"Error getting AI response: {str(e)}"
            print(error_msg)
            return error_msg
    
    def set_model(self, model_name):
        """Set the AI model to use"""
        valid_models = {
            "gpt-4", "gpt-3.5-turbo",
            "claude-3-opus-20240229", "claude-3-sonnet-20240229"
        }
        if model_name in valid_models:
            self.current_model = model_name
            return True
        return False
    
    def clear_history(self):
        """Clear conversation history"""
        self.conversation_history = []
        if self.history_file.exists():
            self.history_file.unlink()
