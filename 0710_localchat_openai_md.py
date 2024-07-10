import os
import uuid
from datetime import datetime
import gradio as gr
from langchain_openai import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage, AIMessage

# 환경 변수에서 OpenAI API 키를 읽어옴
openai_api_key = os.getenv("OPENAI_API_KEY")

# Langchain GPT-4 모델 초기화
TEMPERATURE = 0
MODEL_NAME = 'gpt-4o'
llm = ChatOpenAI(api_key=openai_api_key, temperature=TEMPERATURE, model=MODEL_NAME)

# 전체 대화 기록을 유지할 전역 변수
global_chat_history = {
    "meta": {
        "temperature": TEMPERATURE,
        "model": MODEL_NAME
    },
    "prompts": []
}

# 현재 시간을 yyyymmdd_hhmmss 형식으로 반환하는 함수
def get_current_time():
    return datetime.now().strftime("%Y%m%d_%H%M%S")

# 로컬에 대화 기록을 마크다운 파일로 저장하는 함수 (버튼 클릭 시 호출)
def save_chat_history_to_markdown(session_id):
    output_directory = "_output_OpenAI"
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

# Gradio에서 유저의 질문과 채팅기록을 받아 GPT-4의 대답을 리턴하는 함수
def response(message, history, system_message):
    history_langchain_format = [SystemMessage(content=system_message)]
    for human, ai in history:
        history_langchain_format.append(HumanMessage(content=human))
        history_langchain_format.append(AIMessage(content=ai))
    history_langchain_format.append(HumanMessage(content=message))
    gpt_response = llm.invoke(history_langchain_format)
    user_message_time = get_current_time()
    bot_response_time = get_current_time()
    
    # 글로벌 대화 기록에 추가
    if not global_chat_history["prompts"] or global_chat_history["prompts"][-1]["prompt"] != system_message:
        global_chat_history["prompts"].append({
            "prompt": system_message,
            "history": []
        })
    
    global_chat_history["prompts"][-1]["history"].append({
        "user_message": message,
        "user_message_time": user_message_time,
        "bot_response": gpt_response.content,
        "bot_response_time": bot_response_time
    })
    
    return gpt_response.content

# Gradio 세션 관리 함수
def generate_session_id():
    return str(uuid.uuid4())

# Gradio UI 설정 및 실행
with gr.Blocks() as demo:
    session_id_input = gr.Textbox(value=generate_session_id(), label="Session ID", placeholder="Enter your session ID")
    chatbot = gr.Chatbot(height=500)
    
    with gr.Row():
        msg = gr.Textbox(placeholder="User Message를 입력해 주세요", container=False, scale=7)
        submit_message_button = gr.Button("Submit")
    
    with gr.Row():
        additional_input = gr.Textbox("", label="System Prompt", placeholder="", scale=7)
        update_system_button = gr.Button("Submit")
    
    save_button = gr.Button("대화 기록 마크다운 파일로 저장")

    state = gr.State(value="")  # 초기 시스템 프롬프트 상태

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

    # User message 입력창에서 엔터키로도 메시지를 제출할 수 있도록 설정
    msg.submit(submit_message, [msg, chatbot, session_id_input, state], [chatbot, msg])
    submit_message_button.click(submit_message, inputs=[msg, chatbot, session_id_input, state], outputs=[chatbot, msg])
    update_system_button.click(update_system_message, inputs=additional_input, outputs=state)
    save_button.click(save_chat, inputs=[session_id_input], outputs=None)

    gr.Button("이전챗 삭제 ❌").click(fn=delete_last_chat, inputs=chatbot, outputs=chatbot)
    gr.Button("전챗 삭제 💫").click(fn=lambda: [], inputs=None, outputs=chatbot)

demo.launch(share=True)
