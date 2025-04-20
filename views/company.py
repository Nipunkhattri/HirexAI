from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from models.company import interview_data
from database.mongodb import user_company_collection, interview_collection, Company_collection, Users_Test
from services.send_email import send_email
from middleware.middleware import verify_token
import random
import string
from bson import ObjectId
from bson.json_util import dumps
import json
import uuid
from llama_index.llms.openai import OpenAI
from config.setting import settings
from models.company import SubmitTestAnswer
from datetime import datetime

company_router = APIRouter(prefix="/api/v1/company", tags=["Company"])

def generate_password(length=8):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

@company_router.post("/create-interview", status_code=status.HTTP_201_CREATED)
async def create_interview(interview_data: interview_data, company_id: str = Depends(verify_token)):
    try:
        existing_interview = await interview_collection.find_one({
            "company_id": company_id,
            "domain": interview_data.domain,
            "interview_date": interview_data.interview_date,
            "interview_time": interview_data.interview_time
        })

        interview_id = str(uuid.uuid4())

        if existing_interview:
            raise HTTPException(status_code=400, detail="An interview is already scheduled for this company, domain, date, and time.")

        user_ids = []

        # Get company details
        company = await Company_collection.find_one({"_id": ObjectId(company_id)})
        if not company:
            raise HTTPException(status_code=404, detail="Company not found")

        print(interview_data)

        for candidate in interview_data.list_of_candidates:
            password = generate_password()

            user_doc = {
                "name": candidate["name"],
                "email": candidate["email"],
                "password": password,
            }
            existing_user = await user_company_collection.find_one({"email": candidate["email"]})

            email_password = existing_user["password"] if existing_user else password

            email_body = f"""
            <!DOCTYPE html>
            <html lang="en">
            <head>
            <meta charset="UTF-8" />
            <meta name="viewport" content="width=device-width, initial-scale=1.0" />
            <title>Interview Invitation</title>
            <style>
                body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                line-height: 1.6;
                color: #333;
                margin: 0;
                padding: 0;
                background-color: #f5f5f5;
                }}
                .container {{
                max-width: 600px;
                margin: 0 auto;
                background-color: #ffffff;
                border-radius: 8px;
                overflow: hidden;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                }}
                .header {{
                background-color: #4f46e5;
                padding: 24px;
                text-align: center;
                }}
                .header img {{
                max-height: 60px;
                }}
                .header h1 {{
                color: white;
                margin: 16px 0 0;
                font-size: 24px;
                font-weight: 600;
                }}
                .content {{
                padding: 32px 24px;
                }}
                .greeting {{
                font-size: 18px;
                font-weight: 600;
                margin-bottom: 16px;
                }}
                .message {{
                margin-bottom: 24px;
                color: #555;
                }}
                .interview-details, .credentials {{
                background-color: #f9fafb;
                border-radius: 8px;
                padding: 20px;
                margin-bottom: 24px;
                }}
                .interview-details h2, .credentials h2 {{
                margin-top: 0;
                font-size: 18px;
                color: #4f46e5;
                margin-bottom: 16px;
                }}
                .detail-row {{
                display: flex;
                margin-bottom: 12px;
                }}
                .detail-label {{
                width: 120px;
                font-weight: 600;
                color: #6b7280;
                }}
                .detail-value {{
                flex: 1;
                font-weight: 500;
                }}
                .button {{
                display: block;
                text-align: center;
                background-color: #4f46e5;
                color: white;
                text-decoration: none;
                padding: 12px 24px;
                border-radius: 6px;
                font-weight: 600;
                margin: 32px auto;
                width: 200px;
                }}
                .button:hover {{
                background-color: #4338ca;
                }}
                .tips {{
                background-color: #f0f9ff;
                border-left: 4px solid #3b82f6;
                padding: 16px;
                margin-bottom: 24px;
                }}
                .tips h3 {{
                margin-top: 0;
                color: #1e40af;
                font-size: 16px;
                }}
                .tips ul {{
                margin: 0;
                padding-left: 20px;
                }}
                .tips li {{
                margin-bottom: 8px;
                }}
                .footer {{
                background-color: #f9fafb;
                padding: 20px 24px;
                text-align: center;
                color: #6b7280;
                font-size: 14px;
                }}
                .social-links {{
                margin-top: 16px;
                }}
                .social-links a {{
                display: inline-block;
                margin: 0 8px;
                }}
                .social-links img {{
                width: 24px;
                height: 24px;
                }}
                @media (max-width: 600px) {{
                .container {{
                    border-radius: 0;
                }}
                .detail-row {{
                    flex-direction: column;
                }}
                .detail-label {{
                    width: 100%;
                    margin-bottom: 4px;
                }}
                }}
            </style>
            </head>
            <body>
            <div class="container">
                <div class="header">
                <img src="https://via.placeholder.com/150" alt="{company["company_name"]} Logo" />
                <h1>Interview Invitation</h1>
                </div>
                
                <div class="content">
                <p class="greeting">Hello {candidate['name']},</p>
                
                <p class="message">
                    You have been invited to participate in a technical interview with <strong>{company["company_name"]}</strong>. 
                    We're excited to learn more about your skills and experience in <strong>{interview_data.domain}</strong>.
                </p>
                
                <div class="interview-details">
                    <h2>Interview Details</h2>
                    <div class="detail-row">
                    <div class="detail-label">Company:</div>
                    <div class="detail-value">{company["company_name"]}</div>
                    </div>
                    <div class="detail-row">
                    <div class="detail-label">Domain:</div>
                    <div class="detail-value">{interview_data.domain}</div>
                    </div>
                    <div class="detail-row">
                    <div class="detail-label">Date:</div>
                    <div class="detail-value">{interview_data.interview_date}</div>
                    </div>
                    <div class="detail-row">
                    <div class="detail-label">Time:</div>
                    <div class="detail-value">{interview_data.interview_time}</div>
                    </div>
                </div>

                <div class="credentials">
                    <h2>Login Credentials</h2>
                    <div class="detail-row">
                    <div class="detail-label">Email:</div>
                    <div class="detail-value">{candidate["email"]}</div>
                    </div>
                    <div class="detail-row">
                    <div class="detail-label">Password:</div>
                    <div class="detail-value">{email_password}</div>
                    </div>
                </div>
                
                <div class="tips">
                    <h3>Preparation Tips</h3>
                    <ul>
                    <li>Ensure you have a stable internet connection</li>
                    <li>Find a quiet environment with minimal distractions</li>
                    <li>Test your microphone and camera before starting</li>
                    <li>Have a pen and paper ready for notes</li>
                    <li>Review key concepts in your domain before the interview</li>
                    </ul>
                </div>
                
                <p>
                    Please click the button below to access your interview portal.
                </p>
                
                <a href="http://localhost:3000/candidate-login?interviewID={interview_id}" class="button">Access Interview</a>
                
                <p>
                    If you have any questions or need to reschedule, please contact us at 
                    <a href="mailto:support@hirexai.com">support@hirexai.com</a>.
                </p>
                
                <p>Best regards,<br>The {company["company_name"]} Team</p>
                </div>
                
                <div class="footer">
                <p>© 2023 {company["company_name"]}. All rights reserved.</p>
                <p>1234 Company Address, City, Country</p>
                <div class="social-links">
                    <a href="https://linkedin.com"><img src="https://cdn-icons-png.flaticon.com/512/174/174857.png" alt="LinkedIn"></a>
                    <a href="https://twitter.com"><img src="https://cdn-icons-png.flaticon.com/512/733/733579.png" alt="Twitter"></a>
                    <a href="https://company-website.com"><img src="https://cdn-icons-png.flaticon.com/512/1006/1006771.png" alt="Website"></a>
                </div>
                </div>
            </div>
            </body>
            </html>
            """

            # Check if user already exists
            if existing_user:
                # Add existing user to user_ids list
                user_ids.append({
                    "name": candidate["name"],
                    "email": candidate["email"],
                    "user_id": str(existing_user["_id"])
                })

                await send_email(
                    to=[candidate['email']],
                    subject="HirexAI Interview Login Credentials",
                    body=email_body
                )
                continue

            # Insert into MongoDB
            result = await user_company_collection.insert_one(user_doc)
            print(result)

            user_ids.append({
                "name": candidate["name"],
                "email": candidate["email"],
                "user_id": str(result.inserted_id)
            })
            print(user_ids)

            await send_email(
                to=[candidate['email']],
                subject="HirexAI Interview Login Credentials",
                body=email_body
            )

        # Save interview data
        interview_doc = {
            "company_name": company['company_name'],
            "company_id": company_id,
            "interview_id": interview_id,
            "domain": interview_data.domain,
            "interview_date": interview_data.interview_date,
            "interview_time": interview_data.interview_time,
            "list_of_candidates": user_ids,
            "location": company['location'],
        }

        interview_result = await interview_collection.insert_one(interview_doc)

        return JSONResponse(
            content={"message": "Interview created successfully", "interview_id": str(interview_result.inserted_id)},
            status_code=status.HTTP_201_CREATED
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@company_router.get("/get-company-details", status_code=status.HTTP_200_OK)
async def get_company_details(company_id: str = Depends(verify_token)):
    try:
        company = await Company_collection.find_one({"_id": ObjectId(company_id)})
        if not company:
            raise HTTPException(status_code=404, detail="Company not found")

        # Convert ObjectId to string
        company['_id'] = str(company['_id'])
        return JSONResponse(content={"message": "Company details retrieved successfully", "company": company})

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
def interview_helper(interview) -> dict:
    return {
        "company_name": interview["company_name"],
        "domain": interview["domain"],
        "interview_date": interview["interview_date"],
        "interview_time": interview["interview_time"],
        "location": interview["location"]
    }

@company_router.get("/get-interview", status_code=status.HTTP_200_OK)
async def get_interview_by_ID(interviewID: str, user_id: str = Depends(verify_token)):
    try:
        interview = await interview_collection.find_one({"interview_id": interviewID})
        if not interview:
            raise HTTPException(status_code=404, detail="Interview not found")
        
        list_of_candidates = interview["list_of_candidates"]
        

        return JSONResponse(content={
            "message": "Interview retrieved successfully",
            "interview": interview_helper(interview)
        })

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching interview: {str(e)}")

@company_router.get('/generate-question', status_code=status.HTTP_200_OK)
async def get_interview_questions(interviewID: str, user_id: str = Depends(verify_token)):
    try:
        interview = await interview_collection.find_one({"interview_id": interviewID})
        if not interview:
            raise HTTPException(status_code=404, detail="Interview not found")
        domain = interview["domain"]

        llm = OpenAI(model="gpt-4o-mini", api_key=settings.OPENAI_API_KEY)

        prompt = f"""You are an expert technical interviewer. Your task is to generate two unique technical interview questions based on the given domain . The questions should meet the following criteria:
        Be clear, concise, and diverse each time the prompt is run.

        Cover one basic and one advanced concept within the domain.

        The questions should focus on theory or approach, not coding or syntax.

        Use the domain as a guide to tailor the questions.

        Ensure the questions are not repeated across multiple runs by introducing creative variations in phrasing and focus.

        Input:

        domain: {domain}

        Output:
        Provide a valid JSON object in this exact structure:
        {{
            "questions": [
                "<Question 1>",
                "<Question 2>"
            ]
        }}
        """
        response = llm.complete(prompt)
        response_text = response.text.strip()
        print(response_text)
        try:
            response_dict = json.loads(response_text)
            return JSONResponse(content={"message": "Questions generated successfully", "questions": response_dict})
        except json.JSONDecodeError:
            raise HTTPException(status_code=500, detail="Error decoding JSON response from LLM")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating questions: {str(e)}")

@company_router.post('/submit_answer', status_code=status.HTTP_200_OK)
async def submit_answer(
  answer: SubmitTestAnswer,
  user_id: str = Depends(verify_token)
):
  """
  Record the answer (text) submitted for a question with user_id as key.
  """
  try:
    # Check if the interview exists
    interview = await interview_collection.find_one({"interview_id": answer.interview_id})
    if not interview:
      raise HTTPException(status_code=404, detail="Interview not found")

    # Prepare the answer data
    answer_data = {
      "question": answer.question,
      "answer_text": answer.answer_text
    }

    # Check if there's an existing test record for this interview
    existing_test = await Users_Test.find_one({"interview_id": answer.interview_id})

    if existing_test:
      # If user_id key exists, append to its answers array
      if str(user_id) in existing_test.get("answers", {}):
        await Users_Test.update_one(
          {"interview_id": answer.interview_id},
          {"$push": {f"answers.{str(user_id)}": answer_data}}
        )
      else:
        # If user_id key doesn't exist, create it with new answer array
        await Users_Test.update_one(
          {"interview_id": answer.interview_id},
          {"$set": {f"answers.{str(user_id)}": [answer_data]}}
        )
    else:
      # Create new document with answers object containing user_id key
      test_doc = {
        "interview_id": answer.interview_id,
        "domain_name": interview["domain"],
        "answers": {
          str(user_id): [answer_data]
        }
      }
      await Users_Test.insert_one(test_doc)

    return JSONResponse({"success": "Answer saved successfully"})
  
  except Exception as e:
    raise HTTPException(status_code=500, detail=f"Error saving answer: {str(e)}")

@company_router.get('/analysis', status_code=status.HTTP_200_OK)
async def get_analysis(interviewID: str, user_id: str = Depends(verify_token)):
  try:
    # Fetch the interview details
    interview = await interview_collection.find_one({"interview_id": interviewID})
    if not interview:
      raise HTTPException(status_code=404, detail="Interview not found")
    domain = interview["domain"]
    # Fetch the user's test answers
    user_test = await Users_Test.find_one({"interview_id": interviewID})
    if not user_test:
      raise HTTPException(status_code=404, detail="User test answers not found")
    domain_response = user_test["answers"]
    
    user = await user_company_collection.find_one({"_id": ObjectId(user_id)})
    if not user:
      raise HTTPException(status_code=404, detail="User not found")

    llm = OpenAI(model="gpt-4o-mini", api_key=settings.OPENAI_API_KEY)

    overall_prompt = f"""
    You are an AI interview evaluator assessing technical interview answers for a specific domain.

    You are given:
    1. A {domain} domain 
    2. A {domain_response} that contains a list of questions and the corresponding answers submitted by a user during an interview.

    Your task is to:
    - Analyze each answer to determine:
    - How **technically correct** it is.
    - How **relevant and clear** the explanation is.
    - How much the answer shows the candidate's **depth of understanding** of the concept.
    - Based on this, calculate:
    - **Overall Score** (0 to 100): Reflects the user's total performance.
    - **Technical Skills Score** (0 to 100): Accuracy and correctness of technical knowledge.
    - **Problem Solving Score** (0 to 100): Understanding of problem-solving approaches, algorithms, efficiency, and code structuring.
    - **Skill Breakdown**: Extract key skills mentioned or implied in the answers and rate the user's proficiency (0 to 100) in each.

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

    Be fair and precise. Base your analysis only on what is provided in the answers. Do not assume extra knowledge unless explicitly demonstrated.
    """
    response = llm.complete(overall_prompt)
    scores_dict = json.loads(response.text.strip())
    print(scores_dict)

    result_object = {
      "name": user["name"],
      "email": user["email"],
      "overallScore": scores_dict["Overall_Score"],
      "technicalSkillsScore": scores_dict["Technical_Skills_Score"], 
      "problemSolvingScore": scores_dict["Problem_Solving_Score"],
      "skillBreakdown": scores_dict.get("skillBreakdown", []),
      "date": datetime.utcnow().strftime("%d/%m/%Y"),
    }

    if "analysis" in user_test:
      # If analysis exists, append new result
      await Users_Test.update_one(
        {"interview_id": interviewID},
        {"$set": {f"analysis.{str(user_id)}": result_object}}
      )
    else:
      # Create new analysis array with first result
      await Users_Test.update_one(
        {"interview_id": interviewID},
        {"$set": {"analysis": {str(user_id): result_object}}}
      )

    return JSONResponse(content={"message": "Analysis retrieved successfully"})

  except Exception as e:
    raise HTTPException(status_code=500, detail=f"Error fetching analysis: {str(e)}")

@company_router.get('/detected-cheating', status_code=status.HTTP_200_OK)
async def detected_cheating(interviewID: str, user_id: str = Depends(verify_token)):
    try:
        # Fetch the user's details
        user = await user_company_collection.find_one({"_id": ObjectId(user_id)})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        interview = await interview_collection.find_one({"interview_id": interviewID})
        if not interview:
            raise HTTPException(status_code=404, detail="Interview not found")
        existing_test = await Users_Test.find_one({"interview_id": interviewID})

        print(existing_test)

        if existing_test:
            result_object = {
              "name": user["name"],
              "email": user["email"],
              "Detected": "cheating", 
              "overallScore": 0,
              "date": datetime.utcnow().strftime("%d/%m/%Y"),
            }

            # Get existing analysis data
            existing_analysis = existing_test.get("analysis", {})
            # Update with new data while preserving existing
            existing_analysis[str(user_id)] = result_object

            await Users_Test.update_one(
          {"interview_id": interviewID},
          {"$set": {"analysis": existing_analysis}}
            )
        else:
            test_doc = {
          "interview_id": interviewID,
          "domain_name": interview["domain"],
          "analysis": {
              str(user_id): {
            "name": user["name"],
            "email": user["email"],
            "overallScore": 0,
            "Detected": "cheating",
            "date": datetime.utcnow().strftime("%d/%m/%Y"),
              }
          }
            }
            await Users_Test.insert_one(test_doc)

        return JSONResponse(content={"message": "Cheating analysis retrieved successfully"})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching cheating analysis: {str(e)}")
    

@company_router.get('/leaderboard', status_code=status.HTTP_200_OK)
async def get_leaderboard(interviewID: str, user_id: str = Depends(verify_token)):
    try:
        # Fetch the interview details
        interview = await interview_collection.find_one({"interview_id": interviewID})
        if not interview:
            raise HTTPException(status_code=404, detail="Interview not found")
        
        list_of_candidates = interview["list_of_candidates"]
        leaderboard = []

        for candidate in list_of_candidates:
            id = candidate["user_id"]

            test_result = await Users_Test.find_one({"interview_id": interviewID})
            if test_result and "analysis" in test_result:
              analysis = test_result["analysis"].get(id)
              if analysis:
                leaderboard.append({
                  "name": candidate["name"],
                  "email": candidate["email"],
                  "overallScore": analysis.get("overallScore", 0),
                  "domain": interview["domain"],
                  "Detected": analysis.get("Detected", "No cheating detected"),
                })
        
        print(leaderboard)

        return JSONResponse(content={"message": "Leaderboard retrieved successfully", "leaderboard": leaderboard})

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching leaderboard: {str(e)}")
    
@company_router.get("/get-all-interviews", status_code=status.HTTP_200_OK)
async def get_all_interviews(company_id: str = Depends(verify_token)):
    try:
        interviews = await interview_collection.find({"company_id": company_id}).to_list(length=100)
        if not interviews:
            raise HTTPException(status_code=404, detail="No interviews found")

        return JSONResponse(content={
            "message": "Interviews retrieved successfully",
            "interviews": [interview_helper(interview) for interview in interviews]
        })

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching interviews: {str(e)}")