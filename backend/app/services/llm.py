"""
LLM service using Qwen model for text generation
"""

from multiprocessing import context
import re
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)


class LLMService:
    """Service for generating responses using Qwen LLM"""

    def __init__(self):
        self.model = None
        self.tokenizer = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"

    def load_model(self):
        """Load the LLM model and tokenizer"""
        logger.info(f"Loading LLM model: {settings.LLM_MODEL}")

        self.tokenizer = AutoTokenizer.from_pretrained(settings.LLM_MODEL)
        self.model = AutoModelForCausalLM.from_pretrained(
            settings.LLM_MODEL,
            torch_dtype=torch.float32,
            device_map="auto" if self.device == "cuda" else None,
        )

        if self.device == "cpu":
            self.model.to(self.device)

        logger.info(f"LLM model loaded on {self.device}")

    def generate_response(
        self,
        query: str,
        context: str,
        conversation_history: str = None,  # NEW parameter
    ) -> str:
        """
        Generate response using LLM with context (RAG) and conversation history

        Args:
            query: User's question
            context: Retrieved context from vector database
            conversation_history: Optional previous conversation context

        Returns:
            Generated answer
        """
        if self.model is None or self.tokenizer is None:
            raise RuntimeError("Model not loaded. Call load_model() first.")

        # Build prompt with conversation history if available
        if conversation_history:
            prompt = f"""You are a helpful assistant. Use the provided context to answer questions, and remember the conversation history.

{conversation_history}

Context from documents:
{context}

Current question: {query}

Format your response in clean Markdown. Use:
- **Bold** for important terms
- Bullet points for lists
- ## Headers for sections
- `code` for technical terms
- Keep responses clear and well-structured

Answer:"""
        else:
            prompt = f"""Based on the following context, please answer the question.

Context:
{context}

Question: {query}

Format your response in clean Markdown. Use:
- **Bold** for important terms  
- Bullet points for lists
- ## Headers for sections
- `code` for technical terms
- Keep responses clear and well-structured

Answer:"""

        # Create chat messages
        messages = [
            {
                "role": "system",
                "content": "You are a helpful assistant that answers questions based on the provided context and conversation history.",
            },
            {"role": "user", "content": prompt},
        ]

        # Apply chat template
        text = self.tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )

        # Tokenize
        inputs = self.tokenizer([text], return_tensors="pt").to(self.model.device)

        # Generate
        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=settings.MAX_NEW_TOKENS,
                temperature=settings.TEMPERATURE,
                top_p=settings.TOP_P,
                do_sample=True,
            )

        # Decode response (skip the prompt)
        response = self.tokenizer.decode(
            outputs[0][inputs["input_ids"].shape[1] :], skip_special_tokens=True
        )

        return response.strip()

    def is_loaded(self) -> bool:
        """Check if model is loaded"""
        return self.model is not None and self.tokenizer is not None


# Global instance
llm_service = LLMService()
