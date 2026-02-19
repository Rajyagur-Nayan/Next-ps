
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from backend.config import Config
import os

class FixGeneratorAgent:
    def __init__(self):
        if not Config.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY not found")
            
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-pro-latest",
            google_api_key=Config.GEMINI_API_KEY,
            temperature=0.2
        )

    def generate_fix(self, file_content: str, error_analysis: dict, language: str = "Unknown") -> str:
        """
        Generates a code fix using LLM with language context.
        """
        prompt_template = PromptTemplate(
            input_variables=["code", "error", "language"],
            template="""
            You are an expert Autonomous Coding Agent specializing in {language}.
            
            Analyze the following code and the detected error.
            Generate a minimal, correct fix.
            
            Context:
            - Language: {language}
            - Error Type: {error[type]}
            - Location: Line {error[line]}
            - Message: {error[message]}
            
            CODE CONTENT:
            ```
            {code}
            ```
            
            INSTRUCTIONS:
            1. Fix ONLY the reported error.
            2. Do not add comments or explanations.
            3. Return the COMPLETE file content with the fix applied.
            4. Ensure the syntax is correct for {language}.
            
            OUTPUT (Raw Code Only):
            """
        )
        
        chain = prompt_template | self.llm
        
        try:
            response = chain.invoke({
                "code": file_content,
                "error": error_analysis,
                "language": language
            })
            
            clean_code = response.content.replace("```python", "").replace("```javascript", "").replace("```java", "").replace("```go", "").replace("```", "").strip()
            return clean_code
            
        except Exception as e:
            print(f"Fix Gen Error: {e}")
            return file_content

    def apply_fix_to_repo(self, repo_path: str, file_rel_path: str, new_content: str):
        full_path = os.path.join(repo_path, file_rel_path)
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
