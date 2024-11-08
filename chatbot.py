import os
import glob
from langchain_community.document_loaders import TextLoader
from langchain_community.document_loaders.csv_loader import CSVLoader #csvloader    
#from langchain_community.document_loaders import DirectoryLoader #directoryloader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
from langchain_community.vectorstores import Chroma
import dotenv
import streamlit as st
import time

# 환경 변수 로드
dotenv.load_dotenv()

def load_faq_documents():
    faq_data = []

    # FAQ텍스트 파일 로드
    txt_paths = glob.glob("./files/faq/*.txt")  # FAQ 폴더 내의 텍스트 파일들
    for txt_path in txt_paths:
        loader = TextLoader(file_path=txt_path,encoding='utf-8')
        txt_data = loader.load()
        faq_data.extend(txt_data)  # FAQ 데이터를 리스트에 추가
        print(f"{txt_path} 텍스트 로딩 완료 - 문서 수: {len(txt_data)}")

        print("faq 파일 로딩 완료")
        
    return faq_data
# 텍스트 파일 로드
def load_knowledge_base():
   all_data = []
   try:
       # 디렉토리 내 모든 CSV 파일 경로 가져오기
       file_paths = glob.glob("./files/check/*.csv")
       
       # 각 CSV 파일을 로드하여 데이터 합치기
       for file_path in file_paths:
           loader = CSVLoader(file_path=file_path, encoding='utf-8')
           data = loader.load()
           all_data.extend(data)  # 데이터 추가
           print(f"{file_path} 데이터 로딩 완료 - 문서 수: {len(data)}")
        
       print("모든 CSV 파일 로딩 완료")
       print(f"총 로드된 문서 수: {len(all_data)}")
       return all_data
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
     #1. 카드 데이터 및 FAQ 데이터 로드
    # data = load_knowledge_base()  # csv 데이터 로드
    faq_data = load_faq_documents()  # FAQ 데이터 로드
    # # 카드 및 FAQ 데이터를 하나의 리스트로 결합
    # all_data = data + faq_data  # 데이터 결합
    # if not all_data:
    #     raise ValueError("문서 로딩에 실패했습니다.")

    # # 2. 문서 분할
    all_splits = split_documents(faq_data)
    if not faq_data:
        raise ValueError("문서 분할에 실패했습니다.")

    # 3. 벡터 저장소 생성 및 로드
    openai = OpenAIEmbeddings(openai_api_key=os.getenv("OPENAI_API_KEY"))

    # # 분할된 모든 데이터로부터 벡터 저장소 생성
    vectorstore = Chroma.from_documents(
        documents=faq_data, 
        embedding=openai, 
        persist_directory="vectorstore_db"
    )
    
    #벡터 저장소 생성 및 로드
    # vectorstore = Chroma(
    #     persist_directory="vectorstore_db", 
    #     embedding_function=openai
    # )
    retriever = vectorstore.as_retriever()

# 저장된 모든 문서와 메타데이터 가져오기
    all_data = vectorstore.get()
    for doc in all_data["documents"]:
        print("Document:", doc)

    for meta in all_data["metadatas"]:
        print("Metadata:", meta)

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
