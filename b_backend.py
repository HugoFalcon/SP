# 1. Cargar la bbdd con langchain
from langchain_community.utilities import SQLDatabase
import streamlit as st
import os
import requests
import gdown
import time
import sqlite3

# Función para descargar la base de datos desde Google Drive
@st.cache_data(ttl=3600)  # Cache por 1 hora
def download_database():
    """Descarga la base de datos desde Google Drive si no existe localmente"""
    db_path = "ecommerce.db"
    
    # Si la base de datos ya existe localmente, verificar su tamaño
    if os.path.exists(db_path):
        file_size = os.path.getsize(db_path)
        if file_size > 1000:  # Si el archivo tiene más de 1KB, asumimos que está completo
            return db_path
        else:
            # Si el archivo existe pero está vacío o corrupto, lo eliminamos
            os.remove(db_path)
    
    try:
        # Extraer el ID del archivo de Google Drive
        file_id = "1YDmVjf5Nrz9Llgtka3KQMBUKwsnSF5vk"
        
        # Crear un contenedor para mostrar el progreso
        progress_container = st.container()
        
        with progress_container:
            st.info("🔄 Descargando base de datos... Esto puede tomar unos momentos la primera vez.")
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # Intentar descargar con gdown
            try:
                # URL directa para descargar desde Google Drive
                url = f"https://drive.google.com/uc?id={file_id}"
                
                # Descargar con gdown mostrando progreso
                status_text.text("Conectando con Google Drive...")
                progress_bar.progress(10)
                
                # Usar gdown con quiet=True para evitar conflictos con Streamlit
                output = gdown.download(url, db_path, quiet=True)
                
                if output:
                    progress_bar.progress(100)
                    status_text.text("✅ Base de datos descargada exitosamente!")
                    time.sleep(1)  # Dar tiempo para ver el mensaje
                    return db_path
                else:
                    raise Exception("gdown no pudo descargar el archivo")
                    
            except Exception as e:
                # Si gdown falla, intentar método alternativo
                status_text.text("Intentando método alternativo de descarga...")
                progress_bar.progress(50)
                
                # Primero, obtener el token de confirmación si es necesario
                session = requests.Session()
                response = session.get(f"https://drive.google.com/uc?export=download&id={file_id}", stream=True)
                
                # Buscar token de confirmación en las cookies
                token = None
                for key, value in response.cookies.items():
                    if key.startswith('download_warning'):
                        token = value
                        break
                
                # URLs alternativas para intentar
                if token:
                    urls_to_try = [
                        f"https://drive.google.com/uc?export=download&confirm={token}&id={file_id}"
                    ]
                else:
                    urls_to_try = [
                        f"https://drive.google.com/uc?export=download&id={file_id}",
                        f"https://docs.google.com/uc?export=download&id={file_id}"
                    ]
                
                for url_idx, url in enumerate(urls_to_try):
                    try:
                        status_text.text(f"Intentando descarga método {url_idx + 1}...")
                        
                        if url_idx == 0 and token:
                            # Usar la sesión existente si tenemos token
                            response = session.get(url, stream=True, timeout=300)
                        else:
                            response = requests.get(url, stream=True, timeout=300)
                        
                        if response.status_code == 200:
                            # Verificar el contenido - Google Drive a veces devuelve HTML en lugar del archivo
                            content_type = response.headers.get('content-type', '')
                            if 'text/html' in content_type:
                                # Si recibimos HTML, probablemente es una página de confirmación
                                status_text.text("Archivo requiere confirmación adicional...")
                                continue
                            
                            # Descargar en chunks para archivos grandes
                            total_size = int(response.headers.get('content-length', 0))
                            block_size = 8192
                            downloaded = 0
                            
                            # Usar un archivo temporal primero
                            temp_path = db_path + ".tmp"
                            
                            with open(temp_path, 'wb') as f:
                                for chunk in response.iter_content(block_size):
                                    if chunk:
                                        f.write(chunk)
                                        downloaded += len(chunk)
                                        if total_size > 0:
                                            progress = int(50 + (downloaded / total_size) * 50)
                                            progress_bar.progress(progress)
                                            status_text.text(f"Descargando... {downloaded / 1024 / 1024:.1f} MB")
                            
                            # Verificar que el archivo descargado es una base de datos SQLite válida
                            status_text.text("Verificando integridad de la base de datos...")
                            
                            # Intentar abrir el archivo como SQLite
                            import sqlite3
                            try:
                                conn = sqlite3.connect(temp_path)
                                cursor = conn.cursor()
                                # Intentar una consulta simple
                                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' LIMIT 1")
                                cursor.close()
                                conn.close()
                                
                                # Si llegamos aquí, el archivo es válido
                                os.rename(temp_path, db_path)
                                progress_bar.progress(100)
                                status_text.text("✅ Base de datos descargada y verificada exitosamente!")
                                time.sleep(1)
                                return db_path
                                
                            except sqlite3.DatabaseError as e:
                                os.remove(temp_path)
                                status_text.text(f"❌ El archivo descargado no es una base de datos válida")
                                continue
                            
                    except Exception as download_error:
                        continue
                
                # Si todos los métodos fallan
                raise Exception("No se pudo descargar el archivo con ningún método")
                
    except Exception as e:
        st.error(f"❌ Error al descargar la base de datos: {str(e)}")
        st.error("Por favor, verifica que el enlace de Google Drive sea público.")
        return None
    finally:
        # Limpiar los widgets de progreso
        if 'progress_container' in locals():
            progress_container.empty()

# Variable global para almacenar la conexión a la base de datos
db = None

# Función para inicializar la base de datos
@st.cache_resource
def init_database():
    """Inicializa la conexión a la base de datos"""
    try:
        db_path = download_database()
        if db_path and os.path.exists(db_path):
            return SQLDatabase.from_uri(f"sqlite:///{db_path}")
        else:
            return None
    except Exception as e:
        st.error(f"Error al inicializar la base de datos: {e}")
        return None

# Inicializar la base de datos
db = init_database()

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

@st.cache_resource
def init_chain():
    """Inicializa la cadena solo cuando se necesita"""
    global db
    
    # Asegurar que tenemos la base de datos
    if db is None:
        db = init_database()
        if db is None:
            return None
    
    try:
        # Crear LLM con configuración explícita
        llm = ChatOpenAI(
            temperature=0,
#            model_name='gpt-3.5-turbo',
            model_name='gpt-4',
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
        
        return chain
        
    except Exception as e:
        st.error(f"Error al inicializar la cadena: {str(e)}")
        return None

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
        
        # Obtener o inicializar la cadena
        chain = init_chain()
        if chain is None:
            return "Error: No se pudo inicializar el sistema. Por favor, recarga la página."
        
        # Usar la cadena con timeout
        with st.spinner("Procesando tu consulta..."):
            resultado = chain.invoke({"question": input_usuario})
        
        return resultado
        
    except Exception as e:
        return f"Error al procesar la consulta: {str(e)}"
