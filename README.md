# local.LLM.chat
Chatbots leveraging **LLMs** and **Gradio interface** that can save output to local disc.\
조만간 LLM 종류를 늘려나갈 예정입니다. 

### Notice
`root` 폴더에 `.env`파일 만들어 아래와 같이 api key를 입력해야 실행할 수 있습니다. 
```
openai_api_key = "YOUR OPENAI KEY"
```


### output file type

- `*_json.ipynb`는 결과물을 json으로 저장 (텍스트 생성시 유용)
- `*_md.ipynb`는 결과물을 markdown으로 저장 (코드 생성시 유용)

코드 실행시 `root` 폴더에 `_output_모델명` 폴더가 자동 생성되어 채팅 결과가 저장됩니다.

### Model option 지정 및 저장
`# 모델 초기화` 블록에서 TEMPERATURE 와 MODEL_NAME 을 지정할 수 있고, 지정된 파라미터는 결과 파일에 메타 데이터로 함께 저장 됩니다. 

혹시 내 api-key로 사용 가능한 모든 모델의 리스트가 궁금할 때에는 `# Retrieve the list of available models` 블록을 주석 해제 해서 불러올 수 있습니다 

### System prompt 관련 주의점
혹시 사용 중간에 System prompt를 수정하는 경우 수정이 바로 반영되지 않는 경우가 있는데, 이유는 잘 모르겠습니다. \
대화 내용 저장시 System prompt 변경 내용이 반영되어 저장 됩니다.

### 채팅 삭제 관련
채팅 삭제는 화면에서는 적용되지만, 저장할 때는 삭제한 체팅까지 저장됩니다. 

