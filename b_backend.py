# 1. Cargar la bbdd con langchain
from langchain_community.utilities import SQLDatabase
import streamlit as st
import os
import requests
import gdown

# Función para descargar la base de datos desde Google Drive
@st.cache_resource
def download_database():
    """Descarga la base de datos desde Google Drive si no existe localmente"""
    db_path = "ecommerce.db"
    
    # Si la base de datos ya existe, no la descargamos de nuevo
    if os.path.exists(db_path):
        return db_path
    
    try:
        # Extraer el ID del archivo de Google Drive
        # De tu URL: https://drive.google.com/file/d/1YDmVjf5Nrz9Llgtka3KQMBUKwsnSF5vk/view?usp=drive_link
        file_id = "1YDmVjf5Nrz9Llgtka3KQMBUKwsnSF5vk"
        
        # URL directa para descargar desde Google Drive
        url = f"https://drive.google.com/uc?id={file_id}"
        
        # Mostrar mensaje de descarga
        with st.spinner("Descargando base de datos... Esto puede tomar unos momentos la primera vez."):
            # Usar gdown para descargar el archivo
            gdown.download(url, db_path, quiet=False)
        
        st.success("Base de datos descargada exitosamente!")
        return db_path
        
    except Exception as e:
        st.error(f"Error al descargar la base de datos: {e}")
        # Intentar método alternativo
        try:
            download_url = f"https://drive.google.com/uc?export=download&id={file_id}"
            response = requests.get(download_url)
            
            if response.status_code == 200:
                with open(db_path, 'wb') as f:
                    f.write(response.content)
                st.success("Base de datos descargada exitosamente (método alternativo)!")
                return db_path
            else:
                st.error(f"Error al descargar: Status code {response.status_code}")
                return None
                
        except Exception as e2:
            st.error(f"Error en descarga alternativa: {e2}")
            return None

# Configurar la base de datos
try:
    db_path = download_database()
    if db_path:
        db = SQLDatabase.from_uri(f"sqlite:///{db_path}")
    else:
        db = None
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
