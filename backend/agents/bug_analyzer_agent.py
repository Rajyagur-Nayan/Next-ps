from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from backend.config import Config
import json

class BugAnalyzerAgent:
    def __init__(self):
        if not Config.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY not found")
        self.llm = ChatGoogleGenerativeAI(model="gemini-pro", google_api_key=Config.GEMINI_API_KEY)
        
    def analyze_logs(self, logs: str) -> dict:
        """
        Analyzes logs to find the first error.
        Returns:
            {
                "file": "path/to/file.py",
                "line": 10,
                "type": "LINTING | SYNTAX | LOGIC | TYPE_ERROR | IMPORT | INDENTATION",
                "description": "..."
            }
        """
        prompt = PromptTemplate.from_template(
            """
            You are an expert debugger. unexpected token? invalid syntax? module not found?
            Analyze the following test logs and identify the FIRST failure location.
            
            Logs:
            {logs}
            
            Task:
            Return a valid JSON object (NO MARKDOWN) with:
            - "file": The file path where the error occurred (e.g., src/utils.py)
            - "line": The line number (integer)
            - "type": One of [LINTING, SYNTAX, LOGIC, TYPE_ERROR, IMPORT, INDENTATION]
            - "description": A brief explanation of the bug.
            
            If no specific file is found, assume the main test file or best guess.
            """
        )
        
        chain = prompt | self.llm
        try:
            # Truncate logs if too long
            truncated_logs = logs[-5000:] if len(logs) > 5000 else logs
            
            response = chain.invoke({"logs": truncated_logs})
            content = response.content.strip()
            
            if content.startswith("```json"):
                content = content[7:-3]
            elif content.startswith("```"):
                content = content[3:-3]
                
            return json.loads(content)
        except Exception as e:
            # Fallback
            return {"file": "unknown", "line": 0, "type": "LOGIC", "description": f"Analysis failed: {str(e)}"}
