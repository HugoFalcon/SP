# 1. Cargar la bbdd con langchain
from langchain_community.utilities import SQLDatabase
db = SQLDatabase.from_uri("sqlite:///ecommerce.db")

# 2. Importar las APIs
import streamlit as st
import os

# Usar secrets de Streamlit en lugar de archivo local
# En desarrollo local, usa st.secrets o variables de entorno
if "OPENAI_API_KEY" in st.secrets:
    os.environ["OPENAI_API_KEY"] = st.secrets["OPENAI_API_KEY"]
else:
    # Para desarrollo local, intenta importar el archivo
    try:
        import a_env_vars
        os.environ["OPENAI_API_KEY"] = a_env_vars.OPENAI_API_KEY
    except ImportError:
        st.error("No se encontró la API Key de OpenAI. Configúrala en Streamlit Cloud o en tu archivo local.")

# 3. Crear el LLM
from langchain_openai import ChatOpenAI
llm = ChatOpenAI(temperature=0, model_name='gpt-3.5-turbo')

# 4. Crear la cadena
from langchain.chains import create_sql_query_chain
from langchain_community.tools.sql_database.tool import QuerySQLDataBaseTool
from operator import itemgetter
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough

# Crear la cadena de consulta SQL
query_chain = create_sql_query_chain(llm, db)
execute_query = QuerySQLDataBaseTool(db=db)

# Crear un prompt para procesar la respuesta
answer_prompt = PromptTemplate.from_template(
    """Dada la siguiente pregunta del usuario, la consulta SQL correspondiente y el resultado SQL, 
    formula una respuesta en español.

    Pregunta: {question}
    Consulta SQL: {query}
    Resultado SQL: {result}
    Respuesta:"""
)

# Crear la cadena completa
chain = (
    RunnablePassthrough.assign(query=query_chain).assign(
        result=itemgetter("query") | execute_query
    )
    | answer_prompt
    | llm
    | StrOutputParser()
)

# 5. Formato personalizado de respuesta
formato = """
Dada una pregunta del usuario:
1. crea una consulta de sqlite3
2. revisa los resultados
3. devuelve el dato
4. si tienes que hacer alguna aclaración o devolver cualquier texto que sea siempre en español

Pregunta: {question}
"""

# 6. Función para hacer la consulta
def consulta(input_usuario):
    try:
        # Verificar que tenemos API key
        if "OPENAI_API_KEY" not in os.environ or not os.environ["OPENAI_API_KEY"]:
            return "Error: No se ha configurado la API Key de OpenAI"
        
        # Usar la nueva cadena
        resultado = chain.invoke({"question": input_usuario})
        return resultado
    except Exception as e:
        return f"Error al procesar la consulta: {str(e)}"