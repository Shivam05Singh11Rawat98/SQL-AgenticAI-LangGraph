
import os
from dotenv import load_dotenv
import yaml
from pyprojroot import here
import shutil
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from urllib.parse import quote_plus

print("Environment variables are loaded:", load_dotenv())


class LoadConfig:
    def __init__(self) -> None:
        with open(here("config/app_config.yml")) as cfg:
            app_config = yaml.load(cfg, Loader=yaml.FullLoader)

        self.load_directories(app_config=app_config)
        self.load_llm_configs(app_config=app_config)
        self.load_openai_models()

        # Un comment the code below if you want to clean up the upload csv SQL DB on every fresh run of the chatbot. (if it exists)
        # self.remove_directory(self.uploaded_files_sqldb_directory)

    def load_directories(self, app_config):
        pg_user = os.getenv("PG_USER")
        pg_password = quote_plus(os.getenv("PG_PASSWORD"))  # ← this encodes special chars
        pg_host = os.getenv("PG_HOST", "localhost")
        pg_port = os.getenv("PG_PORT", "5432")
        pg_db = os.getenv("PG_DB1")
        csv_db = os.getenv("PG_DB2")
        self.sqldb_connection_uri = f"postgresql://{pg_user}:{pg_password}@{pg_host}:{pg_port}/{pg_db}"
        self.csvdb_connection_uri = f"postgresql://{pg_user}:{pg_password}@{pg_host}:{pg_port}/{csv_db}"
        self.uploaded_files_sqldb_directory = str(here(
            app_config["directories"]["uploaded_files_sqldb_directory"]))

    def load_llm_configs(self, app_config):
        self.model_name = os.getenv("GPT_MODEL")
        self.agent_llm_system_role = app_config["llm_config"]["agent_llm_system_role"]
        self.temperature = os.getenv("TEMPERATURE")

    def load_openai_models(self):
        OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
        # This will be used for the GPT and embedding models
        
        self.langchain_llm = ChatOpenAI(
            api_key = OPENAI_API_KEY,
            model="gpt-3.5-turbo",
            temperature=self.temperature)

    def remove_directory(self, directory_path: str):
        """
        Removes the specified directory.

        Parameters:
            directory_path (str): The path of the directory to be removed.

        Raises:
            OSError: If an error occurs during the directory removal process.

        Returns:
            None
        """
        if os.path.exists(directory_path):
            try:
                shutil.rmtree(directory_path)
                print(
                    f"The directory '{directory_path}' has been successfully removed.")
            except OSError as e:
                print(f"Error: {e}")
        else:
            print(f"The directory '{directory_path}' does not exist.")