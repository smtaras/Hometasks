import io
from fastapi import FastAPI, File, UploadFile
from PIL import Image
from transformers import pipeline

app = FastAPI()

classifier = pipeline("image-classification", model="google/mobilenet_v2_1.0_224")

@app.post("/predict")
async def predict(file: UploadFile = File(...)):
    image_data = await file.read()
    image = Image.open(io.BytesIO(image_data))
    
    results = classifier(image)
    
    return {"label": results[0]['label'], "confidence": results[0]['score']}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)