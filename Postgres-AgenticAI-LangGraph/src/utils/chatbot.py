import os
from typing import List, Tuple
from utils.load_config import LoadConfig
from langchain_community.utilities import SQLDatabase
from langchain.chains import create_sql_query_chain
from langchain_community.tools.sql_database.tool import QuerySQLDataBaseTool
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from operator import itemgetter
from sqlalchemy import create_engine
from urllib.parse import quote_plus
from langchain_community.agent_toolkits import create_sql_agent
import langchain
langchain.debug = True

APPCFG = LoadConfig()


class ChatBot:
    """
    A ChatBot class capable of responding to messages using different modes of operation.
    It can interact with SQL databases, leverage language chain agents for Q&A,
    and use embeddings for Retrieval-Augmented Generation (RAG) with ChromaDB.
    """
    @staticmethod
    def respond(chatbot: List, message: str, chat_type: str, app_functionality: str) -> Tuple:
        """
        Respond to a message based on the given chat and application functionality types.

        Args:
            chatbot (List): A list representing the chatbot's conversation history.
            message (str): The user's input message to the chatbot.
            chat_type (str): Describes the type of the chat (interaction with SQL DB or RAG).
            app_functionality (str): Identifies the functionality for which the chatbot is being used (e.g., 'Chat').

        Returns:
            Tuple[str, List, Optional[Any]]: A tuple containing an empty string, the updated chatbot conversation list,
                                             and an optional 'None' value. The empty string and 'None' are placeholder
                                             values to match the required return type and may be updated for further functionality.
                                             Currently, the function primarily updates the chatbot conversation list.
        """
        if app_functionality == "Chat":
            # If we want to use langchain agents for Q&A with our SQL DBs that was created from .sql files.
            if chat_type == "Q&A with stored SQL-DB":
                # directories
                try:
                    print("sultan", APPCFG.sqldb_connection_uri)
                    db = SQLDatabase.from_uri(APPCFG.sqldb_connection_uri)
                    execute_query = QuerySQLDataBaseTool(db=db)
                    write_query = create_sql_query_chain(
                            APPCFG.langchain_llm, db)
                    answer_prompt = PromptTemplate.from_template(
                            APPCFG.agent_llm_system_role)
                    answer = answer_prompt | APPCFG.langchain_llm | StrOutputParser()
                    chain = (
                        RunnablePassthrough.assign(query=write_query).assign(
                            result=itemgetter("query") | execute_query
                        )
                        | answer
                    )
                    response = chain.invoke({"question": message})
                except Exception:
                    chatbot.append(
                        (message, f"SQL DB does not exist. Please first create the 'sqldb.db'."))
                    return "", chatbot, None

                    
            # If we want to use langchain agents for Q&A with our SQL DBs that were created from CSV/XLSX files.
            elif chat_type == "Q&A with Uploaded CSV/XLSX SQL-DB" or chat_type == "Q&A with stored CSV/XLSX SQL-DB":
                
                if os.path.exists(APPCFG.uploaded_files_sqldb_directory):
                    pg_user = os.getenv("PG_USER")
                    pg_password = quote_plus(os.getenv("PG_PASSWORD"))  # ← this encodes special chars
                    pg_host = os.getenv("PG_HOST", "localhost")
                    pg_port = os.getenv("PG_PORT", "5432")
                    pg_db = os.getenv("PG_DB1")
                    csv_db = os.getenv("PG_DB2")
                    db_path = f"postgresql://{pg_user}:{pg_password}@{pg_host}:{pg_port}/{csv_db}"
                    engine = create_engine(db_path)
                    db = SQLDatabase(engine=engine)
                    print(db.dialect)
                else:
                    chatbot.append(
                        (message, f"SQL DB from the uploaded csv/xlsx files does not exist. Please first upload the csv files from the chatbot."))
                    return "", chatbot, None
                
                print(db.dialect)
                print(db.get_usable_table_names())
                agent_executor = create_sql_agent(
                    APPCFG.langchain_llm, db=db, agent_type="openai-tools", verbose=True)
                response = agent_executor.invoke({"input": message})
                response = response["output"]
            chatbot.append((message, response))
            return "", chatbot    
        else:
            pass