import os
import uuid
from datetime import datetime
import gradio as gr
from anthropic import Anthropic
import pandas as pd
import PyPDF2
import io

# Initialize Anthropic client
client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

# Set model parameters
TEMPERATURE = 0
MODEL_NAME = 'claude-3-5-sonnet-20240620'
MAX_TOKENS = 4000

# Global variable to maintain entire chat history
global_chat_history = {
    "meta": {
        "temperature": TEMPERATURE,
        "model": MODEL_NAME,
        "max_tokens": MAX_TOKENS
    },
    "prompts": []
}

def get_current_time():
    return datetime.now().strftime("%Y%m%d_%H%M%S")

def read_pdf(file):
    pdf_reader = PyPDF2.PdfReader(file)
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text() + "\n"
    return text

def read_csv(file):
    df = pd.read_csv(file)
    return df.to_string()

def process_uploaded_file(file):
    if file is None:
        return None, None
    
    file_ext = os.path.splitext(file.name)[1].lower()
    
    try:
        if file_ext == '.pdf':
            content = read_pdf(file.name)
            return content, file.name
        elif file_ext == '.csv':
            content = read_csv(file.name)
            return content, file.name
        else:
            return f"Unsupported file type: {file_ext}", None
    except Exception as e:
        return f"Error processing file: {str(e)}", None

def save_chat_history_to_markdown(session_id):
    output_directory = "_output_Anthropic"
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)
    
    timestamp = get_current_time()
    file_name = f"{timestamp}_{session_id}.md"
    file_path = os.path.join(output_directory, file_name)

    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(f"# Chat History\n\n")
        file.write(f"**Model**: {MODEL_NAME}\n\n")
        file.write(f"**Temperature**: {TEMPERATURE}\n\n")

        for i, prompt in enumerate(global_chat_history["prompts"]):
            file.write(f"## Prompt {i+1}\n")
            file.write(f"{prompt['prompt']}\n\n")
            for entry in prompt["history"]:
                file.write(f"### User Message\n")
                file.write(f"**Time**: {entry['user_message_time']}\n\n")
                
                # Clean up the message for markdown file
                message = entry['user_message']
                if "Here's the content of the uploaded file:" in message:
                    # Extract the filename and question
                    file_start = message.find("Uploaded file: ") + len("Uploaded file: ")
                    file_end = message.find("\n", file_start)
                    filename = message[file_start:file_end]
                    
                    question_start = message.find("My question about this content is: ") + len("My question about this content is: ")
                    question = message[question_start:]
                    
                    # Format the message with just filename and question
                    message = f"Uploaded file: {filename}\nQuestion: {question}"
                
                file.write(f"{message}\n\n")
                file.write(f"### Bot Response\n")
                file.write(f"**Time**: {entry['bot_response_time']}\n\n")
                file.write(f"{entry['bot_response']}\n\n")
                file.write(f"---\n\n")
    
    print(f"Chat history saved to {file_path}")
    return f"Chat history saved to {file_path}"

def response(message, history, system_message, file_data=None):
    messages = []
    for human, ai in history:
        messages.append({"role": "user", "content": human})
        messages.append({"role": "assistant", "content": ai})
    
    # If there's file content, add it to the message with filename
    if isinstance(file_data, tuple) and file_data[0] and file_data[1]:
        file_content, filename = file_data
        message = f"Here's the content of the uploaded file:\nUploaded file: {filename}\n\n{file_content}\n\nMy question about this content is: {message}"
    
    messages.append({"role": "user", "content": message})
    
    response = client.messages.create(
        model=MODEL_NAME,
        messages=messages,
        system=system_message,
        temperature=TEMPERATURE,
        max_tokens=MAX_TOKENS
    )
    
    claude_response = response.content[0].text
    user_message_time = get_current_time()
    bot_response_time = get_current_time()
    
    if not global_chat_history["prompts"] or global_chat_history["prompts"][-1]["prompt"] != system_message:
        global_chat_history["prompts"].append({
            "prompt": system_message,
            "history": []
        })
    
    global_chat_history["prompts"][-1]["history"].append({
        "user_message": message,
        "user_message_time": user_message_time,
        "bot_response": claude_response,
        "bot_response_time": bot_response_time
    })
    
    return claude_response

def generate_session_id():
    return str(uuid.uuid4())

# Gradio UI setup and execution
with gr.Blocks() as demo:
    gr.Markdown("# Chat with Claude")
    session_id_input = gr.Textbox(value=generate_session_id(), label="Session ID", placeholder="Enter your session ID")
    chatbot = gr.Chatbot(height=500, autoscroll=True)
    
    with gr.Row():
        msg = gr.Textbox(placeholder="Enter your message here", container=False, scale=7)
        submit_message_button = gr.Button("Submit")
    
    with gr.Row():
        file_upload = gr.File(label="Upload PDF or CSV file", file_types=[".pdf", ".csv"])
        system_prompt = gr.Textbox("", label="System Prompt", placeholder="", scale=7)
        update_system_button = gr.Button("Update System Prompt")
    
    save_button = gr.Button("Save Anthropic Chat History as Markdown")

    state = gr.State(value="")  # Initial system prompt state
    file_data = gr.State(value=None)  # State to store file content and filename

    def submit_message_with_file(message, history, session_id, system_message, current_file_data):
        response_text = response(message, history, system_message, current_file_data)
        history.append((message, response_text))
        return history, "", current_file_data

    def handle_file_upload(file):
        if file is None:
            return None
        content, filename = process_uploaded_file(file)
        return (content, filename) if content and filename else None

    def delete_last_chat(chat_history):
        if len(chat_history) > 0:
            chat_history.pop()
        return chat_history

    def update_system_message(new_prompt):
        state.value = new_prompt
        return new_prompt

    def save_chat(session_id):
        return save_chat_history_to_markdown(session_id)

    # Event handlers
    msg.submit(submit_message_with_file, [msg, chatbot, session_id_input, state, file_data], [chatbot, msg, file_data])
    submit_message_button.click(submit_message_with_file, inputs=[msg, chatbot, session_id_input, state, file_data], outputs=[chatbot, msg, file_data])
    update_system_button.click(update_system_message, inputs=system_prompt, outputs=state)
    save_button.click(save_chat, inputs=[session_id_input], outputs=None)
    file_upload.change(handle_file_upload, inputs=[file_upload], outputs=[file_data])

    gr.Button("Delete Last Message ❌").click(fn=delete_last_chat, inputs=chatbot, outputs=chatbot)
    gr.Button("Clear Chat 💫").click(fn=lambda: [], inputs=None, outputs=chatbot)

demo.launch(share=True)