#!/usr/bin/env python3
"""
DeepSeek Orchestrator - Model Interface
Abstracts different inference engines (DeepSeek, Llama, Qwen, Mock)
"""

import json
import logging
from abc import ABC, abstractmethod

logger = logging.getLogger("model-interface")

class BaseModel(ABC):
    @abstractmethod
    def generate_suggestion(self, command: str) -> str:
        pass

class MockModel(BaseModel):
    def generate_suggestion(self, command: str) -> str:
        logger.info("Using Mock Model for suggestion")
        return f"# Suggested command for: {command}\necho 'Processing: {command}'"

class DeepSeekModel(BaseModel):
    def __init__(self, model_path, context_size=2048, temperature=0.7):
        self.model_path = model_path
        self.context_size = context_size
        self.temperature = temperature
        self.llm = None
        self._load_model()

    def _load_model(self):
        try:
            from llama_cpp import Llama
            logger.info(f"Loading DeepSeek model from {self.model_path}")
            self.llm = Llama(
                model_path=self.model_path,
                n_ctx=self.context_size,
                verbose=False
            )
        except Exception as e:
            logger.error(f"Failed to load DeepSeek model: {e}")
            self.llm = None

    def generate_suggestion(self, command: str) -> str:
        if not self.llm:
            return MockModel().generate_suggestion(command)
            
        prompt = f"### Instruction: Suggest a Linux command for: {command}\n### Response:"
        output = self.llm(prompt, max_tokens=128, temperature=self.temperature)
        return output['choices'][0]['text'].strip()

class LlamaModel(DeepSeekModel):
    """Specific tweaks for Llama-based models if needed"""
    pass

class QwenModel(DeepSeekModel):
    """Specific tweaks for Qwen-based models if needed"""
    pass

def get_model(config):
    model_config = config.get('model', {})
    model_type = model_config.get('type', 'mock').lower()
    model_path = model_config.get('path')

    if model_type == 'deepseek' and model_path:
        return DeepSeekModel(model_path)
    elif model_type == 'llama' and model_path:
        return LlamaModel(model_path)
    elif model_type == 'qwen' and model_path:
        return QwenModel(model_path)
    else:
        return MockModel()
