"""
Multi-Agent Due Diligence AI — Backend
Built for Mistral AI Hackathon
"""

import os
import json
import time
import asyncio
from typing import Optional
from pathlib import Path

from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import uvicorn

from agents import DueDiligenceOrchestrator
from document_processor import DocumentProcessor

app = FastAPI(title="Due Diligence AI", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory job store (use Redis for production)
jobs: dict = {}

class JobStatus(BaseModel):
    job_id: str
    status: str  # queued | processing | done | error
    progress: int  # 0-100
    current_agent: Optional[str] = None
    result: Optional[dict] = None
    error: Optional[str] = None


@app.get("/")
def root():
    return {"message": "Due Diligence AI API", "version": "1.0.0"}


@app.post("/analyze")
async def analyze_documents(
    background_tasks: BackgroundTasks,
    company_name: str = "Unknown Company",
    files: list[UploadFile] = File(...)
):
    if not files:
        raise HTTPException(status_code=400, detail="No files uploaded")

    job_id = f"job_{int(time.time() * 1000)}"
    jobs[job_id] = {
        "status": "queued",
        "progress": 0,
        "current_agent": None,
        "result": None,
        "error": None
    }

    # Read file contents before background task
    file_data = []
    for f in files:
        content = await f.read()
        file_data.append({"filename": f.filename, "content": content, "content_type": f.content_type})

    background_tasks.add_task(run_analysis, job_id, company_name, file_data)
    return {"job_id": job_id}


@app.get("/status/{job_id}", response_model=JobStatus)
def get_status(job_id: str):
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    job = jobs[job_id]
    return JobStatus(job_id=job_id, **job)


async def run_analysis(job_id: str, company_name: str, file_data: list):
    try:
        jobs[job_id]["status"] = "processing"

        def progress_callback(progress: int, agent_name: str):
            jobs[job_id]["progress"] = progress
            jobs[job_id]["current_agent"] = agent_name

        processor = DocumentProcessor()
        documents = processor.process_files(file_data)

        orchestrator = DueDiligenceOrchestrator(progress_callback=progress_callback)
        result = await orchestrator.run(company_name=company_name, documents=documents)

        jobs[job_id]["status"] = "done"
        jobs[job_id]["progress"] = 100
        jobs[job_id]["current_agent"] = None
        jobs[job_id]["result"] = result

    except Exception as e:
        jobs[job_id]["status"] = "error"
        jobs[job_id]["error"] = str(e)
        print(f"Error in job {job_id}: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
