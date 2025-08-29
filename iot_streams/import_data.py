# iot_streams/import_data.py
import click
import requests
import pandas as pd
import os
from pathlib import Path
from datetime import datetime

from clients.minio.minio_wrapper import MinioWrapper
from clients.minio.minio_client import MinioClient
from config.settings import BUCKET_NAME

miwr = MinioWrapper()
micl = MinioClient()

STATE_DIR = Path(os.getenv("EMO_STATE_DIR", "/tmp"))
STATE_DIR.mkdir(parents=True, exist_ok=True)

def _resume_path(filename: str) -> Path:
    return STATE_DIR / f"{filename.replace(' ', '_')}_resume.txt"

def _wm_path(filename: str) -> Path:
    return STATE_DIR / f"{filename.replace(' ', '_')}_watermark.txt"

def _load_resume(filename: str) -> str | None:
    p = _resume_path(filename)
    try:
        if p.exists():
            s = p.read_text().strip()
            return s or None
    except Exception:
        pass
    return None

def _save_resume(filename: str, url: str) -> None:
    try:
        _resume_path(filename).write_text(url or "")
    except Exception:
        pass

def _clear_resume(filename: str) -> None:
    try:
        p = _resume_path(filename)
        if p.exists():
            p.unlink()
    except Exception:
        pass

def _load_watermark(filename: str) -> datetime | None:
    p = _wm_path(filename)
    try:
        if p.exists():
            s = p.read_text().strip()
            if s:
                return pd.to_datetime(s, errors="coerce").to_pydatetime()
    except Exception:
        pass
    return None

def _ts_to_naive(series: pd.Series) -> pd.Series:
    s = series.astype(str).str.replace("Z", "", regex=False).str.replace("T", " ", regex=False)
    s = s.str.replace(r"\+\d{2}:\d{2}$", "", regex=True)
    return pd.to_datetime(s, errors="coerce")

def _maybe_update_watermark(filename: str, candidate_series: pd.Series) -> datetime | None:
    ts = _ts_to_naive(candidate_series)
    if ts.empty:
        return None
    mx = ts.max()
    if pd.isna(mx):
        return None

    mx_py = mx.to_pydatetime() 
    cur = _load_watermark(filename)
    if (cur is None) or (mx_py > cur):
        try:
            Path(_wm_path(filename)).write_text(mx_py.strftime("%Y-%m-%d %H:%M:%S.%f").rstrip("0").rstrip("."))
        except Exception:
            pass
        return mx_py
    return None

def store_api_data_to_minio(url: str, drct: str, filename: str):
    next_url = _load_resume(filename) or url
    page = 1
    total_rows = 0

    wm = _load_watermark(filename)
    print(f"[IMPORTER] {filename}: start from {next_url} | WM={wm or '-'}")

    while next_url:
        _save_resume(filename, next_url)

        try:
            resp = requests.get(next_url, timeout=30)
            print(f"[IMPORTER] {filename}: GET {next_url} -> {resp.status_code}")
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            print(f"[IMPORTER][ERROR] {filename}: request/json failed: {e}")
            raise

        results = data.get("results", [])
        if not isinstance(results, list):
            raise ValueError(f"[IMPORTER] {filename}: 'results' not a list (type={type(results).__name__})")

        rows = len(results)
        print(f"[IMPORTER] {filename}: page {page} rows={rows}")

        df = pd.DataFrame(results) if rows else pd.DataFrame()

        if wm is not None and not df.empty and "timestamp" in df.columns:
            ts = _ts_to_naive(df["timestamp"])
            df = df[ts > wm]

        if not df.empty:
            micl.put_df_(
                bucket_name=BUCKET_NAME,
                directory=drct,
                file_name=f"{filename} {page}",
                df=df,
            )
            total_rows += len(df)
            if "timestamp" in df.columns:
                new_wm = _maybe_update_watermark(filename, df["timestamp"])
                if new_wm is not None:
                    wm = new_wm
        else:
            if wm is not None:
                print(f"[IMPORTER] {filename}: early-stop (no rows > WM) at page {page}")
                break

        next_url = data.get("next")
        page += 1

    _clear_resume(filename)
    print(f"[IMPORTER] {filename}: done, written {total_rows} new rows in {page-1} pages to s3://{BUCKET_NAME}/{drct}/")

def store_file_data_to_minio(filename, file):
    return miwr.put_file(bucket_name=BUCKET_NAME, file_name=filename, file=file)

@click.command()
@click.option("--url", required=True, help="API URL")
@click.option("--drct", required=True, help="Bucket dest dir")
@click.option("--filename", required=True, help="base filename saved into bucket")
@click.option("--minutes", type=int, help="Start delay (minutes)")
def store_data_in_bucket(url, drct, filename, minutes):
    if minutes:
        import time
        time.sleep(int(minutes) * 60)

    print(f"[IMPORTER] BUCKET={BUCKET_NAME} DRCT={drct} FILE={filename}")
    store_api_data_to_minio(url, drct, filename)

if __name__ == "__main__":
    store_data_in_bucket()
