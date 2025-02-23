from transformers import pipeline

class SentimentAnalyzer:
    def __init__(self):
        self.model = pipeline("sentiment-analysis", model="tired-racoon/tonika_sentim")

    def predict(self, text):
        result = self.model(text)[0]
        return result["label"], result["score"]
