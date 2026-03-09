from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path

import matplotlib
import pandas as pd
import psycopg
import requests

matplotlib.use("Agg")
import matplotlib.pyplot as plt


REPORTS_DIR = Path("reports")


@dataclass
class Settings:
    target_url: str
    check_interval_seconds: int
    report_every_n_checks: int
    run_mode: str
    db_host: str
    db_port: int
    db_name: str
    db_user: str
    db_password: str

    @property
    def dsn(self) -> str:
        return (
            f"host={self.db_host} "
            f"port={self.db_port} "
            f"dbname={self.db_name} "
            f"user={self.db_user} "
            f"password={self.db_password}"
        )


@dataclass
class CheckResult:
    checked_at: datetime
    status_code: int
    latency_ms: int
    success: bool


def load_settings() -> Settings:
    return Settings(
        target_url=os.getenv("TARGET_URL", "http://localhost:8080/healthz"),
        check_interval_seconds=int(os.getenv("CHECK_INTERVAL_SECONDS", "30")),
        report_every_n_checks=int(os.getenv("REPORT_EVERY_N_CHECKS", "10")),
        run_mode=os.getenv("RUN_MODE", "once"),
        db_host=os.getenv("DB_HOST", "localhost"),
        db_port=int(os.getenv("DB_PORT", "5432")),
        db_name=os.getenv("DB_NAME", "notesdb"),
        db_user=os.getenv("DB_USER", "notesuser"),
        db_password=os.getenv("DB_PASSWORD", "notessecret"),
    )


def check_api(target_url: str) -> CheckResult:
    started_at = time.perf_counter()
    checked_at = datetime.now(timezone.utc)

    try:
        response = requests.get(target_url, timeout=5)
        status_code = response.status_code
        success = status_code == 200
    except requests.RequestException:
        status_code = 0
        success = False

    latency_ms = int((time.perf_counter() - started_at) * 1000)

    return CheckResult(
        checked_at=checked_at,
        status_code=status_code,
        latency_ms=latency_ms,
        success=success,
    )


def insert_check(conn: psycopg.Connection, result: CheckResult) -> None:
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO api_checks (checked_at, status_code, latency_ms, success)
            VALUES (%s, %s, %s, %s)
            """,
            (
                result.checked_at,
                result.status_code,
                result.latency_ms,
                result.success,
            ),
        )
    conn.commit()


def fetch_recent_checks(conn: psycopg.Connection, limit: int = 100) -> pd.DataFrame:
    query = """
        SELECT checked_at, status_code, latency_ms, success
        FROM api_checks
        ORDER BY checked_at ASC
        LIMIT %s
    """
    return pd.read_sql(query, conn, params=(limit,))


def generate_reports(conn: psycopg.Connection) -> None:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    df = fetch_recent_checks(conn)
    if df.empty:
        print("Нет данных для отчётов")
        return

    df["checked_at"] = pd.to_datetime(df["checked_at"])

    df.to_csv(REPORTS_DIR / "summary.csv", index=False)

    plt.figure(figsize=(10, 5))
    plt.plot(df["checked_at"], df["latency_ms"])
    plt.xlabel("checked_at")
    plt.ylabel("latency_ms")
    plt.title("API latency over time")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(REPORTS_DIR / "latency.png")
    plt.close()

    success_counts = df["success"].value_counts().rename(index={True: "success", False: "fail"})
    plt.figure(figsize=(6, 4))
    success_counts.plot(kind="bar")
    plt.xlabel("result")
    plt.ylabel("count")
    plt.title("API checks success/fail")
    plt.tight_layout()
    plt.savefig(REPORTS_DIR / "success_rate.png")
    plt.close()

    stats = {
        "total_checks": int(len(df)),
        "successful_checks": int(df["success"].sum()),
        "failed_checks": int((~df["success"]).sum()),
        "avg_latency_ms": float(df["latency_ms"].mean()),
        "min_latency_ms": int(df["latency_ms"].min()),
        "max_latency_ms": int(df["latency_ms"].max()),
    }

    with open(REPORTS_DIR / "stats.json", "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2)


def run_once(conn: psycopg.Connection, settings: Settings) -> None:
    result = check_api(settings.target_url)
    insert_check(conn, result)
    print(asdict(result))
    generate_reports(conn)


def run_loop(conn: psycopg.Connection, settings: Settings) -> None:
    counter = 0

    while True:
        result = check_api(settings.target_url)
        insert_check(conn, result)
        counter += 1

        print(asdict(result))

        if counter % settings.report_every_n_checks == 0:
            generate_reports(conn)

        time.sleep(settings.check_interval_seconds)


def main() -> None:
    settings = load_settings()

    with psycopg.connect(settings.dsn) as conn:
        if settings.run_mode == "loop":
            run_loop(conn, settings)
        else:
            run_once(conn, settings)


if __name__ == "__main__":
    main()
