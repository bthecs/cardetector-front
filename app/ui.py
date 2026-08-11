"""UI principal de Car Detector (Streamlit) con preview en vivo."""
from __future__ import annotations

from io import BytesIO
from typing import Optional

import pandas as pd
import streamlit as st

from app import api_client, styles


def _normalize_census(payload) -> pd.DataFrame:
    if isinstance(payload, list):
        return pd.DataFrame(payload)
    if isinstance(payload, dict):
        row = {
            "Total vehículos": payload.get(
                "total_vehicles",
                payload.get("Total de vehiculos en el video", 0),
            ),
            "Tiempo de ejecución": payload.get("execution_time", ""),
            "Frames": payload.get("frames_processed", ""),
        }
        by_class = payload.get("by_class") or {}
        for name, count in by_class.items():
            row[f"Clase: {name}"] = count
        return pd.DataFrame([row])
    return pd.DataFrame([{"resultado": str(payload)}])


def _show_annotated(video_bytes: Optional[bytes], title: str, key: str) -> None:
    if not video_bytes:
        return
    st.subheader(title)
    st.video(video_bytes)
    st.download_button(
        "Descargar video anotado completo",
        data=video_bytes,
        file_name="annotated.mp4",
        mime="video/mp4",
        key=key,
    )


def _run_live_job(job_id: str) -> dict:
    """Polling con preview JPEG + barra de progreso."""
    live_box = st.empty()
    progress_bar = st.progress(0.0, text="Iniciando…")
    stats_box = st.empty()

    def on_update(job: dict, frame: Optional[bytes]) -> None:
        progress = job.get("progress") or {}
        pct = float(progress.get("pct") or 0.0)
        current = progress.get("current", 0)
        total = progress.get("total", 0)
        progress_bar.progress(
            min(1.0, pct / 100.0),
            text=f"Procesando frame {current}/{total or '?'} ({pct:.0f}%)",
        )
        if frame:
            live_box.image(frame, caption="Tracking en vivo", use_container_width=True)
        stats = job.get("live_stats") or {}
        if stats:
            stats_box.json(stats)

    job = api_client.watch_job(job_id, on_update=on_update)
    progress_bar.progress(1.0, text="Completado")
    return job


def render() -> None:
    st.set_page_config(
        page_title="Car Detector",
        page_icon="🚗",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    styles.inject(st)

    st.markdown('<div class="hero-title">Car Detector</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="hero-sub">Sistema de censo vehicular y reconocimiento de matrículas</div>',
        unsafe_allow_html=True,
    )

    with st.sidebar:
        st.subheader("Estado del backend")
        if st.button("Comprobar conexión", use_container_width=True):
            status = api_client.healthcheck()
            if status["ok"]:
                st.markdown(
                    '<span class="badge badge-ok">ONLINE</span>',
                    unsafe_allow_html=True,
                )
                st.json(status["body"])
            else:
                st.markdown(
                    '<span class="badge badge-bad">OFFLINE</span>',
                    unsafe_allow_html=True,
                )
                st.warning(status["body"])

        st.markdown("---")
        live_preview = st.checkbox(
            "Preview en vivo",
            value=True,
            help="Muestra el tracking frame a frame mientras procesa (vía jobs async).",
        )
        save_full_video = st.checkbox(
            "Guardar video anotado final",
            value=True,
            help="Al terminar, genera MP4 completo para descargar/reproducir.",
        )
        st.caption("Formatos: MP4, MKV, AVI, FLV, MOV.")

    upload = st.file_uploader(
        "Subí un video de tráfico",
        type=["mp4", "mkv", "flv", "avi", "mov"],
        help="Se envía al backend Flask para inferencia.",
    )

    if upload is None:
        st.info("Subí un video para habilitar el censo y el detector de matrículas.")
        return

    st.video(upload)
    upload.seek(0)

    tab_census, tab_plates = st.tabs(["Censo de vehículos", "Detector de matrículas"])

    with tab_census:
        st.write(
            "Detecta y rastrea vehículos (auto, moto, bus, camión) a lo largo del video."
        )
        if st.button("Ejecutar censo", type="primary", key="btn_census"):
            video_bytes = BytesIO(upload.getvalue())
            try:
                if live_preview:
                    job_id = api_client.start_census_job(
                        video_bytes,
                        filename=upload.name,
                        return_video=save_full_video,
                    )
                    st.caption(f"Job `{job_id}`")
                    job = _run_live_job(job_id)
                    result = job.get("result") or {}
                else:
                    with st.spinner("Procesando censo…"):
                        result = api_client.census(
                            video_bytes,
                            filename=upload.name,
                            return_video=save_full_video,
                        )

                annotated = None
                if save_full_video and result.get("artifact_id"):
                    annotated = api_client.fetch_artifact(result["artifact_id"])
                st.session_state["census_result"] = result
                st.session_state["census_video"] = annotated
            except api_client.ApiError as exc:
                st.session_state.pop("census_result", None)
                st.session_state.pop("census_video", None)
                st.error(str(exc))

        if "census_result" in st.session_state:
            result = st.session_state["census_result"]
            df = _normalize_census(result)
            st.success("Censo completado.")
            _show_annotated(
                st.session_state.get("census_video"),
                "Video anotado final",
                key="dl_census_video",
            )
            st.dataframe(df, use_container_width=True)
            st.download_button(
                "Descargar CSV",
                data=df.to_csv(index=False).encode("utf-8"),
                file_name="vehicle_census.csv",
                mime="text/csv",
                key="csv_census",
            )

    with tab_plates:
        st.write(
            "Localiza matrículas y aplica OCR. El modo día/noche ajusta el umbral de confianza."
        )
        col_a, col_b = st.columns(2)
        with col_a:
            mode = st.radio(
                "Condición de iluminación",
                ["day", "night"],
                horizontal=True,
                format_func=lambda x: "Día" if x == "day" else "Noche",
            )
        with col_b:
            plate = st.text_input(
                "Filtro de patente (opcional)",
                placeholder="Ej: ABC123",
                help="Si se completa, solo se reportan coincidencias parciales.",
            )

        if st.button("Detectar matrículas", type="primary", key="btn_plates"):
            video_bytes = BytesIO(upload.getvalue())
            try:
                if live_preview:
                    job_id = api_client.start_plates_job(
                        video_bytes,
                        day_night=mode,
                        plate=plate.strip(),
                        filename=upload.name,
                        return_video=save_full_video,
                    )
                    st.caption(f"Job `{job_id}`")
                    job = _run_live_job(job_id)
                    result = job.get("result") or {}
                else:
                    with st.spinner("Detectando matrículas…"):
                        result = api_client.plates(
                            video_bytes,
                            day_night=mode,
                            plate=plate.strip(),
                            filename=upload.name,
                            return_video=save_full_video,
                        )

                annotated = None
                if save_full_video and result.get("artifact_id"):
                    annotated = api_client.fetch_artifact(result["artifact_id"])
                st.session_state["plates_result"] = result
                st.session_state["plates_video"] = annotated
            except api_client.ApiError as exc:
                st.session_state.pop("plates_result", None)
                st.session_state.pop("plates_video", None)
                st.error(str(exc))

        if "plates_result" in st.session_state:
            result = st.session_state["plates_result"]
            plates_data = result.get("plates", result if isinstance(result, list) else [])
            df = pd.DataFrame(plates_data)
            st.success("Detección finalizada.")
            _show_annotated(
                st.session_state.get("plates_video"),
                "Video anotado final",
                key="dl_plates_video",
            )
            if df.empty:
                st.warning("No se detectaron matrículas con los parámetros actuales.")
            else:
                st.success(f"Se obtuvieron {len(df)} matrícula(s) únicas.")
                st.dataframe(df, use_container_width=True)
                st.download_button(
                    "Descargar CSV",
                    data=df.to_csv(index=False).encode("utf-8"),
                    file_name="license_plates.csv",
                    mime="text/csv",
                    key="csv_plates",
                )
