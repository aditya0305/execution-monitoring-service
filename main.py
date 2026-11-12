
import os
import requests

from datetime import datetime, timezone
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc

from database import engine, get_db, Base
from models import Execution
from schemas import ExecutionCreate, ExecutionResponse

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Execution Monitoring & Auto-Recovery Service",
    version="1.0.0"
)

REGISTRY_URL = os.getenv(
    "REGISTRY_SERVICE_URL",
    "http://localhost:8001"
)

@app.get("/health")
def health():
    return {
        "service": "execution-monitoring",
        "status": "healthy"
    }


def get_pipeline(pipeline_id: int):
    try:
        response = requests.get(
            f"{REGISTRY_URL}/pipelines/{pipeline_id}",
            timeout=5
        )
    except requests.RequestException:
        raise HTTPException(
            status_code=503,
            detail="Pipeline Registry Service unavailable"
        )

    if response.status_code == 404:
        raise HTTPException(
            status_code=404,
            detail="Pipeline not found in Registry Service"
        )

    if response.status_code != 200:
        raise HTTPException(
            status_code=502,
            detail="Registry Service returned an error"
        )

    return response.json()


@app.post(
    "/executions",
    response_model=ExecutionResponse,
    status_code=201
)
def start_execution(
    request: ExecutionCreate,
    db: Session = Depends(get_db)
):
    pipeline = get_pipeline(request.pipeline_id)

    if not pipeline["is_active"]:
        raise HTTPException(
            status_code=400,
            detail="Pipeline is disabled"
        )

    max_retries = pipeline["max_retries"]

    execution = Execution(
        pipeline_id=request.pipeline_id,
        pipeline_name=pipeline["pipeline_name"],
        status="RUNNING",
        retry_count=0,
        simulate_failure=request.simulate_failure
    )

    db.add(execution)
    db.commit()
    db.refresh(execution)

    # Simulated pipeline execution:
    # Initial attempt + configured retry attempts.
    for attempt in range(max_retries + 1):

        should_fail = (
            request.simulate_failure
            and attempt < request.fail_attempts
        )

        execution.retry_count = attempt

        if not should_fail:
            execution.status = "SUCCESS"
            execution.error_message = None
            break

        execution.status = "FAILED"
        execution.error_message = (
            f"Simulated failure on attempt {attempt + 1}"
        )

    execution.end_time = datetime.now(timezone.utc)

    db.commit()
    db.refresh(execution)

    return execution


@app.get(
    "/executions",
    response_model=list[ExecutionResponse]
)
def list_executions(db: Session = Depends(get_db)):
    return (
        db.query(Execution)
        .order_by(desc(Execution.id))
        .all()
    )


@app.get(
    "/executions/{execution_id}",
    response_model=ExecutionResponse
)
def get_execution(
    execution_id: int,
    db: Session = Depends(get_db)
):
    execution = db.get(Execution, execution_id)

    if not execution:
        raise HTTPException(
            status_code=404,
            detail="Execution not found"
        )

    return execution


@app.get(
    "/pipelines/{pipeline_id}/executions",
    response_model=list[ExecutionResponse]
)
def get_pipeline_history(
    pipeline_id: int,
    db: Session = Depends(get_db)
):
    return (
        db.query(Execution)
        .filter(Execution.pipeline_id == pipeline_id)
        .order_by(desc(Execution.id))
        .all()
    )
