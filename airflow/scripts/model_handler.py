# model_handler.py
from transformers import RobertaTokenizer, RobertaForSequenceClassification
import torch.nn.functional as F
import torch

class FakeNewsDetector:
    def __init__(self, model_path):
        self.tokenizer = RobertaTokenizer.from_pretrained(model_path)
        self.model = RobertaForSequenceClassification.from_pretrained(model_path,local_files_only=True)
        self.model.eval()
    
    def classify_text(self, text):
        """Classify text and return probability of being fake"""
        inputs = self.tokenizer(text, return_tensors="pt", truncation=True, padding=True, max_length=512)
        with torch.no_grad():
            probs = F.softmax(self.model(**inputs).logits, dim=1)
        return probs[0][1].item()
    
    def get_prediction(self, prob, threshold=0.85):
        """Convert probability to prediction label"""
        return 'Fake' if prob > threshold else 'True'