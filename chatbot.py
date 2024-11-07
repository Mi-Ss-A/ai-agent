import os
#from langchain_community.document_loaders import TextLoader
from langchain_community.document_loaders.csv_loader import CSVLoader #csvloader    
#from langchain_community.document_loaders import DirectoryLoader #directoryloader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
import dotenv
import streamlit as st
import time

# 환경 변수 로드
dotenv.load_dotenv()

# 텍스트 파일 로드
def load_knowledge_base():
    try:
        loader = CSVLoader(file_path="./files/card_info.csv", encoding='utf-8')
        data = loader.load()
        print("데이터 로딩 완료")
        print(f"로드된 문서의 수: {len(data)}")
        for i in range(len(data)):
            print(f"\n[{i}번 문서 내용]\n{data[i].page_content[800:900]}")
        return data
    except Exception as e:
        print(f"로딩 중 에러 발생: {e}")
        return None


# 텍스트 분할
def split_documents(data, chunk_size=500):
    if not data:
        return None
    
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=50
    )
    try:
        all_splits = text_splitter.split_documents(data)
        print(f"분할된 청크 수: {len(all_splits)}")
        return all_splits
    except Exception as e:
        print(f"분할 중 에러 발생: {e}")
        return None

# 에이전트 생성 함수
def create_agent(llm, tools, memory_key="history"):
    from langchain.agents import create_openai_functions_agent
    from langchain.agents.openai_functions_agent.base import OpenAIFunctionsAgent
    from langchain.schema.messages import SystemMessage
    from langchain.prompts import PromptTemplate,MessagesPlaceholder
    from langchain.agents.openai_functions_agent.agent_token_buffer_memory import AgentTokenBufferMemory
    from langchain.agents import AgentExecutor

    # 시스템 메시지 및 프롬프트 설정
    system_message = SystemMessage(
        content=(
            "You are a helpful and knowledgeable financial assistant that provides detailed information about Woori Bank's financial products. "
            "Your task is to assist users with inquiries related to Woori Bank's products and services, including credit cards, loans, and savings accounts. "
            "Answer questions about specific products with details such as benefits, fees, eligibility, and other important information. "
            "If the user asks about products or services from other banks, politely inform them that you only provide information about Woori Bank. "
            "If the information is not available in your knowledge base, tell the user that you cannot answer their question. "
            "Make sure to answer all questions in Korean. "
            "If you do not know the answer, say '저는 그에 대한 정보를 알지 못합니다.'"
            "Please explain each item in paragraphs."
        )
    )

    prompt = OpenAIFunctionsAgent.create_prompt(
        system_message=system_message,
        extra_prompt_messages=[MessagesPlaceholder(variable_name=memory_key)],
    )
    # 에이전트 및 실행기 생성
    agent = create_openai_functions_agent(llm=llm, tools=tools, prompt=prompt)
    
    return AgentExecutor(
        agent=agent,
        tools=tools,
        memory=AgentTokenBufferMemory(memory_key=memory_key, llm=llm),
        verbose=True,
        return_intermediate_steps=True,
    )

# 메인 실행 부분
def main():
    # 1. 데이터 로드
    data = load_knowledge_base()
    if not data:
        raise ValueError("문서 로딩에 실패했습니다.")

    # 2. 문서 분할
    all_splits = split_documents(data)
    if not all_splits:
        raise ValueError("문서 분할에 실패했습니다.")

    # 3. 벡터 저장소 생성
    openai = OpenAIEmbeddings(openai_api_key=os.getenv("OPENAI_API_KEY"))
    vectorstore = Chroma.from_documents(documents=all_splits, embedding=openai, persist_directory="vectorstore_db")
    retriever = vectorstore.as_retriever()

    # 4. 검색 도구 생성
    from langchain.agents.agent_toolkits import create_retriever_tool
    tool = create_retriever_tool(
        retriever,
        "wibee_ChatBot",
        "Searches and returns information regarding the financial service guide.",
    )
    tools = [tool]

    # 5. ChatGPT 모델 설정
    from langchain_openai import ChatOpenAI
    llm = ChatOpenAI(temperature=0)

    # 6. 에이전트 실행기 생성
    agent_executor = create_agent(llm, tools)

    # 7. Streamlit UI 설정
    st.title("WiBee")

    if "openai_model" not in st.session_state:
        st.session_state["openai_model"] = "gpt-3.5-turbo"

    if "messages" not in st.session_state:
        st.session_state.messages = []

    # 이전 메시지 표시
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # 새 메시지 입력 및 처리
    if prompt := st.chat_input("무엇을 도와드릴까요?"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            full_response = ""

            result = agent_executor({"input": prompt})
            for chunk in result['output'].split():
                full_response += chunk + " "
                   # 조건에 따라 줄바꿈 추가
                if chunk.endswith((":","다.", "!", "?")):  # 문장이 끝날 때 줄바꿈 추가
                    full_response += "\n\n"
                time.sleep(0.05)
                message_placeholder.markdown(full_response + "▌")
            message_placeholder.markdown(full_response)
        st.session_state.messages.append({"role": "assistant", "content": full_response})

if __name__ == "__main__":
    main()
