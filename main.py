from dotenv import load_dotenv
import os

load_dotenv()

# Streamlit Cloud: Secrets → variables API_*
try:
    import streamlit as st

    for key in ("API_BASE", "API_KEY", "API_ENDPOINT", "API_MATRICULA"):
        try:
            if key in st.secrets and st.secrets[key]:
                os.environ[key] = str(st.secrets[key]).rstrip("/")
        except Exception:
            pass
except Exception:
    pass

from app.ui import render

if __name__ == "__main__":
    render()
else:
    # `streamlit run main.py` importa el módulo
    render()
