# 1. Cargar la bbdd con langchain
from langchain_community.utilities import SQLDatabase
import streamlit as st
import os

# Configurar la base de datos
try:
    db = SQLDatabase.from_uri("sqlite:///ecommerce.db")
except Exception as e:
    st.error(f"Error al cargar la base de datos: {e}")
    db = None

# 2. Importar las APIs
# Configurar OpenAI API Key desde Streamlit secrets
if "OPENAI_API_KEY" in st.secrets:
    os.environ["OPENAI_API_KEY"] = st.secrets["OPENAI_API_KEY"]
else:
    # Para desarrollo local
    try:
        import a_env_vars
        os.environ["OPENAI_API_KEY"] = a_env_vars.OPENAI_API_KEY
    except ImportError:
        st.warning("No se encontró la API Key de OpenAI")

# 3. Crear el LLM
from langchain_openai import ChatOpenAI

# Inicializar como None
llm = None
chain = None

def init_chain():
    """Inicializa la cadena solo cuando se necesita"""
    global llm, chain
    
    if llm is None:
        try:
            # Crear LLM con configuración explícita
            llm = ChatOpenAI(
                temperature=0,
                model_name='gpt-3.5-turbo',  # Usar gpt-3.5-turbo que es más estable
                request_timeout=30,
                max_retries=2
            )
            
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
            
        except Exception as e:
            st.error(f"Error al inicializar: {str(e)}")
            return False
    
    return True

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
        # Verificar API key
        if "OPENAI_API_KEY" not in os.environ:
            return "Error: No se ha configurado la API Key de OpenAI. Ve a Settings → Secrets en Streamlit Cloud."
        
        # Inicializar la cadena si no está lista
        if not init_chain():
            return "Error: No se pudo inicializar el sistema."
        
        # Verificar que tenemos la base de datos
        if db is None:
            return "Error: No se pudo cargar la base de datos."
        
        # Usar la cadena
        resultado = chain.invoke({"question": input_usuario})
        return resultado
        
    except Exception as e:
        return f"Error al procesar la consulta: {str(e)}"
