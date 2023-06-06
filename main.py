import streamlit as st
import requests
import cv2
from io import BytesIO
import pandas as pd
from dotenv import load_dotenv
import os

load_dotenv()

# Evita que se reinicie el proceso al descargar el archivo CSV
st.set_option('deprecation.showfileUploaderEncoding', False)

page_bg_img = """
<style>
[data-testid="stAppViewContainer"]{
background-color: #000000;
opacity: 0.6;
background-image:  repeating-radial-gradient( circle at 0 0, transparent 0, #000000 10px ), repeating-linear-gradient( #0044ff55, #0044ff );
}
</style>
"""
st.markdown(page_bg_img, unsafe_allow_html=True)

st.markdown("<h1 style='text-align: center;'>🚔CAR DETECTOR🚔</h1>", unsafe_allow_html=True)
# Muestra un widget de subida de archivos de video.
upload_file = st.file_uploader("Choose a video📽️", type=["mp4", "mkv", "flv", "avi"])

# Variables para almacenar el resultado del procesamiento
response_status = None
response_text = None

# Verifica si el archivo ha sido cargado
if upload_file is not None:

    # Crea un objeto BytesIO a partir del archivo cargado
    video_bytes = BytesIO(upload_file.read())

    # Crea una fila con dos columnas
    col1, col2 = st.columns(2)
    col3, col4, col5 = st.columns(3)

    # Variable para almacenar el valor de "day_night"
    day_night_value = ""

    # Agrega el checkbox "Day"
    if col3.checkbox("Day 🌞"):
        day_night_value = "day"

    # Agrega el checkbox "Night"
    if col4.checkbox("Night 🌙"):
        day_night_value = "night"

    # Agregar campo para almacenar el valor de "plate"
    plate = col5.text_input("Plate 🚘")
    

    if col1.button("vehicle census 🚘"):

        # Envia el objeto creado con BytesIO a la URL del endpoint
        response = requests.post(os.getenv("API_ENDPOINT"), files={"video": video_bytes})

        # Estado de la respuesta
        response_status = response.status_code
        response_text = response.text

    if col2.button("License Plate Detector 🚘"):

        # Crea una fila con dos columnas dentro de la columna 2

        if day_night_value:
            # Envia el objeto creado con BytesIO a la URL del endpoint
            response = requests.post(os.getenv("API_MATRICULA"), files={"video": video_bytes}, data={"day_night": day_night_value, "plate": plate})

            # Estado de la respuesta
            response_status = response.status_code
            response_text = response.text

            if response_status == 200:
                unique_plate = response.json()

                df = pd.DataFrame(unique_plate)

                st.table(df)

                # Descarga el archivo XLSX
                st.download_button(
                    label="Download csv",
                    data=df.to_csv().encode("utf-8"),
                    file_name="license_plate.csv",
                )

            else:
                st.error("Error: {} - {}".format(response_status, response_text))


        else:
            st.error("Please select a day or night mode")
        
        

