from fastapi import APIRouter, status, UploadFile,Depends, File, HTTPException,Form
from fastapi.responses import JSONResponse
from services.file_processor import FileProcessor
from services.domain_extractor import DomainExtractor
from models.domain import DomainsResponse , QuestionsResponse , SkillsRequest
from openai import OpenAI
from config.setting import settings
from deepgram import Deepgram
import os
from database.mongodb import users_collection , resume_collection , user_responses
from middleware.middleware import verify_token
from bson import ObjectId
from models.domain import SubmitAnswer
import uuid
import datetime

resume_router = APIRouter(prefix="/api/v1/resume", tags=["Resume Domain Creation"])

@resume_router.post("/extract_domains", 
                   response_model=DomainsResponse,
                   status_code=status.HTTP_200_OK)
async def extract_domain(file: UploadFile = File(...),user_id: str = Depends(verify_token)):
    """
    Extract domains from uploaded resume file
    Accepts PDF and DOCX formats
    """
    try:
        if not file.filename.lower().endswith('.pdf'):
            raise HTTPException(
                status_code=400,
                detail="Unsupported file format. Please upload PDF files only."
            )
        
        file_content = await file.read()
        file_processor = FileProcessor()
        domain_extractor = DomainExtractor()
        
        resume_text = await file_processor.extract_text_from_pdf(file_content)
        domains_dict = domain_extractor.extract_domains(resume_text)
        resume_id = str(uuid.uuid4())

        resume_collection.insert_one({
            "user_id": user_id,
            "resume_id": resume_id,
            "domains": domains_dict
        })
        
        return DomainsResponse(
            status="success",
            message="Domains extracted successfully",
            resume_id=str(resume_id),
            domains=domains_dict
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing resume: {str(e)}"
        )

@resume_router.post('/generate_questions',
                    response_model=QuestionsResponse,
                    status_code=status.HTTP_200_OK)
async def Generate_Questions(request: SkillsRequest,user_id: str = Depends(verify_token)):
    """
    This help us to generate the questions based on 
    the skills
    """
    try:
        skills_str = ", ".join(request.skills)
        client = OpenAI(api_key=settings.OPENAI_API_KEY)

        prompt = f"""Generate 2 technical interview questions for a candidate with the following skills: {skills_str}.
        The questions should:
        - Be specific to the mentioned skills
        - Include a mix of basic and advanced concepts
        - Focus on practical applications
        - Be clear and concise
        - The questions should be in theory or approach based not any code related to it.
        Please provide only the questions without answers."""

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a technical interviewer creating relevant questions based on specific skills."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=1000
        )

        raw_questions = response.choices[0].message.content.strip().split('\n')

        questions = [q.strip().lstrip('0123456789. ') for q in raw_questions if q.strip()]

        questions = questions[:2]

        # Use upsert instead of find_one and insert_one
        existing_doc = await user_responses.find_one({
            "user_id": user_id,
            "resume_id": request.resume_id
        })

        print("existing_doc",existing_doc)
        
        if existing_doc is None:
            # Insert new document if it doesn't exist
            await user_responses.insert_one({
            "user_id": user_id,
            "resume_id": request.resume_id,
            "responses": {}  # Initialize empty responses object
            })

        return QuestionsResponse(questions=questions,DomainName=request.DomainName)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing resume: {str(e)}"
        )
        
@resume_router.post('/record_answer',
                    status_code=status.HTTP_200_OK)
async def Record_Answer(
    audio: UploadFile = File(..., media_type="audio/*"),
    user_id: str = Depends(verify_token)
    ):
    """
    Get the audio and the question from frontend, convert audio to text using Deepgram
    """
    dg_client = Deepgram(settings.DEEPGRAM_API_KEY)
    audio_bytes = await audio.read()
    source = {"buffer": audio_bytes, "mimetype": audio.content_type}
    response = await dg_client.transcription.prerecorded(source, {"punctuate": True})
    transcript = response["results"]["channels"][0]["alternatives"][0]["transcript"]
    print(f"User ID: {user_id}") 
    print(f"Transcript: {transcript}")

    return JSONResponse({"success": "text saved successfully", "transcript": transcript})

@resume_router.post('/submit_answer',
                    status_code=status.HTTP_200_OK)
async def submit_answer(
    answer: SubmitAnswer,
    user_id: str = Depends(verify_token)
    ):
    """
    Record the answer (text) submitted for a question.
    """
    print(f"User ID: {user_id}")
    print(f"Domain: {answer.DomainName}")
    print(f"Question: {answer.question}")
    print(f"Answer: {answer.answer_text}")
    user_doc = await user_responses.find_one({
        "user_id": user_id,
        "resume_id": answer.resume_id
    })

    print(user_doc)
    
    if user_doc and "responses" in user_doc:
        # If responses object exists, update or add to domain array
        # Check if domain exists in responses
        domain_exists = await user_responses.find_one({
            "user_id": user_id,
            "resume_id": answer.resume_id,
            f"responses.{answer.DomainName}": {"$exists": True}
        })

        if domain_exists:
            # If domain exists, push to its array
            await user_responses.update_one(
            {
                "user_id": user_id,
                "resume_id": answer.resume_id
            },
            {"$push": {
                f"responses.{answer.DomainName}": {
                "question": answer.question,
                "transcript": answer.answer_text
                }
            }}
            )
        else:
            # If domain doesn't exist, set it with first answer
            await user_responses.update_one(
            {
                "user_id": user_id,
                "resume_id": answer.resume_id
            },
            {"$set": {
                f"responses.{answer.DomainName}": [{
                "question": answer.question,
                "transcript": answer.answer_text
                }]
            }}
            )
    else:
        # If responses object doesn't exist, create it with first domain and answer
        await user_responses.update_one(
            {
                "user_id": user_id,
                "resume_id": answer.resume_id
            },
            {"$set": {
                "responses": {
                    f"{answer.DomainName}": [{
                        "question": answer.question,
                        "transcript": answer.answer_text
                    }]
                }
            }}
        )
    return JSONResponse({"success": "Answer saved successfully"})

@resume_router.get('/analysis', status_code=status.HTTP_200_OK)
async def get_analysis(resume_id: str, domain_name: str, user_id: str = Depends(verify_token)):
    """
    Get the analysis of the user responses for a specific domain including scores and improved answers
    """
    try:
        user_doc = await user_responses.find_one({
            "user_id": user_id,
            "resume_id": resume_id
        })

        user = await users_collection.find_one({"_id": ObjectId(user_id)})

        if not user_doc or "responses" not in user_doc:
            raise HTTPException(status_code=404, detail="No responses found")
            
        responses = user_doc["responses"]
        
        if domain_name not in responses:
            raise HTTPException(status_code=404, detail=f"No responses found for domain: {domain_name}")
            
        client = OpenAI(api_key=settings.OPENAI_API_KEY)
        analysis_result = {}

        # Only get responses for the specified domain
        domain_responses = responses[domain_name]
        all_responses = []
        for qa in domain_responses:
            all_responses.append({"question": qa['question'], "transcript": qa["transcript"]})

        print(all_responses)

        overall_prompt = f"""
        You are an expert technical interviewer for the {domain_name} domain. Your task is to analyze and evaluate a series of technical interview responses provided by a candidate.

        You will receive a list of questions and the corresponding answers in JSON format:
        {all_responses}

        ### Evaluation Criteria:
        - **Relevance**: Does the answer directly address the question asked?
        - **Completeness**: Does it provide sufficient technical and contextual detail?
        - **Clarity**: Is the explanation clear and easy to understand?
        - **Accuracy**: Are the technical concepts and implementations described correctly?

        Based on the evaluation, provide a comprehensive assessment of the candidate’s performance. Your response should include:

        - **Overall Score**: An overall evaluation of the candidate’s performance.
        - **Technical Skills Score**: How well the candidate demonstrated technical expertise.
        - **Problem Solving Score**: How well the candidate approached and solved technical problems.
        - **Skill Breakdown**: A breakdown of specific skills demonstrated based on the questions (e.g., React, Node.js, Algorithms, SQL, etc.), each rated out of 100.

        ### Output Format:
        Return a valid JSON object in **this exact structure**:
        {{
            "Overall_Score": <integer from 0 to 100>,
            "Technical_Skills_Score": <integer from 0 to 100>,
            "Problem_Solving_Score": <integer from 0 to 100>,
            "skillBreakdown": [
                {{
                    "name": "<Skill Name>",
                    "value": <integer from 0 to 100>
                }},
                ...
            ]
        }}
        """

        overall_response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "system", "content": overall_prompt}],
            temperature=0.7
        )

        import json
        scores_dict = {}
        try:
            scores_dict = json.loads(overall_response.choices[0].message.content)
        except (json.JSONDecodeError, ValueError):
            scores_dict = {
                "Overall_Score": 0,
                "Technical_Skills_Score": 0,
                "Problem_Solving_Score": 0,
                "skillBreakdown": []
            }

        # Process only the specified domain
        domain_questions = []
        for qa in domain_responses:
            question = qa["question"]
            user_response = qa["transcript"]
            prompt = f"""
            You will get the question and answer which user submitted in the interview.
            You have to Analyze the user answer using the user response and provide an improved answer:
            Question: {question}
            User Response: {user_response}
            Provide a detailed, technically accurate improved answer that covers all important aspects and in short"""
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "system", "content": prompt}],
                temperature=0.7
            )
            improved_answer = response.choices[0].message.content.strip()
            domain_questions.append({
                "question": question,
                "userResponse": user_response,
                "improvedAnswer": improved_answer
            })
        analysis_result[domain_name] = domain_questions

        await user_responses.update_one(
            {
            "user_id": user_id,
            "resume_id": resume_id
            },
            {"$set": {
            f"analysis.{domain_name}": {
                "resume_id": resume_id,
                "name": user['name'] if user else "",
                "email": user['email'] if user else "",
                "overallScore": scores_dict.get("Overall_Score", 0),
                "technicalSkillsScore": scores_dict.get("Technical_Skills_Score", 0),
                "problemSolvingScore": scores_dict.get("Problem_Solving_Score", 0),
                "skillBreakdown": scores_dict.get("skillBreakdown", []),
                "domainAnalysis": analysis_result,
                "date": str(datetime.datetime.now()),
                "time": str(datetime.datetime.now().time())
            }
            }}
        )

        return JSONResponse({
            "success": True,
            "message": "Analysis completed successfully",
        })

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error analyzing responses: {str(e)}"
        )
    
@resume_router.get('/get_analysis', status_code=status.HTTP_200_OK)
async def get_domain_analysis(resume_id: str, domain_name: str, user_id: str = Depends(verify_token)):
    """
    Get the analysis for a specific domain from the user responses
    """
    try:
        # Find the user response document
        user_doc = await user_responses.find_one({
            "user_id": user_id,
            "resume_id": resume_id,
        })
        
        if not user_doc or "analysis" not in user_doc:
            raise HTTPException(status_code=404, detail="No analysis found")
            
        analysis = user_doc.get("analysis", {})
        
        if domain_name not in analysis:
            raise HTTPException(status_code=404, detail=f"No analysis found for domain: {domain_name}")
            
        # Return the analysis for the specified domain
        return JSONResponse({
            "success": True,
            "analysis": analysis[domain_name]
        })

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving analysis: {str(e)}"
        )


@resume_router.get("/InterviewHistory",status_code=status.HTTP_200_OK)
async def get_interview_history(user_id: str = Depends(verify_token)):
    """
    Get the interview history of the user to buil a chart
    """
    try:
        user_doc = await user_responses.find_one({"user_id": user_id})
        print(len(user_doc))

        if not user_doc.get('analysis'):
            raise HTTPException(status_code=404, detail="No analysis data found")

        print(user_doc)

        history = []
        for domain_name, domain in user_doc['analysis'].items():
            history.append({
            'overallScore': domain.get('overallScore', 0),
            'date': domain.get('date'),
            'time': domain.get('time'),
            'domain_name': domain_name,
            })

        # Sort by date and time in descending order (latest first)
        history.sort(key=lambda x: (x['date'], x['time']), reverse=True)

        print(history)

        if not user_doc:
            raise HTTPException(status_code=404, detail="No interview history found")
        
        return JSONResponse({
            "success": True,
            "interview_history": history
        })
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving interview history: {str(e)}"
        )