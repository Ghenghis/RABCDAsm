import os
from pathlib import Path
from typing import Dict, List, Optional
import json
import requests
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class ModelManager:
    """Manages AI model configurations and directories"""
    
    def __init__(self):
        self.lmstudio_dir = Path(os.path.expanduser("~/.lmstudio/models"))
        self.ollama_dir = Path(os.path.expanduser("~/.ollama/models"))
        self.openrouter_key = os.getenv("OPENROUTER_API_KEY", "")
        self.openrouter_models = []
        self.lmstudio_models = []
        self.ollama_models = []
        
        # Set up file watchers
        self.setup_watchers()
        
        # Initial model scan
        self.refresh_models()
    
    def setup_watchers(self):
        """Set up directory watchers for model changes"""
        self.observer = Observer()
        
        # Watch LM Studio directory
        if self.lmstudio_dir.exists():
            self.observer.schedule(
                ModelWatcher(self.refresh_models),
                str(self.lmstudio_dir),
                recursive=False
            )
        
        # Watch Ollama directory
        if self.ollama_dir.exists():
            self.observer.schedule(
                ModelWatcher(self.refresh_models),
                str(self.ollama_dir),
                recursive=False
            )
        
        self.observer.start()
    
    def refresh_models(self):
        """Refresh the list of available models"""
        self.lmstudio_models = self._scan_lmstudio_models()
        self.ollama_models = self._scan_ollama_models()
        self.openrouter_models = self._fetch_openrouter_models()
    
    def _scan_lmstudio_models(self) -> List[Dict]:
        """Scan LM Studio models directory"""
        models = []
        if self.lmstudio_dir.exists():
            for model_file in self.lmstudio_dir.glob("*.gguf"):
                models.append({
                    'name': model_file.stem,
                    'path': str(model_file),
                    'type': 'lmstudio',
                    'size': model_file.stat().st_size
                })
        return models
    
    def _scan_ollama_models(self) -> List[Dict]:
        """Scan Ollama models directory"""
        models = []
        if self.ollama_dir.exists():
            for model_dir in self.ollama_dir.iterdir():
                if model_dir.is_dir():
                    manifest = model_dir / "manifest.json"
                    if manifest.exists():
                        try:
                            with open(manifest) as f:
                                data = json.load(f)
                                models.append({
                                    'name': data.get('name', model_dir.name),
                                    'path': str(model_dir),
                                    'type': 'ollama',
                                    'config': data
                                })
                        except json.JSONDecodeError:
                            continue
        return models
    
    def _fetch_openrouter_models(self) -> List[Dict]:
        """Fetch available models from OpenRouter API"""
        if not self.openrouter_key:
            return []
            
        try:
            response = requests.get(
                "https://openrouter.ai/api/v1/models",
                headers={"Authorization": f"Bearer {self.openrouter_key}"}
            )
            response.raise_for_status()
            return response.json()
        except Exception:
            return []
    
    def get_all_models(self) -> Dict[str, List[Dict]]:
        """Get all available models grouped by provider"""
        return {
            'lmstudio': self.lmstudio_models,
            'ollama': self.ollama_models,
            'openrouter': self.openrouter_models
        }
    
    def get_model_info(self, model_name: str, provider: str) -> Optional[Dict]:
        """Get detailed information about a specific model"""
        models_map = {
            'lmstudio': self.lmstudio_models,
            'ollama': self.ollama_models,
            'openrouter': self.openrouter_models
        }
        
        if provider in models_map:
            for model in models_map[provider]:
                if model['name'] == model_name:
                    return model
        return None

class ModelWatcher(FileSystemEventHandler):
    """Watches for changes in model directories"""
    
    def __init__(self, callback):
        self.callback = callback
        
    def on_created(self, event):
        if not event.is_directory:
            self.callback()
            
    def on_deleted(self, event):
        if not event.is_directory:
            self.callback()
            
    def on_modified(self, event):
        if not event.is_directory:
            self.callback()
