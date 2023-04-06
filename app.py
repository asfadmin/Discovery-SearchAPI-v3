from fastapi import FastAPI
from fastapi.responses import JSONResponse

app = FastAPI()

@app.get("/")
def health_check():
    return JSONResponse({"hello": "world"})

@app.get("/{text}")
def read_item(text: str):
    return JSONResponse({"result": text})
