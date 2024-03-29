# imports
import streamlit as st
import os, tempfile
import pandas as pd
from langchain.chat_models import ChatOpenAI
from langchain_community.vectorstores import FAISS
from langchain.embeddings import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import CSVLoader
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.chat_history import BaseChatMessageHistory
from langchain.chains.summarize import load_summarize_chain
from langchain_core.prompts import MessagesPlaceholder
from langchain_experimental.agents import create_pandas_dataframe_agent
import asyncio

st.set_page_config(page_title="CSV AI", layout="wide")
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

def home_page():
    st.write("""Select "Summarize CSV" feature from above sliderbox """)

@st.cache_resource()
def retriever_func(uploaded_file):
    if uploaded_file :
        with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            tmp_file_path = tmp_file.name
        try:
            loader = CSVLoader(file_path=tmp_file_path, encoding="utf-8")
            data = loader.load()
        except:
            loader = CSVLoader(file_path=tmp_file_path, encoding="cp1252")
            data = loader.load()

        text_splitter = RecursiveCharacterTextSplitter(
                        chunk_size=1000, 
                        chunk_overlap=200, 
                        add_start_index=True
                        )
        all_splits = text_splitter.split_documents(data)

        
        vectorstore = FAISS.from_documents(documents=all_splits, embedding=OpenAIEmbeddings())
        retriever = vectorstore.as_retriever(search_type="similarity", search_kwargs={"k": 6})
    if not uploaded_file:
        st.info("Please upload CSV documents to continue.")
        st.stop()
    return retriever, vectorstore

def summary(model_name, temperature, top_p):
    st.write("# Summary of CSV")
    st.write("Upload your document here:")
    uploaded_file = st.file_uploader("Upload source document", type="csv", label_visibility="collapsed")
    if uploaded_file is not None:
        with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            tmp_file_path = tmp_file.name
        # encoding = cp1252
        text_splitter = RecursiveCharacterTextSplitter(chunk_size = 1024, chunk_overlap=100)
        try:
            loader = CSVLoader(file_path=tmp_file_path, encoding="cp1252")
            #loader = UnstructuredFileLoader(tmp_file_path)
            data = loader.load()
            texts = text_splitter.split_documents(data)

            df = pd.read_csv(tmp_file_path)
            llm = ChatOpenAI(model=model_name, temperature=temperature)
            agent = create_pandas_dataframe_agent(llm, df, agent_type="openai-tools", verbose=True,handle_parsing_errors=True)            

        except:
            loader = CSVLoader(file_path=tmp_file_path, encoding="utf-8")
            #loader = UnstructuredFileLoader(tmp_file_path)
            data = loader.load()
            texts = text_splitter.split_documents(data)

            df = pd.read_csv(tmp_file_path)
            llm = ChatOpenAI(model=model_name, temperature=temperature)
            agent = create_pandas_dataframe_agent(llm, df, agent_type="openai-tools", verbose=True,handle_parsing_errors=True)

        os.remove(tmp_file_path)
        gen_sum = st.button("Generate Summary")
        if gen_sum:
            # Initialize the OpenAI module, load and run the summarize chain
            llm = ChatOpenAI(model_name=model_name, temperature=temperature)
            chain = load_summarize_chain(
                llm=llm,
                chain_type="map_reduce",

                return_intermediate_steps=True,
                input_key="input_documents",
                output_key="output_text",
            )
            result = chain({"input_documents": texts}, return_only_outputs=True)

            msg_initiate1 = agent.invoke({"input": "What are the names of the stores?"})
            print(msg_initiate1["output"])
            msg_initiate2 = agent.invoke({"input": "Which store have the highest sales?"})
            print(msg_initiate2["output"])
            msg_initiate3 = agent.invoke({"input": "Which store have the most sudden or most significant spike in growth, and in which day?"})
            print(msg_initiate3["output"])
            msg_initiate4 = agent.invoke({"input": "Get and list all relevant information from 'information on' columns. Tell me what information that you found"})
            print(msg_initiate4["output"])
            msg_initiate5 = agent.invoke({"input": "Analyze factors from the additional 'information on' columns to identify potential reasons for significant daily changes in sales and profit? If you generate Python code to do the analysis, execute and find the information, ignore ones without specific information but take all other relevant information. Then identify factors from that additional 'information on' day columns that might affect significant daily changes on each store, for example by comparing it to sales and profit, and suggest on the insights."})
            print(msg_initiate5["output"])
            # msg_initiate6 = agent.invoke({"input": "Is there any figure or information that doesn't seem right?"})
            # print(msg_initiate6["output"])

            # data = {'column1': ["summary -->","report 5->"], 'column2': [result["output_text"],msg_initiate5["output"]]}
            data = {'column1': ["summary -->","report 1->", "report 2->", "report 3->", "report 4->","report 5->"], 'column2': [result["output_text"],msg_initiate1["output"], msg_initiate2["output"], msg_initiate3["output"],msg_initiate4["output"],msg_initiate5["output"]]}
            # data = {'column1': ["summary -->","report 1->", "report 2->", "report 3->", "report 4->","report 5->","report 6->","report 7->"], 'column2': [result["output_text"],msg_initiate1["output"], msg_initiate2["output"], msg_initiate3["output"],msg_initiate4["output"],msg_initiate5["output"],msg_initiate6["output"],"End of report"]}
            df = pd.DataFrame(data)
            csv_file = df.to_csv(index=False).encode('utf-8')  # Convert DataFrame to CSV

            download = st.download_button(
                 label="Download Data as CSV",
                 data=csv_file,
                 file_name='your_data.csv',
                 mime='text/csv',
            )
                

            st.success("Report generated - you can download the report with download button above")


def increase_spinner_font(font_size="1.2em"):  # Adjust font_size as needed
    """Injects custom CSS to potentially increase spinner font size."""
    st.markdown(
        f"""<style>
        .stSpinner > div > div {{ font-size: {font_size}; }}
        </style>""",
        unsafe_allow_html=True,
    )

# Main App
def main():
    st.markdown(
        """
        <div style='text-align: center;'>
            <h1>CSV REPORTING AI </h1>
        </div>
        <style>
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        </style>
        """,
        unsafe_allow_html=True,
    )
    st.markdown(
        """
        <div style='text-align: center;'>
            <h4>Analyze CSVs with LLM</h4>
        </div>
        """,
        unsafe_allow_html=True,
    )
    increase_spinner_font()
    global user_api_key
    # #
    # st.sidebar.write("---")
    if os.path.exists(".env") and os.environ.get("OPENAI_API_KEY") is not None:
        user_api_key = os.environ["OPENAI_API_KEY"]
        st.success("API key loaded from .env")
    else:
        user_api_key = st.sidebar.text_input(
            label="#### Enter OpenAI API key", placeholder="Paste your openAI API key, sk-", type="password", key="openai_api_key"
        )
        if user_api_key:
            st.sidebar.success("API key loaded")

    os.environ["OPENAI_API_KEY"] = user_api_key

    

    # Execute the home page function
    MODEL_OPTIONS = ["gpt-3.5-turbo", "gpt-4", "gpt-4-32k","gpt-3.5-turbo-16k","gpt-4-1106-preview"]
    max_tokens = {"gpt-4":7000, "gpt-4-32k":31000, "gpt-3.5-turbo":3000}
    TEMPERATURE_MIN_VALUE = 0.0
    TEMPERATURE_MAX_VALUE = 1.0
    TEMPERATURE_DEFAULT_VALUE = 0.9
    TEMPERATURE_STEP = 0.01
    model_name = st.sidebar.selectbox(label="Model", options=MODEL_OPTIONS)
    top_p = st.sidebar.slider("Top_P", 0.0, 1.0, 1.0, 0.1)
    # freq_penalty = st.sidebar.slider("Frequency Penalty", 0.0, 2.0, 0.0, 0.1)
    temperature = st.sidebar.slider(
                label="Temperature",
                min_value=TEMPERATURE_MIN_VALUE,
                max_value=TEMPERATURE_MAX_VALUE,
                value=TEMPERATURE_DEFAULT_VALUE,
                step=TEMPERATURE_STEP,)

    # Define a dictionary with the function names and their respective functions
    functions = [
        "home",
        # "Chat with CSV",
        "Summarize CSV",
        # "Analyze CSV",
    ]
    
    #st.subheader("Select any generator")
    # Create a selectbox with the function names as options
    selected_function = st.selectbox("Select a functionality", functions)
    if selected_function == "home":
        home_page()
    elif selected_function == "Chat with CSV":
        chat(temperature=temperature, model_name=model_name)
    elif selected_function == "Summarize CSV":
        summary(model_name=model_name, temperature=temperature, top_p=top_p)
    elif selected_function == "Analyze CSV":
        analyze(temperature=temperature, model_name=model_name)
    else:
        st.warning("You haven't selected any AI Functionality!!")
    

    

if __name__ == "__main__":
    main()
