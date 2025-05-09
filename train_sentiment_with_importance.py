import torch
from torch.utils.data import Dataset, DataLoader
from transformers import AutoTokenizer, AutoModelForSequenceClassification, AdamW
import torch.nn.functional as F
import json
import os
import csv
import time
from typing import List, Dict

# Configurations
MODEL_NAME = "cardiffnlp/twitter-roberta-base-sentiment-latest"  # Replace with regression model if available
BATCH_SIZE = 8
EPOCHS = 3
LR = 2e-5
MAX_LEN = 128

# Example dataset class (supports CSV and JSONL)
class ReviewDataset(Dataset):
    def __init__(self, data_path, tokenizer, max_len=128):
        self.samples = []
        self.tokenizer = tokenizer
        self.max_len = max_len
        if data_path.endswith(".csv"):
            with open(data_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # Expecting columns: text, label (label as int or str convertible to int)
                    sentiment_str = row["sentiment"].strip().lower()
                    if sentiment_str == "positive":
                        label = 1
                    elif sentiment_str == "negative":
                        label = 0
                    else:
                        raise ValueError(f"Unknown sentiment label: {sentiment_str}")
                    sample = {"text": row["review"], "label": label}
                    self.samples.append(sample)
        else:
            with open(data_path, "r", encoding="utf-8") as f:
                for line in f:
                    self.samples.append(json.loads(line))

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        sample = self.samples[idx]
        text = sample["text"]
        label = sample["label"]
        encoding = self.tokenizer(text, return_tensors="pt", max_length=self.max_len, truncation=True, padding="max_length", return_offsets_mapping=True)
        item = {k: v.squeeze(0) for k, v in encoding.items() if k != "offset_mapping"}
        item["label"] = torch.tensor(label, dtype=torch.long)
        item["offset_mapping"] = encoding["offset_mapping"].squeeze(0)
        item["text"] = text
        return item


def train(data_path, save_path):
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    model = AutoModelForSequenceClassification.from_pretrained(MODEL_NAME, output_attentions=True)
    model.train()
    dataset = ReviewDataset(data_path, tokenizer, max_len=MAX_LEN)
    loader = DataLoader(dataset, batch_size=BATCH_SIZE, shuffle=True)
    optimizer = AdamW(model.parameters(), lr=LR)
    device = torch.device("mps" if torch.backends.mps.is_available() else ("cuda" if torch.cuda.is_available() else "cpu"))
    print(device)
    model.to(device)

    for epoch in range(EPOCHS):
        total_loss = 0.0
        print(f"\nEpoch {epoch+1}/{EPOCHS} started...")
        epoch_start_time = time.time()
        for batch_idx, batch in enumerate(loader):
            batch_start_time = time.time() if batch_idx == 0 else batch_start_time
            optimizer.zero_grad()
            input_ids = batch["input_ids"].to(device)
            attention_mask = batch["attention_mask"].to(device)
            labels = batch["label"].to(device)
            outputs = model(input_ids=input_ids, attention_mask=attention_mask, labels=labels, output_attentions=True)
            loss = outputs.loss
            loss.backward()
            optimizer.step()
            total_loss += loss.item()
            # Checkpoint every 1000 steps
            if (batch_idx + 1) % 1000 == 0:
                checkpoint_dir = os.path.join(save_path, f"checkpoint-epoch{epoch+1}-step{batch_idx+1}")
                os.makedirs(checkpoint_dir, exist_ok=True)
                model.save_pretrained(checkpoint_dir)
                tokenizer.save_pretrained(checkpoint_dir)
                print(f"Checkpoint saved at {checkpoint_dir}")
            # Timing logic
            batches_done = batch_idx + 1
            elapsed = time.time() - epoch_start_time
            avg_batch_time = elapsed / batches_done
            batches_left = len(loader) - batches_done
            est_time_left = avg_batch_time * batches_left
            if (batch_idx + 1) % 10 == 0 or (batch_idx + 1) == len(loader):
                mins, secs = divmod(est_time_left, 60)
                print(f"  Batch {batch_idx+1}/{len(loader)} | Current Loss: {loss.item():.4f} | Est. time left: {int(mins):02d}:{int(secs):02d}")
        epoch_time = time.time() - epoch_start_time
        mins, secs = divmod(epoch_time, 60)
        print(f"Epoch {epoch+1}/{EPOCHS} | Sentiment Loss: {total_loss/len(loader):.4f} | Time: {int(mins):02d}:{int(secs):02d}")
    model.save_pretrained(save_path)
    tokenizer.save_pretrained(save_path)
    print(f"Model saved to {save_path}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=str, default="/content/data.jsonl", help="Path to training data (JSONL or CSV)")
    parser.add_argument("--save", type=str, default="/content/model_save", help="Path to save trained model")
    args = parser.parse_args()
    train(args.data, args.save)