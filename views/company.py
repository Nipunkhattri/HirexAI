from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from models.company import interview_data
from database.mongodb import user_company_collection, interview_collection, Company_collection
from services.send_email import send_email
from middleware.middleware import verify_token
import random
import string
from bson import ObjectId
from bson.json_util import dumps
import json
import uuid

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

            email_body = f"""
            <!DOCTYPE html>
            <html lang="en">
            <head>
              <meta charset="UTF-8">
              <meta name="viewport" content="width=device-width, initial-scale=1.0">
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
                .interview-details {{
                  background-color: #f9fafb;
                  border-radius: 8px;
                  padding: 20px;
                  margin-bottom: 24px;
                }}
                .interview-details h2 {{
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
                  <img src="https://via.placeholder.com/150" alt="{company["company_name"]} Logo">
                  <h1>Interview Invitation</h1>
                </div>
                
                <div class="content">
                  <p class="greeting">Hello {candidate['name']},</p>
                  
                  <p class="message">
                    You have been invited to participate in a technical interview with {company["company_name"]}. 
                    We're excited to learn more about your skills and experience in {interview_data.domain}.
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
                  
                  <div class="tips">
                    <h3>Preparation Tips</h3>
                    <ul>
                      <li>Ensure you have a stable internet connection</li>
                      <li>Find a quiet environment with minimal distractions</li>
                      <li>Test your microphone and camera before starting</li>
                      <li>Have a pen and paper ready for notes</li>
                      <li>Review the key concepts in your domain before the interview</li>
                    </ul>
                  </div>
                  
                  <p>
                    Please click the button below to access your interview portal. You can log in using your email and the temporary password provided to you separately.
                  </p>
                  
                  <a href="http://localhost:3000/candidate-login?interviewID={interview_id}" class="button">Access Interview</a>
                  
                  <p>
                    If you have any questions or need to reschedule, please contact us at <a href="mailto:support@hirexai.com">support@hirexai.com</a>.
                  </p>
                  
                  <p>
                    Best regards,<br>
                    The {company["company_name"]} Team
                  </p>
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
            existing_user = await user_company_collection.find_one({"email": candidate["email"]})
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

        return JSONResponse(content={
            "message": "Interview retrieved successfully",
            "interview": interview_helper(interview)
        })

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching interview: {str(e)}")