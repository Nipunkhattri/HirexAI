from llama_index.llms.openai import OpenAI
import json
import os

class DomainExtractor:
    def __init__(self):
        self.llm = OpenAI(model="gpt-4o", api_key=os.getenv("OPENAI_API_KEY"))
    
    def extract_domains(self, resume_text):
        prompt = f"""
        You are an expert in resume parsing for technical interviews.

        Given a resume text, extract and classify the user’s skills into high-level, interview-relevant technical domains only — these should be the domains you'd conduct an in-depth technical interview on.

        The resume text is as follows:
        {resume_text}

        Guidelines:
        - Do NOT include support categories such as "Version Control", "Tools", "API Development", or "Technologies".
        - DO include only meaningful technical domains such as:
        - Backend Development
        - Frontend Development
        - AI/ML or Generative AI
        - Android Development
        - Cloud Computing
        - DevOps
        - Cybersecurity
        - Data Engineering
        - Web Development
        - Embedded Systems
        - etc.

        These domains should reflect actual areas you'd prepare interview questions for.

        Each domain must include an array of unique, contextually relevant skills extracted from the resume. A skill should only appear under the domain it contributes most strongly to.

        Format:
        {{
        "domain1": {{
            "skills": ["skill1", "skill2", "skill3"]
        }},
        "domain2": {{
            "skills": ["skill1", "skill2", "skill3"]
        }}
        }}

        Output only the JSON. Do not include vague or overly granular domains like "Version Control", "Tools", or "API Development".
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