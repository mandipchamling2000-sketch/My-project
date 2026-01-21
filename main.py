from fastapi import FastAPI, UploadFile, File, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import shutil, os
import pandas as pd

from parser import parse_pdf

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("index.html", {
        "request": request,
        "data": None
    })


@app.post("/upload", response_class=HTMLResponse)
async def upload_pdfs(request: Request, files: list[UploadFile] = File(...)):
    all_data = []

    for file in files:
        path = f"{UPLOAD_DIR}/{file.filename}"
        with open(path, "wb") as f:
            shutil.copyfileobj(file.file, f)

        all_data.extend(parse_pdf(path))

    df = pd.DataFrame(all_data)
    csv_path = "assignments_summary.csv"
    df.to_csv(csv_path, index=False)

    return templates.TemplateResponse("index.html", {
        "request": request,
        "data": df.to_dict(orient="records")
    })

