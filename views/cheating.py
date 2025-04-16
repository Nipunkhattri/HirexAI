from fastapi import APIRouter, Depends, HTTPException, WebSocket
import base64
import numpy as np
import cv2
import json
from time import time
from PIL import Image
from ultralytics import YOLO
import io

cheat_router = APIRouter(prefix="/api/v1/cheat", tags=["Cheating Detection"])

face_model = YOLO("best.pt")
mobile_detection_model = YOLO("object.pt")

@cheat_router.websocket('/face-detection')
async def get_cheat(websocket: WebSocket):
    """
    Get cheat detection status.
    """
    await websocket.accept()
    while True:
        try:
            # Receive image from frontend as base64 string
            base64_data = await websocket.receive_text()
            image_data = base64.b64decode(base64_data)
            image = Image.open(io.BytesIO(image_data)).convert("RGB")

            # Run detection
            results = face_model.predict(image)
            detections = results[0].boxes
            count = len(detections)

            # Return face count
            message = "Don't cheat! Multiple faces detected" if count > 1 else "OK"
            if count > 1:
                await websocket.send_json({
                    "face_count": count,
                    "boxes": [box.xyxy[0].tolist() for box in detections],
                    "message": message
                })
            else:
                await websocket.send_json({
                    "face_count": count,
                    "boxes": [box.xyxy[0].tolist() for box in detections]
                })

        except Exception as e:
            await websocket.send_json({"error": str(e)})
            break

@cheat_router.websocket('/mobile-detection')
async def get_cheat_mobile(websocket: WebSocket):
    """
    Get cheat detection status.
    """
    await websocket.accept()
    while True:
        try:
            # Receive image from frontend as base64 string
            base64_data = await websocket.receive_text()
            image_data = base64.b64decode(base64_data)
            image = Image.open(io.BytesIO(image_data)).convert("RGB")

            # Run detection
            results = mobile_detection_model.predict(image)
            print("Results:", results)
            detections = results[0].boxes
            count = len(detections)

            # Return face count
            message = "Don't cheat! Phone is getting detected" if count > 0 else "OK"
            if count > 1:
                await websocket.send_json({
                    "object_count": count,
                    "boxes": [box.xyxy[0].tolist() for box in detections],
                    "message": message
                })
            else:
                await websocket.send_json({
                    "object_count": count,
                    "boxes": [box.xyxy[0].tolist() for box in detections]
                })

        except Exception as e:
            await websocket.send_json({"error": str(e)})
            break

