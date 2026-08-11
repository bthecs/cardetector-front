# Car Detector — Frontend

Interfaz **Streamlit** del sistema de tesis: censo vehicular y reconocimiento de matrículas contra el backend Flask.

## Requisitos

- Python 3.10+
- Backend corriendo en `http://127.0.0.1:8000` (ver `cardetector-backend`)

## Instalación

```bash
python -m venv env
.\env\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

## Ejecutar

```bash
streamlit run main.py
```

## Funciones

- Preview del video subido
- Censo de vehículos con export CSV
- Detector de matrículas (modo día/noche + filtro opcional)
- Healthcheck del backend desde la barra lateral
- Timeouts y mensajes de error claros

## Estructura

```
main.py           # Entrada Streamlit
app/
  ui.py           # Pantalla principal
  api_client.py   # Cliente HTTP
  styles.py       # Tema visual
.streamlit/config.toml
```
