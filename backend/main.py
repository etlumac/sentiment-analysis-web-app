from fastapi import FastAPI, UploadFile, File
from pydantic import BaseModel
import pandas as pd
from backend.model import SentimentAnalyzer
from fastapi.middleware.cors import CORSMiddleware
from bs4 import BeautifulSoup  # Для очистки HTML

app = FastAPI()
analyzer = SentimentAnalyzer()

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=".*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Словарь для замены меток
LABEL_MAPPING = {
    "LABEL_0": "bad",
    "LABEL_1": "neutral",
    "LABEL_2": "good",
}

class TextRequest(BaseModel):
    text: str

@app.post("/analyze/")
async def analyze_text(request: TextRequest):
    sentiment, confidence = analyzer.predict(request.text)
    sentiment = LABEL_MAPPING.get(sentiment, "unknown")  # Меняем метку
    return {"sentiment": sentiment, "confidence": confidence}

@app.post("/analyze-file/")
async def analyze_file(file: UploadFile = File(...)):
    df = pd.read_excel(file.file)

    # Проверяем, есть ли колонка "MessageText"
    if "MessageText" not in df.columns:
        return {"error": "Файл должен содержать колонку 'MessageText'"}

    # Чистим текст от HTML и обрезаем до 512 символов
    df["text"] = df["MessageText"].fillna("").apply(
        lambda x: BeautifulSoup(x, "html.parser").get_text(strip=True)[:512]
    )

    # Анализ тональности
    df["sentiment"], df["confidence"] = zip(*df["text"].map(analyzer.predict))
    df["sentiment"] = df["sentiment"].map(LABEL_MAPPING)  # Меняем метки

    # Оставляем нужные колонки
    result = df[["UserSenderId", "SubmitDate", "MessageText", "sentiment", "confidence"]]

    return result.to_dict(orient="records")


