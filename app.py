import streamlit as st
from streamlit.components.v1 import html
import requests
import json
from datetime import datetime
import os
from feedback_manager import ensure_file_exists
import time

# --- Landing Section State ---
if "landing_shown" not in st.session_state:
    st.session_state["landing_shown"] = True
if "show_examples" not in st.session_state:
    st.session_state["show_examples"] = False

def show_landing():
    st.set_page_config(page_title="TextSense", layout="centered")
    st.markdown("""
    <div style='text-align:center;'>
        <span style='font-size:3em;'>🧠</span>
        <h1 style='margin-bottom:0.2em;'>TextSense</h1>
        <div style='font-size:1.1em;margin-bottom:1em;color:#444;'>
            Instantly understand the sentiment behind your text.<br/>
            Get clear, actionable insights for better communication.
        </div>
        <div style='font-size:1em;margin-bottom:1.2em;color:#888;'>
            <b>AI can make mistakes, use answers only for reference</b>
        </div>
    </div>
    """, unsafe_allow_html=True)
    col1, col2 = st.columns([1,1])
    start_clicked = col1.button("Start Analysis", key="start_analysis_btn", use_container_width=True)
    examples_clicked = col2.button("View Examples", key="view_examples_btn", use_container_width=True)
    st.markdown("""
    <div style='margin-bottom:1.2em;'>
        <div style='font-size:1em;margin-bottom:0.3em;'>Sentiment Scale</div>
        <div style='height:18px;width:320px;margin:auto;background:linear-gradient(90deg,#c00000,#ffdc00,#21bf21);border-radius:9px;position:relative;'>
            <span style='position:absolute;left:0;top:22px;font-size:0.95em;color:#c00000;'>Negative</span>
            <span style='position:absolute;left:50%;top:22px;transform:translateX(-50%);font-size:0.95em;color:#ffdc00;'>Neutral</span>
            <span style='position:absolute;right:0;top:22px;font-size:0.95em;color:#21bf21;'>Positive</span>
        </div>
    </div>
    <div style='font-size:1em;color:#555;margin-top:1.2em;'>
        Paste your text and let TextSense analyze its sentiment and highlight important words. No technical knowledge needed—just clear, fast results.
    </div>
    """, unsafe_allow_html=True)
    if start_clicked:
        st.session_state["landing_shown"] = False
        st.rerun()
    if examples_clicked:
        st.session_state["show_examples"] = True
        st.session_state["landing_shown"] = False
        st.rerun()

if st.session_state["landing_shown"]:
    show_landing()
    st.stop()

if st.session_state["show_examples"]:
    st.markdown("""
    ### Example Texts
    - "I love this product! It exceeded my expectations."
    - "The service was okay, nothing special."
    - "I'm very disappointed with the quality."
    """)
    col1, col2 = st.columns([1,1])
    go_to_analysis_clicked = col1.button("Go to Analysis", key="go_to_analysis_from_examples")
    home_clicked = col2.button("Back to Welcome", key="home_from_examples")
    if go_to_analysis_clicked:
        st.session_state["show_examples"] = False
        st.session_state["landing_shown"] = False
        st.rerun()
    if home_clicked:
        st.session_state["show_examples"] = False
        st.session_state["landing_shown"] = True
        st.rerun()
    st.stop()

# --- Main App Workflow (unchanged) ---
if "stage" not in st.session_state:
    st.session_state.stage = 0

def set_stage(i):
    st.session_state.stage = i

st.set_page_config(page_title="Sentiment Checker", layout="centered")
st.title("Sentiment Analysis Interface")

st.markdown("""
<div style='font-size:1em;color:#888;margin-bottom:0.7em;'>
<b>Warning:</b> AI can make mistakes, use answers only for reference.
</div>
""", unsafe_allow_html=True)

# Example texts for one-click insertion
example_texts = [
    ("I love this product! It exceeded my expectations.", "Positive"),
    ("The service was okay, nothing special.", "Neutral"),
    ("I'm very disappointed with the quality.", "Negative"),
    ("The meeting was productive, but some issues remain unresolved.", "Mixed")
]

if "input_text" not in st.session_state:
    st.session_state["input_text"] = ""

col1, col2 = st.columns([8,1])
with col1:
    user_input = st.text_area(
        "",
        st.session_state["input_text"],
        height=180,
        key="input_text_area",
        label_visibility="collapsed",
        on_change=None
    )
    # Update session state if changed
    if user_input != st.session_state["input_text"]:
        st.session_state["input_text"] = user_input
    # Character/word counter (dynamic)
    char_count = len(st.session_state["input_text"])
    word_count = len(st.session_state["input_text"].split())
    st.markdown(f"<div style='color:#888;font-size:0.98em;margin-bottom:0.5em;'>Characters: <b>{char_count}</b> | Words: <b>{word_count}</b></div>", unsafe_allow_html=True)
with col2:
    analyze_button = st.button("Enter", type="primary")
    clear_button = st.button("Clear", key="clear_input_btn")
    if clear_button:
        st.session_state["input_text"] = ""
        st.rerun()

# Example Texts section with one-click insert
with st.expander("Example Texts", expanded=False):
    for idx, (ex, tone) in enumerate(example_texts):
        col_ex, col_btn = st.columns([6,2])
        with col_ex:
            st.markdown(f"<span style='color:#444;font-size:1.05em;'>\"{ex}\"</span> <span style='color:#888;font-size:0.95em;'>[{tone}]</span>", unsafe_allow_html=True)
        with col_btn:
            if st.button(f"Insert Example {idx+1}", key=f"insert_example_{idx}"):
                st.session_state["input_text"] = ex
                st.rerun()

col3, col4 = st.columns([1,1])
home_from_analysis = col3.button("Back to Welcome", key="home_from_analysis")
examples_from_analysis = col4.button("View Examples", key="examples_from_analysis")
if home_from_analysis:
    st.session_state["landing_shown"] = True
    st.session_state["show_examples"] = False
    st.session_state["input_text"] = user_input
    st.rerun()
if examples_from_analysis:
    st.session_state["show_examples"] = True
    st.session_state["landing_shown"] = False
    st.session_state["input_text"] = user_input
    st.rerun()

if "feedback_active" not in st.session_state:
    st.session_state["feedback_active"] = False
if "actual_score" not in st.session_state:
    st.session_state["actual_score"] = 0.0

def update_score():
    st.session_state["actual_score"] = st.session_state["sentiment_slider"]

def save_feedback(text, sentiment, score, actual_score):
    feedback = {
        "text": text,
        "sentiment": sentiment,
        "score": score,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "actual_sentiment_score": actual_score
    }
    feedback_file = "feedback_requests.json"
    ensure_file_exists(feedback_file)
    try:
        with open(feedback_file, "r") as f:
            feedback_list = json.load(f)
    except json.JSONDecodeError:
        feedback_list = []
    feedback_list.append(feedback)
    with open(feedback_file, "w") as f:
        json.dump(feedback_list, f, indent=2)
    return True

result_container = st.container()
feedback_container = st.container()
feedback_submitted = False

if "stage" not in st.session_state:
    st.session_state.stage = 0

def set_stage(i):
    st.session_state.stage = i


if st.session_state.stage == 0:
    if analyze_button and st.session_state["input_text"].strip():
        with st.spinner("Analyzing..."):
            try:
                response = requests.post("http://localhost:8000/analyze/", json={"sentence": st.session_state["input_text"]})
                if response.status_code == 200:
                    result = response.json()
                    score = result["score"]
                    score = score * 4
                    highlights = result["highlights"]
                    # Only keep the latest highlights
                    st.session_state["last_highlights"] = highlights
                    if "editable_highlights" in st.session_state:
                        del st.session_state["editable_highlights"]
                    # New: Multi-level sentiment classification
                    if score >= 8.0:
                        sentiment = "High Positive"
                        sentiment_color = "#21bf21"
                    elif score >= 7.0:
                        sentiment = "Medium Positive"
                        sentiment_color = "#4be04b"
                    elif score >= 6.0:
                        sentiment = "Low Positive"
                        sentiment_color = "#8ff78f"
                    elif score >= 5.0:
                        sentiment = "High Neutral"
                        sentiment_color = "#ffdc00"
                    elif score >= 4.5:
                        sentiment = "Medium Neutral"
                        sentiment_color = "#ffe066"
                    elif score >= 4.0:
                        sentiment = "Low Neutral"
                        sentiment_color = "#fff3b0"
                    elif score >= 3.0:
                        sentiment = "Low Negative"
                        sentiment_color = "#ffb3b3"
                    elif score >= 2.5:
                        sentiment = "Medium Negative"
                        sentiment_color = "#ff6666"
                    else:
                        sentiment = "High Negative"
                        sentiment_color = "#c00000"
                    st.session_state["last_user_input"] = st.session_state["input_text"]
                    st.session_state["last_sentiment"] = sentiment
                    st.session_state["last_score"] = score
                    st.session_state["last_highlights"] = highlights
                    st.markdown(f"**Sentiment Score:** {score}")
                    st.markdown(f'<span style="font-size:1.3em;font-weight:bold;color:{sentiment_color}">{sentiment}</span>', unsafe_allow_html=True)
                    st.markdown("**Word Importance:**")
                    highlighted = []
                    positive_sentiment_words = ["High Positive", "Medium Positive", "Low Positive"]
                    negative_sentiment_words = ["High Negative", "Medium Negative", "Low Negative"]
                    neutral_sentiment_words = ["High Neutral", "Medium Neutral", "Low Neutral"]
                    for h in highlights:
                        imp = float(h["importance"])
                        if sentiment in positive_sentiment_words:
                            color = f"rgba(0, 200, 0, {imp})"
                        elif sentiment in negative_sentiment_words:
                            color = f"rgba(200, 0, 0, {imp})"
                        elif sentiment in neutral_sentiment_words:
                            color = f"rgba(128, 128, 128, {imp})"
                        else:
                            color = f"rgba(180, 180, 180, {imp})"
                        highlighted.append(f'<span style="background-color:{color};padding:2px 4px;border-radius:4px">{h["word"]} <span style="font-size:0.9em;color:#333;opacity:0.7;">({imp:.2f})</span></span>')
                    st.markdown(" ".join(highlighted), unsafe_allow_html=True)
                    st.session_state["last_user_input"] = st.session_state["input_text"]
                    st.session_state["last_sentiment"] = sentiment
                    st.session_state["last_score"] = score
                    st.session_state["last_highlights"] = highlights
                    with feedback_container:
                        if st.button("What's wrong?",on_click=set_stage, args=[1], key="feedback_btn"):
                            st.session_state["actual_score"] = score
                else:
                    st.error(f"API Error: {response.status_code} - {response.text}")
            except Exception as e:
                st.error(f"Request failed: {e}")
    elif not st.session_state["input_text"].strip():
        st.info("Type your text and click Analyse.")

if st.session_state.stage == 1:
    with feedback_container:
        with result_container:
            positive_sentiment_words = ["High Positive", "Medium Positive", "Low Positive"]
            negative_sentiment_words = ["High Negative", "Medium Negative", "Low Negative"]
            neutral_sentiment_words = ["High Neutral", "Medium Neutral", "Low Neutral"]
            score = st.session_state["last_score"]
            sentiment = st.session_state["last_sentiment"]
            highlights = st.session_state["last_highlights"]
            if sentiment in positive_sentiment_words:
                sentiment_color = "#21bf21"
            elif sentiment in negative_sentiment_words:
                sentiment_color = "#ffdc00"
            else:
                sentiment_color = "#c00000"
            st.markdown(f"**Sentiment Score:** {score}")
            st.markdown(f'<span style="font-size:1.3em;font-weight:bold;color:{sentiment_color}">{sentiment}</span>', unsafe_allow_html=True)
            st.markdown("**Word Importance:**")
            
            highlighted = []
            for h in highlights:
                imp = float(h["importance"])
                if sentiment in positive_sentiment_words:
                    color = f"rgba(0, 200, 0, {imp})"
                elif sentiment in negative_sentiment_words:
                    color = f"rgba(200, 0, 0, {imp})"
                elif sentiment in neutral_sentiment_words:
                    color = f"rgba(128, 128, 128, {imp})"
                else:
                    color = f"rgba(180, 180, 180, {imp})"
                highlighted.append(f'<span style="background-color:{color};padding:2px 4px;border-radius:4px">{h["word"]} <span style="font-size:0.9em;color:#333;opacity:0.7;">({imp:.2f})</span></span>')
            st.markdown(" ".join(highlighted), unsafe_allow_html=True)
      
        st.markdown("**If the sentiment is wrong, please provide the actual sentiment score below (0 = extremely negative, 10 = extremely positive):**")
        sentiment_options = [
            "High Negative", "Medium Negative", "Low Negative",
            "Low Neutral", "Medium Neutral", "High Neutral",
            "Low Positive", "Medium Positive", "High Positive"
        ]
        selected_sentiment = st.radio("Change Sentiment Classification", sentiment_options, index=sentiment_options.index(st.session_state["last_sentiment"]), key="sentiment_classification_radio")
        # Editable word importance sliders
        if "editable_highlights" not in st.session_state:
            st.session_state["editable_highlights"] = [dict(word=h["word"], importance=float(h["importance"])) for h in st.session_state["last_highlights"]]
        st.markdown("**Adjust Word Importances:**")
        new_importances = []
        for idx, h in enumerate(st.session_state["editable_highlights"]):
            col_word, col_slider = st.columns([2,4])
            with col_word:
                st.markdown(f"<span style='font-size:1.1em'>{h['word']}</span>", unsafe_allow_html=True)
            with col_slider:
                imp = st.slider(f"Importance for {h['word']}", min_value=0.0, max_value=1.0, value=h["importance"], step=0.01, key=f"imp_slider_{idx}", label_visibility='hidden')
            new_importances.append(dict(word=h["word"], importance=imp))
        st.session_state["editable_highlights"] = new_importances
        # Score slider
        actual_score = st.slider("Actual Sentiment Score", min_value=0.0, max_value=10.0, value=st.session_state.get("actual_score", 1.25), step=0.01, key="sentiment_slider", label_visibility='hidden')
        st.session_state["actual_score"] = actual_score
        orig_col, new_col = st.columns([2,2])
        with orig_col:
            st.markdown(f"Original Score: <b>{st.session_state['last_score']}</b>", unsafe_allow_html=True)
        with new_col:
            st.markdown(f"New Score: <b>{st.session_state['actual_score']}</b>", unsafe_allow_html=True)
        user_comment = st.text_area("Comment (optional)", value=st.session_state.get("feedback_comment", ""), key="feedback_comment_area")
        can_use_data = st.checkbox("Can we use your data to improve our system?", value=st.session_state.get("can_use_data", False), key="can_use_data_checkbox")
        send_report = st.button("Send Report", key="send_report_btn")
        if send_report:
            save_feedback(
                st.session_state["last_user_input"],
                selected_sentiment,
                st.session_state["last_score"],
                st.session_state["actual_score"]
            )
            st.session_state["feedback_comment"] = user_comment
            st.session_state["can_use_data"] = can_use_data
            time.sleep(1)
            # st.switch_page("feedback_manager.py")
            with feedback_container:
                st.success("Thank you for your feedback!")
                time.sleep(3)
                set_stage(0)
                st.rerun()

            

    
        
        
            


