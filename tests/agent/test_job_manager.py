import pytest
import tempfile
import os
import json
from pathlib import Path
from VibraVid.agent.job_manager import JobManager

def test_job_manager_init():
    """Test job manager initialization."""
    with tempfile.TemporaryDirectory() as tmpdir:
        jm = JobManager(tmpdir)
        assert jm.jobs_dir == Path(tmpdir)
        assert jm.jobs_dir.exists()

def test_job_manager_create_job():
    """Test creating a job."""
    with tempfile.TemporaryDirectory() as tmpdir:
        jm = JobManager(tmpdir)
        job_id = jm.create_job(
            command=["test", "command"],
            title="Test Job",
            output_path="/tmp/test.mkv"
        )
        assert job_id.startswith("job_")
        assert jm.get_job(job_id) is not None
        assert jm.get_job("nonexistent") is None

def test_job_manager_list_jobs():
    """Test listing jobs."""
    with tempfile.TemporaryDirectory() as tmpdir:
        jm = JobManager(tmpdir)
        jm.create_job(["cmd1"], "Job 1", "/tmp/1.mkv")
        jm.create_job(["cmd2"], "Job 2", "/tmp/2.mkv")
        jobs = jm.list_jobs()
        assert len(jobs) == 2

def test_job_manager_update_job():
    """Test updating a job."""
    with tempfile.TemporaryDirectory() as tmpdir:
        jm = JobManager(tmpdir)
        job_id = jm.create_job(["cmd"], "Test", "/tmp/test.mkv")
        jm.update_job(job_id, progress=50.0, status="downloading")
        job = jm.get_job(job_id)
        assert job["progress"] == 50.0
        assert job["status"] == "downloading"

def test_job_manager_cancel_job_no_pid():
    """Test cancelling a job without PID (should not raise)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        jm = JobManager(tmpdir)
        job_id = jm.create_job(["cmd"], "Test", "/tmp/test.mkv")
        result = jm.cancel_job(job_id)
        assert result is False
