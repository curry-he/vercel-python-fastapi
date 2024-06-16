from fastapi import FastAPI, HTTPException, APIRouter
from gradio_client import Client
import requests
from io import BytesIO
from PIL import Image
from pydantic import BaseModel

router = APIRouter()

class GenerateImageRequest(BaseModel):
    prompt: str
    negative_prompt: str = """out of frame, worst quality, low quality, 
        jpeg artifacts, ugly, duplicate, morbid, mutilated, extra fingers, 
        mutated hands, poorly drawn hands, poorly drawn face, mutation, 
        deformed, blurry, dehydrated, bad anatomy, bad proportions, 
        extra limbs, cloned face, disfigured, gross proportions, 
        malformed limbs, missing arms, missing legs, extra arms, 
        extra legs, fused fingers, too many fingers, long neck"""
    seed: float = 0
    randomize_seed: bool = True
    width: float = 1024
    height: float = 1024
    guidance_scale: float = 5
    num_inference_steps: float = 28

@router.post("/")
async def generate_image_api(request: GenerateImageRequest):
    """
    生成图像并上传到图床的 API 路由.

    Args:
        request (GenerateImageRequest): 图像生成请求.

    Returns:
        dict: 包含图像 URL 的响应.
    """
    try:
        # 使用 Stable Diffusion 模型生成图像
        client = Client("stabilityai/stable-diffusion-3-medium")
        result = client.predict(
            prompt=request.prompt,
            negative_prompt=request.negative_prompt,
            seed=request.seed,
            randomize_seed=request.randomize_seed,
            width=request.width,
            height=request.height,
            guidance_scale=request.guidance_scale,
            num_inference_steps=request.num_inference_steps,
            api_name="/infer"
        )

        # 读取 webp 文件内容
        with open(result[0], 'rb') as f:
            image_data = f.read()

        # 使用 BytesIO 避免创建临时文件
        with BytesIO(image_data) as input_buffer:
            image = Image.open(input_buffer).convert('RGBA')
            with BytesIO() as output_buffer:
                image.save(output_buffer, format='PNG')
                png_image_data = output_buffer.getvalue()

        # 上传图像到图床
        url, delete_url = upload_image(png_image_data)

        # 删除图床中的图片
        requests.get(delete_url)

        return {"image_url": url}
    except Exception as e:
        # 处理任何异常,并返回适当的错误响应
        raise HTTPException(status_code=500, detail=str(e))

def upload_image(image_data: bytes):
    """
    上传图像数据到图床.

    Args:
        image_data: 图像的二进制数据.

    Returns:
        一个包含图像 URL 和删除 URL 的元组.
    """
    url = "https://www.picgo.net/api/1/upload"
    files = {'source': ('image.png', image_data, 'image/png')}
    data = {
        'key': 'chv_CLkW_f7b2e91d2653e629feefbafc8017ca1496847853d531cbc1367b6eb5824f340928aa4c0465e6ec187f77f9c35c3b039868a35c50ed58586100c6d478f5ad8e10',
    }

    response = requests.post(url, data=data, files=files)

    return response.json().get('image').get('url'), response.json().get('image').get('delete_url')

