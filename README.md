# local.LLM.chat
Chatbots leveraging **LLMs** and **Gradio interface** that can save output to local disc.

## 통합 버전 (Unified Chat App)

**`unified_chat_app.py`** - 모든 기능을 하나로 통합한 최신 버전!

### 주요 기능
- **멀티 API 지원**: OpenAI(GPT-4 등)와 Anthropic(Claude) API를 선택해서 사용 가능
- **파일 업로드**: PDF, Markdown, CSV, TXT 파일 업로드 및 분석
- **파라미터 조정**: Temperature와 Max Tokens를 UI에서 직접 조정 가능
- **대화 저장**: JSON 또는 Markdown 형식 중 선택해서 저장
- **LangChain 기반**: LangChain 라이브러리를 사용한 안정적인 통합

### Notice
`root` 폴더에 `.env`파일 만들어 아래와 같이 api key를 입력해야 실행할 수 있습니다.
```
OPENAI_API_KEY=your_openai_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here
```

### 실행 방법
```bash
pip install -r requirements.txt
python unified_chat_app.py
```

---

## 기존 버전 (Legacy Files)

### output file type

- `*_json.py`는 결과물을 json으로 저장 (텍스트 생성시 유용)
- `*_md.py`는 결과물을 markdown으로 저장 (코드 생성시 유용)

코드 실행시 `root` 폴더에 `_output_모델명` 폴더가 자동 생성되어 채팅 결과가 저장됩니다.

### Model option 지정 및 저장
`# 모델 초기화` 블록에서 TEMPERATURE 와 MODEL_NAME 을 지정할 수 있고, 지정된 파라미터는 결과 파일에 메타 데이터로 함께 저장 됩니다. 

혹시 내 api-key로 사용 가능한 모든 모델의 리스트가 궁금할 때에는 `.ipynb` 파일에서 `# Retrieve the list of available models` 블록을 주석 해제해서 불러올 수 있습니다 

### System prompt 관련 업데이트
0710버전부터 system message submit button 이 추가되어 시스템 메시지 반영 및 저장에 누락이 없게 되었습니다. 
submit button 을 누르지 않을 경우에는 반영 및 저장이 원활치 않습니다. (되다 안되다 합니다. 정확한 이유는 아직 모름)

### 채팅 삭제 관련
채팅 삭제 버튼이 채팅 화면에서는 적용되지만, 저장시에는 삭제한 채팅까지 저장됩니다. 
chat history 에서 챗을 삭제하는 기능은 현재로서는 고려하지 않습니다. 

