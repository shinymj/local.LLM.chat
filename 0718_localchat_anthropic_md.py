import os
import uuid
from datetime import datetime
import gradio as gr
from anthropic import Anthropic

# Initialize Anthropic client
client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

# Set model parameters
TEMPERATURE = 0
MODEL_NAME = 'claude-3-5-sonnet-20240620'

# Global variable to maintain entire chat history
global_chat_history = {
    "meta": {
        "temperature": TEMPERATURE,
        "model": MODEL_NAME
    },
    "prompts": []
}

# Function to return current time in yyyymmdd_hhmmss format
def get_current_time():
    return datetime.now().strftime("%Y%m%d_%H%M%S")

# Function to save chat history as a markdown file (called on button click)
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
                file.write(f"{entry['user_message']}\n\n")
                file.write(f"### Bot Response\n")
                file.write(f"**Time**: {entry['bot_response_time']}\n\n")
                file.write(f"{entry['bot_response']}\n\n")
                file.write(f"---\n\n")
    
    print(f"Chat history saved to {file_path}")
    return f"Chat history saved to {file_path}"

# Function to get response from Claude using Anthropic API
def response(message, history, system_message):
    messages = []
    for human, ai in history:
        messages.append({"role": "user", "content": human})
        messages.append({"role": "assistant", "content": ai})
    messages.append({"role": "user", "content": message})
    
    response = client.messages.create(
        model=MODEL_NAME,
        messages=messages,
        system=system_message,  
        temperature=TEMPERATURE,
        max_tokens=1000
    )
    
    claude_response = response.content[0].text
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
        "bot_response": claude_response,
        "bot_response_time": bot_response_time
    })
    
    return claude_response

# Function to generate session ID
def generate_session_id():
    return str(uuid.uuid4())

# Gradio UI setup and execution
with gr.Blocks() as demo:
    gr.Markdown("# Chat with Claude")
    session_id_input = gr.Textbox(value=generate_session_id(), label="Session ID", placeholder="Enter your session ID")
    chatbot = gr.Chatbot(height=500)
    
    with gr.Row():
        msg = gr.Textbox(placeholder="Enter your message here", container=False, scale=7)
        submit_message_button = gr.Button("Submit")
    
    with gr.Row():
        additional_input = gr.Textbox("", label="System Prompt", placeholder="", scale=7)
        update_system_button = gr.Button("Submit")
    
    save_button = gr.Button("Save Anthropic Chat History as Markdown")

    state = gr.State(value="")  # Initial system prompt state

    def submit_message(message, history, session_id, system_message):
        response_text = response(message, history, system_message)
        history.append((message, response_text))
        return history, ""
    
    def delete_last_chat(chat_history):
        if len(chat_history) > 0:
            chat_history.pop()
        return chat_history

    def update_system_message(new_prompt):
        state.value = new_prompt
        return new_prompt

    def save_chat(session_id):
        return save_chat_history_to_markdown(session_id)

    # Enable submitting message with Enter key
    msg.submit(submit_message, [msg, chatbot, session_id_input, state], [chatbot, msg])
    submit_message_button.click(submit_message, inputs=[msg, chatbot, session_id_input, state], outputs=[chatbot, msg])
    update_system_button.click(update_system_message, inputs=additional_input, outputs=state)
    save_button.click(save_chat, inputs=[session_id_input], outputs=None)

    gr.Button("Delete Last Message ❌").click(fn=delete_last_chat, inputs=chatbot, outputs=chatbot)
    gr.Button("Clear Chat 💫").click(fn=lambda: [], inputs=None, outputs=chatbot)

demo.launch(share=True)
