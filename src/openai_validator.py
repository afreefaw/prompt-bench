import json
import aiohttp
from pathlib import Path
from typing import Dict, Optional
from datetime import datetime

class OpenAIValidator:
    def __init__(self):
        self.config = self._load_config()
        self.api_key = self.config["api_key"]
        self.model = self.config["model"]
        self.session = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            headers={"Authorization": f"Bearer {self.api_key}"}
        )
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    def _load_config(self) -> Dict:
        """Load OpenAI configuration from local config file"""
        config_path = Path("config/openai_config.local.json")
        if not config_path.exists():
            raise FileNotFoundError(
                "OpenAI config not found. Please create config/openai_config.local.json "
                "with your API key based on config/openai_config.json template."
            )
        
        with open(config_path) as f:
            config = json.load(f)
        
        if not config["api_key"]:
            raise ValueError(
                "OpenAI API key not set. Please add your API key to "
                "config/openai_config.local.json"
            )
        
        return config
    
    @classmethod
    async def validate_batch(
        cls,
        test_run: Dict,
        count: int,
        progress_callback: Optional[callable] = None
    ) -> Dict:
        """
        Validate a batch of responses using OpenAI.
        
        Args:
            test_run: The test run containing results to validate
            count: Number of examples to validate
            progress_callback: Optional callback(validated_count, total_count)
        
        Returns:
            Dict containing validation statistics
        """
        if "promptText" not in test_run:
            raise ValueError("promptText not found in test run data")
            
        # Get results without OpenAI validation
        unvalidated = [
            result for result in test_run["results"]
            if "validations" not in result or "openai" not in result["validations"]
        ]
        
        # Limit to requested count
        to_validate = unvalidated[:count]
        total = len(to_validate)
        
        import asyncio
        
        completed = 0
        
        async def process_single_validation(validator, result):
            nonlocal completed
            validation = await validator.validate_response(
                context=result["context"],
                prompt=test_run["promptText"],
                response=result["modelResponse"]
            )
            
            # Update result with validation
            if "validations" not in result:
                result["validations"] = {}
            
            result["validations"]["openai"] = {
                "status": validation["status"],
                "reason": validation["reason"],
                "model": validation["model"],
                "response": validation.get("response", ""),
                "timestamp": datetime.now().isoformat()
            }
            
            completed += 1
            if progress_callback:
                progress_callback(completed, total)
                
            return validation["status"]
        
        # Create validator instance and use as context manager
        validator = cls()
        async with validator:
            # Run validations concurrently
            validation_tasks = [
                process_single_validation(validator, result)
                for result in to_validate
            ]
            validation_results = await asyncio.gather(*validation_tasks)
            
            # Calculate statistics
            validated = len(validation_results)
            success = sum(1 for status in validation_results if status)
            failed = validated - success
            
            return {
                "total": total,
                "validated": validated,
                "success": success,
                "failed": failed,
                "success_rate": (success / validated * 100) if validated > 0 else 0
            }

    async def validate_response(
        self,
        context: str,
        prompt: str,
        response: str,
        validation_prompt: Optional[str] = None
    ) -> Dict:
        """
        Validate a model response using OpenAI.
        
        Args:
            context: The context provided to the model
            prompt: The prompt given to the model
            response: The model's response to validate
            validation_prompt: Optional custom validation prompt
        
        Returns:
            Dict containing validation result with fields:
            - status: bool indicating if response is valid
            - reason: Explanation of validation result
            - type: "openai"
            - model: Name of OpenAI model used
        """
        if validation_prompt is None:
            validation_prompt = (
                "You are a validation assistant. Your task is to validate if the model's "
                "response is the correct output.\n\n"
                "Evaluate whether the model's response is correct. You do not need to worry "
                "about punctuation or capitalization, however otherwise the answer must be "
                "in the requested format.\n"
                "Respond with a JSON object containing:\n"
                "- reason: brief explanation of your assessment\n"
                "- valid: boolean indicating if the response is valid\n"
                "- format_fail: boolean indicating if there was a formatting issue\n"
                "Example:\n"
                "{\n"
                "  \"reason\": \"The response is correct because the addresses shown are "
                "likely a match, since the non-matching elements are unimportant, and the "
                "response given was Yes,\",\n"
                "  \"valid\": true,\n"
                "  \"format_fail\": false\n"
                "}\n"
            )
        
        messages = [
            {"role": "system", "content": validation_prompt},
            {"role": "user", "content": f"Prompt:\n{prompt}\n{context}\n\n\nResponse to validate:\n{response}"}
        ]
        
        if not self.session:
            raise RuntimeError("Validator must be used as async context manager")
            
        try:
            async with self.session.post(
                "https://api.openai.com/v1/chat/completions",
                json={
                    "model": self.model,
                    "messages": messages
                }
            ) as response:
                response.raise_for_status()
                completion = await response.json()
                result = json.loads(completion["choices"][0]["message"]["content"])
                
                return {
                    "type": "openai",
                    "model": self.model,
                    "status": result["valid"],
                    "reason": result["reason"],
                    "response": completion["choices"][0]["message"]["content"]
                }
                
        except Exception as e:
            return {
                "type": "openai",
                "model": self.model,
                "status": False,
                "reason": f"Validation failed: {str(e)}"
            }