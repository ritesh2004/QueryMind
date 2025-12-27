from ollama import chat
from ollama import ChatResponse
from PySide6.QtCore import QThread, Signal


class OllamaAgent(QThread):
    response_received = Signal(str, str)  # SQL query and response
    error_occurred = Signal(str)
    status_update = Signal(str)
    def __init__(self, query: str, model_name: str, db_schema: str, db_tables: list[str]):
        super().__init__()
        self.query = query
        self.model_name = model_name
        self.db_schema = db_schema
        self.db_tables = db_tables
        self._is_running = True
    
    def stop(self):
        self._is_running = False
        self.quit()
        self.wait()
    def run(self):
        try:
            self.status_update.emit("Generating SQL query...")
            
            system_prompt = f"""
            You are a SQL expert. Given the following database tables:
            {', '.join(self.db_tables)}.
            
            Database Schema:
            {self.db_schema}
            
            Instructions:
            1. Convert the user's natural language question into a valid SQL query.
            2. Only use tables and columns that exist in the schema.
            3. Return ONLY the SQL code in a single line.
            4. If the query is ambiguous, make reasonable assumptions and note them in comments.
            5. If the query cannot be answered with the given schema, explain why.
            
            Example:
            User: Show me all users who signed up last month
            Response: SELECT * FROM users WHERE signup_date >= DATE_TRUNC('month', CURRENT_DATE - INTERVAL '1 month') AND signup_date < DATE_TRUNC('month', CURRENT_DATE);
            """
            
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": self.query}
            ]
            
            # print("Input: ", messages)
            
            response = chat(
                model=self.model_name,
                messages=messages
            )
            
            # print("Response: ", response)
            # print("Type: ", type(response))
            
            if response and 'message' in response:
                self.response_received.emit("sql", self.extract_message_content(response))
                self.response_received.emit("complete", self.extract_message_content(response))
            else:
                self.error_occurred.emit("No response from model")
            
            
        except Exception as e:
            self.error_occurred.emit(f"Error generating SQL: {str(e)}")
        finally:
            self.status_update.emit("Ready")
            
    def extract_message_content(self, response):
        if hasattr(response, "message"):
            return response.message.content
        if isinstance(response, dict):
            return response.get("message", {}).get("content")
        return None