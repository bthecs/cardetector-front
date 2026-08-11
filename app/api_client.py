"""Cliente HTTP hacia cardetector-backend."""
from __future__ import annotations

import os
import time
from typing import Any, Callable, Dict, Optional, Tuple

import requests


class ApiError(Exception):
    def __init__(self, message: str, status_code: Optional[int] = None):
        super().__init__(message)
        self.status_code = status_code


def _headers() -> Dict[str, str]:
    key = os.getenv("API_KEY", "").strip()
    if key:
        return {"X-API-Key": key}
    return {}


def _base() -> str:
    return os.getenv("API_BASE", "http://127.0.0.1:8000").rstrip("/")


def _url(name: str, default: str) -> str:
    value = os.getenv(name, default).rstrip("/")
    if not value:
        raise ApiError(f"Variable de entorno {name} no configurada.")
    return value


def healthcheck(timeout: float = 5.0) -> Dict[str, Any]:
    try:
        resp = requests.get(
            f"{_base()}/detector/health", headers=_headers(), timeout=timeout
        )
        return {
            "ok": resp.status_code == 200,
            "status_code": resp.status_code,
            "body": resp.json(),
        }
    except requests.RequestException as exc:
        return {"ok": False, "status_code": None, "body": {"error": str(exc)}}


def start_census_job(
    video_bytes,
    filename: str = "video.mp4",
    return_video: bool = True,
    timeout: float = 60.0,
) -> str:
    url = f"{_base()}/detector/jobs/census"
    try:
        resp = requests.post(
            url,
            files={"video": (filename, video_bytes, "application/octet-stream")},
            data={"return_video": "true" if return_video else "false"},
            headers=_headers(),
            timeout=timeout,
        )
    except requests.RequestException as exc:
        raise ApiError(f"No se pudo encolar el censo: {exc}") from exc
    if resp.status_code not in (200, 202):
        raise ApiError(_extract_error(resp), resp.status_code)
    return resp.json()["job_id"]


def start_plates_job(
    video_bytes,
    day_night: str,
    plate: str = "",
    filename: str = "video.mp4",
    return_video: bool = True,
    timeout: float = 60.0,
) -> str:
    url = f"{_base()}/detector/jobs/matricula"
    try:
        resp = requests.post(
            url,
            files={"video": (filename, video_bytes, "application/octet-stream")},
            data={
                "day_night": day_night,
                "plate": plate,
                "return_video": "true" if return_video else "false",
            },
            headers=_headers(),
            timeout=timeout,
        )
    except requests.RequestException as exc:
        raise ApiError(f"No se pudo encolar la deteccion: {exc}") from exc
    if resp.status_code not in (200, 202):
        raise ApiError(_extract_error(resp), resp.status_code)
    return resp.json()["job_id"]


def get_job(job_id: str, timeout: float = 10.0) -> Dict[str, Any]:
    url = f"{_base()}/detector/jobs/{job_id}"
    try:
        resp = requests.get(url, headers=_headers(), timeout=timeout)
    except requests.RequestException as exc:
        raise ApiError(f"No se pudo consultar el job: {exc}") from exc
    if resp.status_code != 200:
        raise ApiError(_extract_error(resp), resp.status_code)
    return resp.json()


def get_job_frame(job_id: str, timeout: float = 10.0) -> Optional[bytes]:
    url = f"{_base()}/detector/jobs/{job_id}/frame"
    try:
        resp = requests.get(url, headers=_headers(), timeout=timeout)
    except requests.RequestException:
        return None
    if resp.status_code == 204 or resp.status_code != 200:
        return None
    return resp.content


def watch_job(
    job_id: str,
    *,
    on_update: Optional[Callable[[Dict[str, Any], Optional[bytes]], None]] = None,
    poll_interval: float = 0.25,
    timeout: float = 3600.0,
) -> Dict[str, Any]:
    """Hace polling hasta done/error. on_update(job, frame_jpeg)."""
    started = time.time()
    last_seq = -1
    while True:
        if time.time() - started > timeout:
            raise ApiError("Timeout esperando el job en vivo.")
        job = get_job(job_id)
        frame = None
        seq = int(job.get("latest_frame_seq") or 0)
        if seq != last_seq:
            frame = get_job_frame(job_id)
            last_seq = seq
        if on_update:
            on_update(job, frame)
        status = job.get("status")
        if status == "done":
            return job
        if status == "error":
            raise ApiError(job.get("error") or "Job falló.")
        time.sleep(poll_interval)


def fetch_artifact(artifact_id: str, timeout: float = 60.0) -> bytes:
    url = f"{_base()}/detector/artifacts/{artifact_id}"
    try:
        resp = requests.get(url, headers=_headers(), timeout=timeout)
    except requests.RequestException as exc:
        raise ApiError(f"No se pudo descargar el video anotado: {exc}") from exc
    if resp.status_code != 200:
        raise ApiError(_extract_error(resp), resp.status_code)
    return resp.content


def census(
    video_bytes,
    filename: str = "video.mp4",
    return_video: bool = True,
    timeout: float = 600.0,
) -> Any:
    url = f"{_base()}/detector/"
    try:
        resp = requests.post(
            url,
            files={"video": (filename, video_bytes, "application/octet-stream")},
            data={"return_video": "true" if return_video else "false"},
            headers=_headers(),
            timeout=timeout,
        )
    except requests.Timeout as exc:
        raise ApiError("Timeout en censo sincrono.") from exc
    except requests.RequestException as exc:
        raise ApiError(f"No se pudo conectar al backend: {exc}") from exc
    if resp.status_code != 200:
        raise ApiError(_extract_error(resp), resp.status_code)
    return resp.json()


def plates(
    video_bytes,
    day_night: str,
    plate: str = "",
    filename: str = "video.mp4",
    return_video: bool = True,
    timeout: float = 900.0,
) -> Any:
    url = f"{_base()}/detector/matricula"
    try:
        resp = requests.post(
            url,
            files={"video": (filename, video_bytes, "application/octet-stream")},
            data={
                "day_night": day_night,
                "plate": plate,
                "return_video": "true" if return_video else "false",
            },
            headers=_headers(),
            timeout=timeout,
        )
    except requests.Timeout as exc:
        raise ApiError("Timeout en deteccion sincrona.") from exc
    except requests.RequestException as exc:
        raise ApiError(f"No se pudo conectar al backend: {exc}") from exc
    if resp.status_code != 200:
        raise ApiError(_extract_error(resp), resp.status_code)
    return resp.json()


def _extract_error(resp: requests.Response) -> str:
    try:
        payload = resp.json()
        if isinstance(payload, dict) and "error" in payload:
            return str(payload["error"])
    except ValueError:
        pass
    return f"HTTP {resp.status_code}: {resp.text[:300]}"
