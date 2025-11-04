from typing import Optional
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import JSONResponse
from transformers import AutoProcessor, Qwen2_5_VLForConditionalGeneration
from PIL import Image
import torch
import io

app = FastAPI()

# Load model and processor once at startup
model = Qwen2_5_VLForConditionalGeneration.from_pretrained(
    "Qwen/Qwen2.5-VL-3B-Instruct",
    device_map="cuda",
    torch_dtype=torch.bfloat16,
)
processor = AutoProcessor.from_pretrained("Qwen/Qwen2.5-VL-3B-Instruct")


@app.post("/predict")
async def predict(
    question: str = Form(...),
    files: Optional[list[UploadFile]] = File(None),
):
    """Runs multimodal inference using Qwen2.5-VL.

    Accepts an English text question and optional image uploads, then
    generates a natural-language answer based on the visual and textual inputs.

    Args:
        question: The text prompt or question.
        files: Optional list of uploaded image files.

    Returns:
        JSONResponse: A JSON object containing the model’s text response.
            Example:
            {"result": "YES — This appears to be an indoor warehouse scene."}
    """
    images = []
    if files:
        for f in files:
            img_bytes = await f.read()
            img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
            images.append(img)

    # Construct multimodal message content
    content = [{"type": "text", "text": question}]
    if images:
        content = [{"type": "image", "image": img} for img in images] + content

    messages = [{"role": "user", "content": content}]
    text = processor.apply_chat_template(
        messages, tokenize=False, add_generation_prompt=True
    )

    inputs = processor(
        text=[text],
        images=images if images else None,
        return_tensors="pt",
    ).to("cuda")

    with torch.no_grad():
        output = model.generate(**inputs, max_new_tokens=64)
        answer = processor.batch_decode(
            output[:, inputs.input_ids.shape[1]:],
            skip_special_tokens=True,
        )

    return JSONResponse({"result": answer[0]})