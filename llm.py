from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_upstage import UpstageEmbeddings, ChatUpstage 
from langchain_pinecone import PineconeVectorStore
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder, FewShotChatMessagePromptTemplate
from langchain.chains import create_history_aware_retriever, create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
from config import answer_examples
import os

store = {}
llm_model = 'OpenAI'

def get_session_history(session_id: str) -> BaseChatMessageHistory:
    if session_id not in store:
        store[session_id] = ChatMessageHistory()
    return store[session_id]

def get_history_retriever():
    llm = get_llm()
    retriever = get_retriever()

    contextualize_q_system_prompt = (
        "Given a chat history and the latest user question, "
        "rephrase the question to make it standalone without the context of the history. "
        "Do NOT answer the question, just reformulate it if necessary."
    )

    contextualize_q_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", contextualize_q_system_prompt),
            MessagesPlaceholder("chat_history"),
            ("human", "{input}"),
        ]
    )
    history_aware_retriever = create_history_aware_retriever(
        llm, retriever, contextualize_q_prompt
    )
    return history_aware_retriever

def get_llm():
    if llm_model == 'OpenAI':
        return ChatOpenAI(model='gpt-4o')
    elif llm_model == 'Upstage':
        upstage_api_key = os.getenv("UPSTAGE_API_KEY")
        return ChatUpstage(api_key=upstage_api_key)
    else:
        raise ValueError("Invalid provider selected.")

def get_retriever():
    if llm_model == 'OpenAI':
        embedding = OpenAIEmbeddings(model='text-embedding-3-large')
        index_name = 'unity-game-development'
    elif llm_model == 'Upstage':
        embedding = UpstageEmbeddings(model='solar-embedding-1-large')
        index_name = 'unity-game-development-upstage'
    else:
        raise ValueError("Choose 'OpenAI' or 'Upstage' as model source.")

    database = PineconeVectorStore.from_existing_index(index_name=index_name, embedding=embedding)
    retriever = database.as_retriever(search_kwargs={'k': 4})
    return retriever

def get_dictionary_chain():
    if llm_model == 'OpenAI':
        dictionary = ["Player -> Game Developer Terminology"]
    elif llm_model == 'Upstage':
        dictionary = []

    llm = get_llm()
    prompt = ChatPromptTemplate.from_template(f"""
        Based on the user's question, refer to our dictionary to adjust the terminology if needed.
        If no changes are necessary, return the question as is.
        Dictionary : {dictionary}
        
        Question: {{question}} 
    """)
    dictionary_chain = prompt | llm | StrOutputParser()
    return dictionary_chain

def few_shot():
    example_prompt = ChatPromptTemplate.from_messages(
        [
            ("human", "{input}"),
            ("ai", "{answer}"),
        ]
    )
    few_shot_prompt = FewShotChatMessagePromptTemplate(
        example_prompt=example_prompt,
        examples=answer_examples,
    )
    return few_shot_prompt

def get_rag_chain():
    llm = get_llm()

    system_prompt = (
        "You are an expert in Unity game development. "
        "When providing responses, base them on 'Unity Game Development in 24 Hours'. "
        "If unsure, respond with 'I don't know'. Keep responses concise and to the point."
        "\n\n"
        "{context}"
    )
    few_shot_prompt = few_shot()
    qa_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            few_shot_prompt,
            MessagesPlaceholder("chat_history"),
            ("human", "{input}"),
        ]
    )
    history_aware_retriever = get_history_retriever()
    question_answer_chain = create_stuff_documents_chain(llm, qa_prompt)
    rag_chain = create_retrieval_chain(history_aware_retriever, question_answer_chain)

    conversational_rag_chain = RunnableWithMessageHistory(
        rag_chain,
        get_session_history,
        input_messages_key="input",
        history_messages_key="chat_history",
        output_messages_key="answer",
    ).pick('answer')
    return conversational_rag_chain

def get_ai_response(user_message, cfg, provider):
    global llm_model
    llm_model = provider
    dictionary_chain = get_dictionary_chain()
    rag_chain = get_rag_chain()
    game_dev_chain = {"input": dictionary_chain} | rag_chain
    ai_response = game_dev_chain.stream(
        {
            "question": user_message
        },
        config=cfg,
    )
    return ai_response
