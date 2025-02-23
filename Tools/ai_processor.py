import os
from typing import Dict, Optional
from PyQt6.QtCore import QObject, pyqtSignal
import openai
import anthropic
from pathlib import Path
import json
import requests
from dotenv import load_dotenv

class AIProcessor(QObject):
    """Handles AI model interactions and processing"""
    
    # Signals for async processing
    processing_started = pyqtSignal()
    processing_finished = pyqtSignal(str)
    processing_error = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.load_configuration()
        
    def load_configuration(self):
        """Load API keys and configuration"""
        load_dotenv()
        
        # Load API keys from environment
        self.openai_key = os.getenv('OPENAI_API_KEY')
        self.anthropic_key = os.getenv('ANTHROPIC_API_KEY')
        self.ollama_url = os.getenv('OLLAMA_URL', 'http://localhost:11434')
        
        # Initialize clients
        if self.openai_key:
            self.openai_client = openai.OpenAI(api_key=self.openai_key)
        if self.anthropic_key:
            self.anthropic_client = anthropic.Client(api_key=self.anthropic_key)
    
    def process_request(self, model: str, context: Dict, query: str) -> str:
        """Process an AI request with the specified model"""
        try:
            self.processing_started.emit()
            
            # Prepare system message based on context
            system_message = self.prepare_system_message(context)
            
            # Process with appropriate model
            if 'gpt' in model.lower():
                response = self._process_openai(system_message, query)
            elif 'claude' in model.lower():
                response = self._process_anthropic(system_message, query)
            else:
                response = self._process_ollama(system_message, query)
            
            self.processing_finished.emit(response)
            return response
            
        except Exception as e:
            error_msg = f"AI processing error: {str(e)}"
            self.processing_error.emit(error_msg)
            raise RuntimeError(error_msg)
    
    def prepare_system_message(self, context: Dict) -> str:
        """Prepare system message based on context"""
        messages = [
            "You are an expert in Flash SWF analysis and ActionScript. ",
            "Help analyze and modify SWF files safely and effectively."
        ]
        
        # Add context-specific information
        if context.get('file'):
            messages.append(f"Currently working with file: {context['file']}")
        
        if context.get('analysis'):
            messages.append("Analysis results available:")
            messages.append(json.dumps(context['analysis'], indent=2))
        
        if context.get('task'):
            messages.append(f"Current task: {context['task']}")
        
        return "\n".join(messages)
    
    def _process_openai(self, system_message: str, query: str) -> str:
        """Process request with OpenAI models"""
        if not self.openai_key:
            raise RuntimeError("OpenAI API key not configured")
            
        response = self.openai_client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": query}
            ],
            temperature=0.7,
            max_tokens=1000
        )
        
        return response.choices[0].message.content
    
    def _process_anthropic(self, system_message: str, query: str) -> str:
        """Process request with Anthropic models"""
        if not self.anthropic_key:
            raise RuntimeError("Anthropic API key not configured")
            
        response = self.anthropic_client.messages.create(
            model="claude-3-sonnet-20240229",
            max_tokens=1000,
            messages=[{
                "role": "user",
                "content": f"{system_message}\n\nUser Query: {query}"
            }]
        )
        
        return response.content
    
    def _process_ollama(self, system_message: str, query: str) -> str:
        """Process request with local Ollama models"""
        try:
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": "codellama",
                    "prompt": f"{system_message}\n\nUser Query: {query}",
                    "stream": False
                }
            )
            response.raise_for_status()
            return response.json()['response']
            
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Ollama API error: {str(e)}")
    
    def validate_response(self, response: str, context: Dict) -> bool:
        """Validate AI response for safety and relevance"""
        # Implement validation logic based on context
        if 'modify' in context.get('task', '').lower():
            # Extra validation for modification suggestions
            unsafe_keywords = ['delete', 'remove', 'format', 'overwrite']
            return not any(keyword in response.lower() for keyword in unsafe_keywords)
        return True
