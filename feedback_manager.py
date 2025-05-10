import streamlit as st
import json
import os
from datetime import datetime

FEEDBACK_FILE = "feedback_requests.json"
DATASET_FILE = "special_dataset.json"

# Ensure feedback file exists
def ensure_file_exists(filename):
    if not os.path.exists(filename):
        with open(filename, "w") as f:
            json.dump([], f)

def load_feedback():
    ensure_file_exists(FEEDBACK_FILE)
    with open(FEEDBACK_FILE, "r") as f:
        return json.load(f)

def save_feedback(feedback_list):
    with open(FEEDBACK_FILE, "w") as f:
        json.dump(feedback_list, f, indent=2)

def add_to_dataset(entry):
    ensure_file_exists(DATASET_FILE)
    with open(DATASET_FILE, "r") as f:
        dataset = json.load(f)
    dataset.append(entry)
    with open(DATASET_FILE, "w") as f:
        json.dump(dataset, f, indent=2)

def main():
    st.set_page_config(page_title="Feedback Manager", layout="centered")
    st.title("Feedback Requests Review")
    feedback_list = load_feedback()
    if not feedback_list:
        st.info("No feedback requests to review.")
        return
    for idx, fb in enumerate(feedback_list):
        st.markdown(f"**Request #{idx+1}**")
        st.markdown(f"- **Text:** {fb['text']}")
        st.markdown(f"- **Predicted Sentiment:** {fb['sentiment']}")
        st.markdown(f"- **Score:** {fb['score']}")
        st.markdown(f"- **Submitted:** {fb['timestamp']}")
        col1, col2 = st.columns(2)
        with col1:
            if st.button(f"Accept #{idx+1}"):
                add_to_dataset(fb)
                feedback_list.pop(idx)
                save_feedback(feedback_list)
                st.success("Added to special dataset.")
                st.rerun()
        with col2:
            if st.button(f"Reject #{idx+1}"):
                feedback_list.pop(idx)
                save_feedback(feedback_list)
                st.info("Feedback rejected.")
                st.rerun()

if __name__ == "__main__":
    main()