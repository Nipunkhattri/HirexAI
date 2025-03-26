from llama_index.llms.openai import OpenAI
import json
import os

class DomainExtractor:
    def __init__(self):
        self.llm = OpenAI(model="gpt-4o", api_key=os.getenv("OPENAI_API_KEY"))
    
    def extract_domains(self, resume_text):
        prompt = f"""
            You are a expert in getting the domains from the user resume.
            Resume Text : {resume_text}
            You have to classify the domains in which the user are having skills.
            And you have to return a json response of that.
            Here is a example how it will look like             
            {{
                "domain1": {{
                    "skills": ["skill1", "skill2", "skill3"]
                }},
                "domain2": {{
                    "skills": ["skill1", "skill2", "skill3"]
                }},
                "domain3": {{
                    "skills": ["skill1", "skill2", "skill3"]
                }}
            }}
            The Output should be in JSON format.
            All the domains and inside there skills should be different.
            Skills must be returned as an array of strings, not as a comma-separated string.
            I want only the json reponse nothing else.
        """
        response = self.llm.complete(prompt).text.strip()
        print(response)
        try:
            response_dict = json.loads(response)
            return response_dict
        except json.JSONDecodeError:
            # Clean the response to ensure it's valid JSON
            cleaned_response = response.replace('\n', '').replace('```json', '').replace('```', '')
            try:
                response_dict = json.loads(cleaned_response)
                return response_dict
            except json.JSONDecodeError:
                raise ValueError("Invalid JSON response from LLM")