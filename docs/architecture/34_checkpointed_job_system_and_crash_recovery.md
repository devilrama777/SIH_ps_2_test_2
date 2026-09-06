# Phase 34: Checkpointed 12-Stage Job System with Crash Recovery

## 1. Overview
Section 27 of the CIL Local AI Report Generator specification mandates that massive report generation workflows—spanning up to 300–400 pages and requiring thousands of document extraction and normalization operations—must be fully resumable, pausing and checkpointing across process boundaries. In the event of an unexpected crash, power interruption, or operating system reboot, no already-executed stage should ever need to re-run.

Phase 34 implements:
1. **Persistent 12-Stage Checkpoints**:
   - Each completed pipeline stage (`DISCOVERY`, `INGESTION`, `OCR`, `EXTRACTION`, `NORMALIZATION`, `INDEXING`, `PLANNING`, `GENERATION`, `VALIDATION`, `COMPOSITION`, `RENDERING`, `READY_FOR_REVIEW`) atomically persists its state, intermediate file references, and checkpoint metadata into SQLite with WAL mode.
2. **Automated Crash Recovery**:
   - `ReportJobManager.recover_crashed_jobs(auto_resume=True)` scans for jobs stranded in `RUNNING` status by previous terminated instances.
   - Restores the job state from its latest validated stage checkpoint and continues sequentially without re-processing earlier stages.
   - Logs an immutable security audit event tracking the crash detection and recovery lifecycle.
3. **Dedicated REST Endpoints**:
   - `POST /api/v1/report-jobs/create`: Create and start 12-stage job.
   - `GET /api/v1/report-jobs/{job_id}`: Retrieve real-time progress and stage checkpoints.
   - `POST /api/v1/report-jobs/{job_id}/pause`: Safely pause job at next stage boundary.
   - `POST /api/v1/report-jobs/{job_id}/resume`: Resume from saved checkpoint.
   - `POST /api/v1/report-jobs/recover`: Scan and restore all orphaned jobs.

## 2. Component Workflow

```
[System Crash / Sudden Termination during Stage N]
                       │
                       ▼
        [System / Service Reboot]
                       │
                       ▼
   [ReportJobManager.recover_crashed_jobs()]
                       │
       ┌───────────────┴───────────────┐
       ▼                               ▼
[Inspect SQLite WAL]        [Log Audit Event]
  Find status='running'       "crash_recovery_detected"
       │
       ▼
[Load Completed Stages 1..N-1]
       │
       ▼
[Resume at Stage N without re-executing 1..N-1]
       │
       ▼
[Complete remaining stages -> COMPLETED (100%)]
```

## 3. Verification & Compliance
- Full integration tests via `tests/orchestrator/test_job_checkpoint_recovery.py`:
  - `test_job_creation_and_stage_execution`: verified 12 stages run sequentially to 100%.
  - `test_job_pause_and_resume`: verified clean pause and resumption.
  - `test_crash_recovery_simulation`: simulated process death with state abandoned at stage 4; a newly instantiated manager successfully recovered and completed stages 5 through 12.
  - `test_jobs_rest_api`: validated REST endpoints under `/api/v1/report-jobs/`.
- 100% test pass rate achieved.
