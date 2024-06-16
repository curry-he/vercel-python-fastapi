import time

from fastapi import FastAPI, Request, HTTPException, APIRouter
from fastapi.responses import StreamingResponse
import requests
import json

router = APIRouter()

@router.post("/silicon/v1/chat/completions")
async def generate_image(request: Request):
    try:
        body = await request.json()
        model = body.get("model")
        messages = body.get("messages")

        if not model or not messages or len(messages) == 0:
            raise HTTPException(status_code=400, detail="Bad Request: Missing required fields")

        prompt = messages[-1].get("content")
        new_url = f"https://api.siliconflow.cn/v1/{model}/text-to-image"

        new_request_body = {
            "prompt": prompt,
            "image_size": "1024x1024",
            "batch_size": 1,
            "num_inference_steps": 4,
            "guidance_scale": 1
        }

        response = requests.post(
            new_url,
            headers={
                "accept": "application/json",
                "content-type": "application/json",
                "Authorization": request.headers.get("Authorization")
            },
            json=new_request_body
        )
        response.raise_for_status()  # 检查请求是否成功

        response_body = response.json()
        image_url = response_body["images"][0]["url"]
        unique_id = int(time.time() * 1000)
        current_timestamp = unique_id // 1000

        response_payload = {
            "id": unique_id,
            "object": "chat.completion.chunk",
            "created": current_timestamp,
            "model": "wbot-2.3",
            "choices": [
                {
                    "index": 0,
                    "delta": {
                        "content": f"![]({image_url})"
                    },
                    "finish_reason": "stop"
                }
            ]
        }

        data_string = json.dumps(response_payload)

        async def stream_response():
            yield f"data: {data_string}\n\n"

        return StreamingResponse(
            stream_response(),
            status_code=200,
            headers={
                "Content-Type": "text/event-stream",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "*"
            }
        )

    except Exception as error:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(error)}")
