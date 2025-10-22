import os
import uuid
import json
from datetime import datetime
import gradio as gr
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain.schema import SystemMessage, HumanMessage, AIMessage
import pandas as pd
import PyPDF2
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Global variable to maintain entire chat history
global_chat_history = {
    "meta": {},
    "prompts": []
}

def get_current_time():
    """Return current time in yyyymmdd_hhmmss format"""
    return datetime.now().strftime("%Y%m%d_%H%M%S")

def read_pdf(file_path):
    """Extract text from PDF file"""
    with open(file_path, 'rb') as file:
        pdf_reader = PyPDF2.PdfReader(file)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
    return text

def read_csv(file_path):
    """Convert CSV to string format"""
    df = pd.read_csv(file_path)
    return df.to_string()

def read_markdown(file_path):
    """Read markdown file"""
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()

def read_text(file_path):
    """Read text file"""
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()

def process_uploaded_file(file):
    """Process uploaded file based on its extension"""
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
        elif file_ext == '.md':
            content = read_markdown(file.name)
            return content, file.name
        elif file_ext == '.txt':
            content = read_text(file.name)
            return content, file.name
        else:
            return f"Unsupported file type: {file_ext}", None
    except Exception as e:
        return f"Error processing file: {str(e)}", None

def save_chat_history_to_json(session_id, api_provider):
    """Save chat history as JSON file"""
    output_directory = f"_output_{api_provider}"
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)

    timestamp = get_current_time()
    file_name = f"{timestamp}_{session_id}.json"
    file_path = os.path.join(output_directory, file_name)

    with open(file_path, 'w', encoding='utf-8') as file:
        json.dump(global_chat_history, file, ensure_ascii=False, indent=2)

    print(f"Chat history saved to {file_path}")
    return f"Chat history saved to {file_path}"

def save_chat_history_to_markdown(session_id, api_provider):
    """Save chat history as Markdown file"""
    output_directory = f"_output_{api_provider}"
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)

    timestamp = get_current_time()
    file_name = f"{timestamp}_{session_id}.md"
    file_path = os.path.join(output_directory, file_name)

    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(f"# Chat History\n\n")
        file.write(f"**Model**: {global_chat_history['meta'].get('model', 'N/A')}\n\n")
        file.write(f"**Temperature**: {global_chat_history['meta'].get('temperature', 'N/A')}\n\n")
        file.write(f"**Max Tokens**: {global_chat_history['meta'].get('max_tokens', 'N/A')}\n\n")

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
                    if file_end == -1:
                        filename = message[file_start:]
                        question = ""
                    else:
                        filename = message[file_start:file_end]
                        question_start = message.find("My question about this content is: ")
                        if question_start != -1:
                            question_start += len("My question about this content is: ")
                            question = message[question_start:]
                        else:
                            question = ""

                    # Format the message with just filename and question
                    if question:
                        message = f"Uploaded file: {filename}\nQuestion: {question}"
                    else:
                        message = f"Uploaded file: {filename}"

                file.write(f"{message}\n\n")
                file.write(f"### Bot Response\n")
                file.write(f"**Time**: {entry['bot_response_time']}\n\n")
                file.write(f"{entry['bot_response']}\n\n")
                file.write(f"---\n\n")

    print(f"Chat history saved to {file_path}")
    return f"Chat history saved to {file_path}"

def get_llm(api_provider, model_name, temperature, max_tokens):
    """Initialize and return the appropriate LLM based on API provider"""
    if api_provider == "OpenAI":
        return ChatOpenAI(
            api_key=os.getenv("OPENAI_API_KEY"),
            model=model_name,
            temperature=temperature,
            max_tokens=max_tokens
        )
    else:  # Anthropic
        return ChatAnthropic(
            api_key=os.getenv("ANTHROPIC_API_KEY"),
            model=model_name,
            temperature=temperature,
            max_tokens=max_tokens
        )

def response(message, history, system_message, api_provider, model_name, temperature, max_tokens, file_data=None):
    """Get response from the selected LLM"""
    # Update global chat history metadata
    global_chat_history["meta"] = {
        "api_provider": api_provider,
        "model": model_name,
        "temperature": temperature,
        "max_tokens": max_tokens
    }

    # Initialize LLM
    llm = get_llm(api_provider, model_name, temperature, max_tokens)

    # Build message history
    history_langchain_format = [SystemMessage(content=system_message)]
    for human, ai in history:
        history_langchain_format.append(HumanMessage(content=human))
        history_langchain_format.append(AIMessage(content=ai))

    # If there's file content, add it to the message with filename
    if isinstance(file_data, tuple) and file_data[0] and file_data[1]:
        file_content, filename = file_data
        message = f"Here's the content of the uploaded file:\nUploaded file: {filename}\n\n{file_content}\n\nMy question about this content is: {message}"

    history_langchain_format.append(HumanMessage(content=message))

    # Get response from LLM
    llm_response = llm.invoke(history_langchain_format)

    user_message_time = get_current_time()
    bot_response_time = get_current_time()

    # Add to global chat history
    if not global_chat_history["prompts"] or global_chat_history["prompts"][-1]["prompt"] != system_message:
        global_chat_history["prompts"].append({
            "prompt": system_message,
            "history": []
        })

    global_chat_history["prompts"][-1]["history"].append({
        "user_message": message,
        "user_message_time": user_message_time,
        "bot_response": llm_response.content,
        "bot_response_time": bot_response_time
    })

    return llm_response.content

def generate_session_id():
    """Generate a unique session ID"""
    return str(uuid.uuid4())

# Gradio UI setup
with gr.Blocks(title="Unified LLM Chat") as demo:
    gr.Markdown("# Unified LLM Chat Interface")
    gr.Markdown("Chat with OpenAI or Anthropic models with file upload support")

    with gr.Row():
        session_id_input = gr.Textbox(
            value=generate_session_id(),
            label="Session ID",
            placeholder="Enter your session ID",
            scale=2
        )
        api_provider = gr.Dropdown(
            choices=["OpenAI", "Anthropic"],
            value="OpenAI",
            label="API Provider",
            scale=1
        )

    with gr.Row():
        model_name = gr.Textbox(
            value="gpt-4o",
            label="Model Name",
            placeholder="e.g., gpt-4o or claude-sonnet-4-20250514",
            scale=2
        )
        temperature = gr.Slider(
            minimum=0,
            maximum=2,
            value=0.7,
            step=0.1,
            label="Temperature",
            scale=1
        )
        max_tokens = gr.Slider(
            minimum=100,
            maximum=8000,
            value=4000,
            step=100,
            label="Max Tokens",
            scale=1
        )

    chatbot = gr.Chatbot(height=500, autoscroll=True)

    with gr.Row():
        msg = gr.Textbox(
            placeholder="Enter your message here",
            container=False,
            scale=7
        )
        submit_message_button = gr.Button("Submit", scale=1)

    with gr.Row():
        file_upload = gr.File(
            label="Upload File (PDF, MD, CSV, TXT)",
            file_types=[".pdf", ".md", ".csv", ".txt"],
            scale=2
        )
        system_prompt = gr.Textbox(
            "",
            label="System Prompt",
            placeholder="Enter system prompt (optional)",
            scale=5
        )
        update_system_button = gr.Button("Update System Prompt", scale=1)

    with gr.Row():
        save_format = gr.Dropdown(
            choices=["Markdown", "JSON"],
            value="Markdown",
            label="Save Format",
            scale=1
        )
        save_button = gr.Button("Save Chat History", scale=1)
        save_status = gr.Textbox(label="Save Status", scale=2, interactive=False)

    with gr.Row():
        delete_last_button = gr.Button("Delete Last Message ❌")
        clear_chat_button = gr.Button("Clear Chat 💫")

    # States
    state = gr.State(value="")  # System prompt state
    file_data = gr.State(value=None)  # File content state

    # Helper functions
    def submit_message_with_file(message, history, session_id, system_message, api_prov, model, temp, max_tok, current_file_data):
        response_text = response(message, history, system_message, api_prov, model, temp, max_tok, current_file_data)
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
        return new_prompt

    def save_chat(session_id, save_fmt, api_prov):
        if save_fmt == "JSON":
            return save_chat_history_to_json(session_id, api_prov)
        else:
            return save_chat_history_to_markdown(session_id, api_prov)

    def update_model_suggestion(api_prov):
        """Update model name suggestion based on API provider"""
        if api_prov == "OpenAI":
            return "gpt-4o"
        else:
            return "claude-sonnet-4-20250514"

    # Event handlers
    msg.submit(
        submit_message_with_file,
        [msg, chatbot, session_id_input, state, api_provider, model_name, temperature, max_tokens, file_data],
        [chatbot, msg, file_data]
    )
    submit_message_button.click(
        submit_message_with_file,
        inputs=[msg, chatbot, session_id_input, state, api_provider, model_name, temperature, max_tokens, file_data],
        outputs=[chatbot, msg, file_data]
    )
    update_system_button.click(update_system_message, inputs=system_prompt, outputs=state)
    save_button.click(save_chat, inputs=[session_id_input, save_format, api_provider], outputs=save_status)
    file_upload.change(handle_file_upload, inputs=[file_upload], outputs=[file_data])
    delete_last_button.click(fn=delete_last_chat, inputs=chatbot, outputs=chatbot)
    clear_chat_button.click(fn=lambda: [], inputs=None, outputs=chatbot)
    api_provider.change(update_model_suggestion, inputs=[api_provider], outputs=[model_name])

if __name__ == "__main__":
    demo.launch(share=True)
