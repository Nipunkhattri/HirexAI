from fastapi_mail import FastMail, MessageSchema
from config.setting import settings,conf
from typing import List

async def send_email(to: List[str], subject: str, body: str):
    message = MessageSchema(
        subject=subject,
        recipients=to,
        body=body,
        subtype="html"
    )
    print(conf)
    fm = FastMail(conf)
    await fm.send_message(message)
