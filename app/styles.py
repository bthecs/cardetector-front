"""Estilos y tema visual de la app Streamlit."""

CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600;700&family=IBM+Plex+Mono:wght@500&display=swap');

html, body, [class*="css"] {
  font-family: 'IBM Plex Sans', sans-serif;
}

[data-testid="stAppViewContainer"] {
  background:
    radial-gradient(1200px 600px at 10% -10%, #1b3a4b 0%, transparent 55%),
    radial-gradient(900px 500px at 100% 0%, #0f766e33 0%, transparent 50%),
    linear-gradient(180deg, #0b1220 0%, #111827 45%, #0b1220 100%);
  color: #e5e7eb;
}

[data-testid="stHeader"] {
  background: rgba(11, 18, 32, 0.6);
}

.hero-title {
  font-size: 2.4rem;
  font-weight: 700;
  letter-spacing: -0.03em;
  margin-bottom: 0.25rem;
  color: #f8fafc;
}

.hero-sub {
  color: #94a3b8;
  font-size: 1.05rem;
  margin-bottom: 1.5rem;
}

.metric-card {
  background: rgba(30, 41, 59, 0.72);
  border: 1px solid rgba(148, 163, 184, 0.18);
  border-radius: 14px;
  padding: 1rem 1.1rem;
}

.badge {
  display: inline-block;
  padding: 0.2rem 0.55rem;
  border-radius: 999px;
  font-size: 0.75rem;
  font-weight: 600;
  font-family: 'IBM Plex Mono', monospace;
}

.badge-ok {
  background: #064e3b;
  color: #6ee7b7;
}

.badge-bad {
  background: #7f1d1d;
  color: #fecaca;
}

div[data-testid="stFileUploader"] section {
  background: rgba(15, 23, 42, 0.65);
  border: 1px dashed rgba(148, 163, 184, 0.35);
  border-radius: 12px;
}
</style>
"""


def inject(st) -> None:
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
