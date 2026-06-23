import os
import json
import signal
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional, List, Dict


class JobManager:
    """Manage background download jobs."""

    def __init__(self, jobs_dir: Optional[str] = None):
        if jobs_dir is None:
            jobs_dir = os.path.expanduser("~/.vibravid-agent/jobs")
        self.jobs_dir = Path(jobs_dir)
        self.jobs_dir.mkdir(parents=True, exist_ok=True)

    def create_job(
        self,
        command: List[str],
        title: str,
        output_path: str,
        pid: Optional[int] = None
    ) -> str:
        job_id = f"job_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        job_data = {
            "job_id": job_id,
            "pid": pid,
            "status": "started",
            "started_at": datetime.now(timezone.utc).isoformat(),
            "command": command,
            "title": title,
            "output_path": output_path,
            "progress": 0.0,
            "error": None,
        }
        job_file = self.jobs_dir / f"{job_id}.json"
        with open(job_file, 'w') as f:
            json.dump(job_data, f, indent=2)
        return job_id

    def get_job(self, job_id: str) -> Optional[Dict]:
        job_file = self.jobs_dir / f"{job_id}.json"
        if not job_file.exists():
            return None
        with open(job_file, 'r') as f:
            return json.load(f)

    def update_job(self, job_id: str, **kwargs):
        job_data = self.get_job(job_id)
        if job_data is None:
            raise ValueError(f"Job not found: {job_id}")
        job_data.update(kwargs)
        job_file = self.jobs_dir / f"{job_id}.json"
        with open(job_file, 'w') as f:
            json.dump(job_data, f, indent=2)

    def list_jobs(self) -> List[Dict]:
        jobs = []
        for job_file in sorted(self.jobs_dir.glob("job_*.json")):
            with open(job_file, 'r') as f:
                jobs.append(json.load(f))
        return jobs

    def cancel_job(self, job_id: str) -> bool:
        job_data = self.get_job(job_id)
        if job_data is None:
            return False
        pid = job_data.get("pid")
        if pid is None:
            return False
        try:
            os.kill(pid, signal.SIGTERM)
            self.update_job(job_id, status="cancelled")
            return True
        except ProcessLookupError:
            self.update_job(job_id, status="finished")
            return False
