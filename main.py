from fastapi import FastAPI, File, UploadFile
from pydantic import BaseModel
from fastapi.responses import JSONResponse
from korail_reservation import reserve_train, Train
from korail_payment import pay_train
from card_ocr import process_document
from korail_search import search_train

app = FastAPI()

class Train(BaseModel):
    departure: str
    destination: str
    date: str
    time: str

@app.post("/search")
async def search_train_endpoint(train: Train):
    return await search_train(train)

@app.post("/reservation")
async def reserve_train_endpoint(train: Train):
    return await reserve_train(train)

@app.post("/pay")
async def pay_train_endpoint():
    return await pay_train()

@app.post("/extract_card_info")
async def extract_card_info(file: UploadFile = File(...)):
    content = await file.read()
    try:
        card_info = process_document(content)
        return card_info
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
