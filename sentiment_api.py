from fastapi import FastAPI
from pydantic import BaseModel
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch
from typing import List, Dict
import numpy as np
import re

app = FastAPI(title="Sentiment Analysis API", description="API for sentiment regression and word highlighting.")

MODEL_NAME = "StepanVagin/nlptown-bert-base-multilingual-uncased-sentiment-fine-tuned"
TOKENIZER_PATH = MODEL_NAME
MODEL_PATH = MODEL_NAME

# Load model and tokenizer from Hugging Face
model = AutoModelForSequenceClassification.from_pretrained(MODEL_NAME)
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model.eval()

class SentimentRequest(BaseModel):
    sentence: str

class SentimentResponse(BaseModel):
    score: float
    highlights: List[Dict[str, str]]

# The model will calculate word importance dynamically based on attention weights

def calculate_word_importance(sentence, attention_weights, tokens, offsets):
    """
    Calculate importance scores for each word in the sentence based on attention weights.
    
    Args:
        sentence: The input sentence
        attention_weights: Attention weights from the transformer model
        tokens: Tokenized words
        offsets: Token offsets for mapping back to original text
    
    Returns:
        Dictionary mapping words to their importance scores
    """
    # Create a mapping from character positions to tokens
    char_to_token = {}
    for i, (start, end) in enumerate(offsets):
        if start == 0 and end == 0:  # Skip special tokens
            continue
        for char_idx in range(start, end):
            char_to_token[char_idx] = i
    
    # Extract words and their positions
    word_importances = {}
    word_positions = []
    
    # Use regex to find word boundaries with their positions
    for match in re.finditer(r'\b\w+\b', sentence):
        word = match.group().lower()
        start, end = match.span()
        word_positions.append((word, start, end))
    
    # Calculate importance for each word based on attention
    for word, start, end in word_positions:
        # Find all tokens that are part of this word
        token_indices = []
        for char_idx in range(start, end):
            if char_idx in char_to_token:
                token_indices.append(char_to_token[char_idx])
        
        # Remove duplicates and sort
        token_indices = sorted(set(token_indices))
        
        if not token_indices:  # Skip if no tokens found for this word
            continue
        
        # Calculate importance based on attention weights for these tokens
        # Use the average attention weight across all layers and heads
        importance = 0.0
        count = 0
        
        for token_idx in token_indices:
            # Skip special tokens
            if token_idx >= len(tokens) - 2:  # Accounting for special tokens
                continue
                
            # Get attention for this token (average across all layers and heads)
            token_attention = attention_weights[:, :, token_idx].mean().item()
            importance += token_attention
            count += 1
        
        if count > 0:
            importance /= count
            word_importances[word] = importance
    
    # Normalize importance scores to range [0.1, 1.0]
    if word_importances:
        min_imp = min(word_importances.values())
        max_imp = max(word_importances.values())
        
        # Avoid division by zero
        if max_imp > min_imp:
            for word in word_importances:
                # Normalize to [0.1, 1.0] range
                word_importances[word] = 0.1 + 0.9 * (word_importances[word] - min_imp) / (max_imp - min_imp)
        else:
            # If all words have the same importance, set to mid-range
            for word in word_importances:
                word_importances[word] = 0.5
    
    return word_importances

@app.post("/analyze/", response_model=SentimentResponse)
def analyze_sentiment(request: SentimentRequest):
    sentence = request.sentence
    inputs = tokenizer(sentence, return_tensors="pt", return_offsets_mapping=True, truncation=True)
    # Remove 'offset_mapping' from model inputs if present
    model_inputs = {k: v for k, v in inputs.items() if k != "offset_mapping"}
    
    with torch.no_grad():
        outputs = model(**model_inputs, output_attentions=True)
        
        # Extract logits for sentiment score calculation
        if hasattr(outputs, "logits"):
            logits = outputs.logits
        else:
            logits = outputs[0]
            
        # Extract attention weights
        attentions = outputs.attentions
        
        # For regression: scale output to 0-10 if needed
        if logits.shape[-1] == 1:
            score = logits.item()
            score = max(0.0, min(10.0, score))
        else:
            # For classification: use softmax and weighted average
            probs = torch.nn.functional.softmax(logits, dim=-1).squeeze()
            score = float((probs * torch.arange(len(probs))).sum().item())
            score = score * (10.0 / (len(probs)-1))  # scale to 0-10
    
    # Process attention weights - average across all layers and heads
    # Shape: [layers, heads, seq_len, seq_len]
    avg_attention = torch.mean(torch.stack(attentions), dim=0)  # Average across layers
    avg_attention = torch.mean(avg_attention, dim=0)  # Average across heads
    
    # Get tokens and their offsets
    tokens = tokenizer.convert_ids_to_tokens(inputs["input_ids"][0])
    offsets = inputs["offset_mapping"][0].tolist()
    
    # Calculate word importance scores
    word_importances = calculate_word_importance(sentence, avg_attention, tokens, offsets)
    
    # Extract words from the sentence by splitting on whitespace
    words = [w for w in sentence.split() if w.strip()]
    highlights = []
    
    # Process each word in the original sentence
    for word in words:
        # Get importance score for this word, default to 0.5 if not found
        importance = word_importances.get(word.lower(), 0.5)
        highlights.append({"word": word, "importance": str(round(importance, 2))})
    
    # Ensure we have highlights for all words
    if not highlights:
        # Fallback if no words were processed
        for idx, (token, offset) in enumerate(zip(tokens, offsets)):
            if offset[0] == 0 and offset[1] == 0:
                continue  # skip special tokens
            word = sentence[offset[0]:offset[1]]
            if word.strip():
                # Default importance of 0.5 for fallback
                highlights.append({"word": word, "importance": str(0.5)})
    
    return {"score": round(score, 2), "highlights": highlights}

@app.get("/")
def root():
    return {"message": "Sentiment Analysis API. Use /analyze/ endpoint with a sentence."}