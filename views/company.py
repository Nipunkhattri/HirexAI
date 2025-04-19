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

        if existing_interview:
            raise HTTPException(status_code=400, detail="An interview is already scheduled for this company, domain, date, and time.")

        user_ids = []

        print(interview_data)

        for candidate in interview_data.list_of_candidates:
            password = generate_password()

            user_doc = {
                "name": candidate["name"],
                "email": candidate["email"],
                "password": password,
            }

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
                    body=f"Hi {candidate['name']},\n\nYou've been registered for an interview.\nLogin Email: {candidate['email']}\nPassword: {existing_user['password']}\n\nGood luck!\nTeam HirexAI",
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
                body=f"Hi {candidate['name']},\n\nYou've been registered for an interview.\nLogin Email: {candidate['email']}\nPassword: {password}\n\nGood luck!\nTeam HirexAI",
            )

        # Get company details
        print(company_id)
        company = await Company_collection.find_one({"_id": ObjectId(company_id)})
        print(company)
        if not company:
            raise HTTPException(status_code=404, detail="Company not found")

        # Save interview data
        interview_doc = {
            "company_name": company['company_name'],
            "company_id": company_id,
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
    
@company_router.get("/get-all-interviews", status_code=status.HTTP_200_OK)
async def get_all_interviews(user_id: str = Depends(verify_token)):
    try:
        interviews_cursor = await interview_collection.find({"list_of_candidates.user_id": user_id}).to_list(length=None)
        interviews = json.loads(dumps(interviews_cursor))  # Convert from BSON to JSON-friendly
        print(interviews)
        return JSONResponse(content={"message": "Interviews retrieved successfully", "interviews": interviews})

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))