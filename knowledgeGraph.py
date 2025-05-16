import os
from dotenv import load_dotenv
from langchain.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
from langchain.prompts import PromptTemplate
from langchain.vectorstores import Neo4jVector
from langchain.chat_models import ChatOpenAI
from langchain.embeddings import OpenAIEmbeddings
from langchain.graphs import Neo4jGraph
from langchain_experimental.graph_transformers import LLMGraphTransformer
from langchain.chains.graph_qa.cypher import GraphCypherQAChain
import tempfile
from neo4j import GraphDatabase
from langchain_groq import ChatGroq

load_dotenv()

#loading all the APIS
OPENAI_API_KEY = os.environ['OPENAI_API_KEY']
NEO4J_URI = os.environ['NEO4J_URI']
NEO4J_USERNAME = os.environ['NEO4J_USERNAME']
NEO4J_PASSWORD = os.environ['NEO4J_PASSWORD']
GROQ_API_KEY = os.environ['GROQ_API_KEY']

#Connecting Neo4j
from langchain_community.graphs import Neo4jGraph
graph=Neo4jGraph(
    url=NEO4J_URI,
    username=NEO4J_USERNAME,
    password=NEO4J_PASSWORD,
)

#llm
llm=ChatGroq(groq_api_key=GROQ_API_KEY,model_name="gemma2-9b-it")
llm

### Load the dataset of movie
movie_query="""
LOAD CSV WITH HEADERS FROM
'https://raw.githubusercontent.com/tomasonjo/blog-datasets/main/movies/movies_small.csv' as row

MERGE(m:Movie{id:row.movieId})
SET m.released = date(row.released),
    m.title = row.title,
    m.imdbRating = toFloat(row.imdbRating)
FOREACH (director in split(row.director, '|') |
    MERGE (p:Person {name:trim(director)})
    MERGE (p)-[:DIRECTED]->(m))
FOREACH (actor in split(row.actors, '|') |
    MERGE (p:Person {name:trim(actor)})
    MERGE (p)-[:ACTED_IN]->(m))
FOREACH (genre in split(row.genres, '|') |
    MERGE (g:Genre {name:trim(genre)})
    MERGE (m)-[:IN_GENRE]->(g))
"""

graph.query(movie_query)

graph.refresh_schema()
print(graph.schema)


from langchain.chains import GraphCypherQAChain
chain=GraphCypherQAChain.from_llm(llm=llm,graph=graph,verbose=True, allow_dangerous_requests=True)
chain

response=chain.invoke({"query":"Number of actors in the dataset"})

response


