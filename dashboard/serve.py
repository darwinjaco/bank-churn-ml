"""Launcher ASGI público de Streamlit con las cabeceras de la spec 007 v1.2.

Uso: uv run streamlit run dashboard/serve.py (mismas opciones de Streamlit).
"""

from pathlib import Path

import streamlit as st
from starlette.middleware import Middleware

from churn.dashboard_security import DashboardHeaders

app = st.App(Path(__file__).with_name("app.py"), middleware=[Middleware(DashboardHeaders)])
