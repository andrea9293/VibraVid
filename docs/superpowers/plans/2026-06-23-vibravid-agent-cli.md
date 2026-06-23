# VibraVid Agent CLI Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create a CLI tool `vibravid-agent` with JSON output for AI agents to search, download, and manage media from VibraVid providers.

**Architecture:** Standalone CLI binary built with PyInstaller from `agent.py` entry point. Commands organized as subparsers in `VibraVid/agent/commands/`. Output formatted as JSON to stdout, logs to stderr. Background jobs managed via PID files in `~/.vibravid-agent/jobs/`.

**Tech Stack:** Python 3.9+, argparse, PyInstaller, JSON, subprocess (for job management)

---

## File Structure

```
VibraVid/
├── VibraVid/
│   ├── agent/
│   │   ├── __init__.py              # Empty init
│   │   ├── main.py                  # CLI dispatcher, output_json()
│   │   ├── output.py                # JSON formatter utilities
│   │   ├── job_manager.py           # Background job management
│   │   └── commands/
│   │       ├── __init__.py          # Empty init
│   │       ├── providers.py         # List providers
│   │       ├── search.py            # Search titles
│   │       ├── download.py          # Download media
│   │       ├── status.py            # Job status
│   │       ├── config.py            # Show/modify config
│   │       └── cancel.py            # Cancel job
├── agent.py                         # Entry point for PyInstaller
├── install.sh                       # Global installation script
└── .github/workflows/
    └── build.yml                    # Modified to build agent binary
```

---

### Task 1: Create Agent Package Structure

**Files:**
- Create: `VibraVid/agent/__init__.py`
- Create: `VibraVid/agent/commands/__init__.py`

- [ ] **Step 1: Create agent package init files**

```python
# VibraVid/agent/__init__.py
"""VibraVid Agent CLI for AI agents."""
```

```python
# VibraVid/agent/commands/__init__.py
"""Agent CLI commands."""
```

- [ ] **Step 2: Verify package structure**

Run: `python -c "from VibraVid.agent import commands; print('OK')"`
Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add VibraVid/agent/__init__.py VibraVid/agent/commands/__init__.py
git commit -m "feat: add agent package structure"
```

---

### Task 2: Implement JSON Output Formatter

**Files:**
- Create: `VibraVid/agent/output.py`
- Test: `tests/agent/test_output.py`

- [ ] **Step 1: Write failing test for output_json**

```python
# tests/agent/test_output.py
import json
import pytest
from VibraVid.agent.output import output_json

def test_output_json_success():
    """Test successful JSON output."""
    result = output_json(success=True, data={"test": "value"})
    assert result["success"] is True
    assert result["data"]["test"] == "value"
    assert result["error"] is None
    assert "metadata" in result
    assert "version" in result["metadata"]
    assert "timestamp" in result["metadata"]

def test_output_json_error():
    """Test error JSON output."""
    result = output_json(success=False, error="Test error")
    assert result["success"] is False
    assert result["data"] is None
    assert result["error"] == "Test error"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/agent/test_output.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'VibraVid.agent.output'"

- [ ] **Step 3: Implement output_json function**

```python
# VibraVid/agent/output.py
import sys
import json
from datetime import datetime
from typing import Any, Optional

from VibraVid.upload.version import __version__


def output_json(
    success: bool,
    data: Optional[Any] = None,
    error: Optional[str] = None,
    exit_on_call: bool = True
) -> dict:
    """
    Format and output JSON response.
    
    Args:
        success: Whether the operation succeeded
        data: Response data (optional)
        error: Error message (optional)
        exit_on_call: If True, exit with appropriate code
    
    Returns:
        The formatted JSON dict (for testing)
    """
    result = {
        "success": success,
        "data": data,
        "error": error,
        "metadata": {
            "version": __version__,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
    }
    
    print(json.dumps(result, indent=2, ensure_ascii=False))
    
    if exit_on_call:
        sys.exit(0 if success else 1)
    
    return result
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/agent/test_output.py::test_output_json_success -v`
Expected: PASS

Run: `pytest tests/agent/test_output.py::test_output_json_error -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add VibraVid/agent/output.py tests/agent/test_output.py
git commit -m "feat: implement JSON output formatter"
```

---

### Task 3: Implement Providers Command

**Files:**
- Create: `VibraVid/agent/commands/providers.py`
- Test: `tests/agent/commands/test_providers.py`

- [ ] **Step 1: Write failing test for providers command**

```python
# tests/agent/commands/test_providers.py
import pytest
from argparse import Namespace
from VibraVid.agent.commands.providers import register, execute

def test_providers_register():
    """Test that providers command registers correctly."""
    import argparse
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()
    register(subparsers)
    
    # Should be able to parse 'providers' command
    args = parser.parse_args(['providers'])
    assert hasattr(args, 'command')

def test_providers_execute():
    """Test that providers command executes without error."""
    args = Namespace(command='providers', available=False)
    # Should not raise exception
    try:
        execute(args)
    except SystemExit as e:
        # Expected to exit with 0
        assert e.code == 0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/agent/commands/test_providers.py -v`
Expected: FAIL with "ModuleNotFoundError"

- [ ] **Step 3: Implement providers command**

```python
# VibraVid/agent/commands/providers.py
from VibraVid.services._base import load_search_functions
from VibraVid.agent.output import output_json


def register(subparsers):
    """Register providers command."""
    parser = subparsers.add_parser("providers", help="List available providers")
    parser.add_argument(
        "--available",
        action="store_true",
        help="Only show available providers"
    )


def execute(args):
    """Execute providers command."""
    try:
        search_functions = load_search_functions()
        providers = []
        
        for func in search_functions.values():
            providers.append({
                "index": func.indice,
                "name": func.module_name,
                "category": func.use_for.lower(),
                "available": True
            })
        
        if args.available:
            providers = [p for p in providers if p["available"]]
        
        output_json(True, data={"providers": providers})
    except Exception as e:
        output_json(False, error=str(e))
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/agent/commands/test_providers.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add VibraVid/agent/commands/providers.py tests/agent/commands/test_providers.py
git commit -m "feat: implement providers command"
```

---

### Task 4: Implement Search Command

**Files:**
- Create: `VibraVid/agent/commands/search.py`
- Test: `tests/agent/commands/test_search.py`

- [ ] **Step 1: Write failing test for search command**

```python
# tests/agent/commands/test_search.py
import pytest
from argparse import Namespace
from VibraVid.agent.commands.search import register, execute

def test_search_register():
    """Test that search command registers correctly."""
    import argparse
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()
    register(subparsers)
    
    args = parser.parse_args(['search', '--query', 'test', '--provider', 'streamingcommunity'])
    assert args.query == 'test'
    assert args.provider == 'streamingcommunity'

def test_search_execute_missing_query():
    """Test search with missing query."""
    args = Namespace(command='search', query=None, provider='streamingcommunity')
    with pytest.raises(SystemExit) as exc_info:
        execute(args)
    assert exc_info.value.code == 1
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/agent/commands/test_search.py -v`
Expected: FAIL with "ModuleNotFoundError"

- [ ] **Step 3: Implement search command**

```python
# VibraVid/agent/commands/search.py
import sys
from VibraVid.services._base import load_search_functions
from VibraVid.agent.output import output_json


def register(subparsers):
    """Register search command."""
    parser = subparsers.add_parser("search", help="Search for titles")
    parser.add_argument("--query", "-q", required=True, help="Search query")
    parser.add_argument("--provider", "-p", required=True, help="Provider name or index")
    parser.add_argument("--year", help="Year filter (e.g., '2020' or '1990-2015')")
    parser.add_argument("--category", type=int, help="Category filter (1=Anime, 2=Movies/Series, 3=Series)")
    parser.add_argument("--auto-first", action="store_true", help="Auto-select first result")
    parser.add_argument("--global", dest="global_search", action="store_true", help="Search across all providers")


def execute(args):
    """Execute search command."""
    if not args.query:
        output_json(False, error="Query is required")
        return
    
    try:
        search_functions = load_search_functions()
        
        # Find provider
        provider_key = str(args.provider).strip().lower()
        search_func = None
        
        # Try by index
        if provider_key.isdigit():
            for func in search_functions.values():
                if str(func.indice) == provider_key:
                    search_func = func
                    break
        
        # Try by name
        if search_func is None:
            for func in search_functions.values():
                if func.module_name.lower() == provider_key:
                    search_func = func
                    break
        
        if search_func is None:
            output_json(False, error=f"Provider not found: {args.provider}")
            return
        
        # Perform search
        database = search_func(args.query, get_onlyDatabase=True)
        
        if not database or not hasattr(database, 'media_list') or not database.media_list:
            output_json(True, data={"query": args.query, "provider": args.provider, "results": []})
            return
        
        # Format results
        results = []
        for item in database.media_list:
            result_item = {
                "id": str(getattr(item, 'id', '')),
                "title": getattr(item, 'name', ''),
                "year": getattr(item, 'year', None),
                "type": getattr(item, 'type', 'unknown')
            }
            results.append(result_item)
        
        # Apply year filter if provided
        if args.year:
            results = [r for r in results if r.get('year') and str(r['year']) in args.year]
        
        output_json(True, data={
            "query": args.query,
            "provider": args.provider,
            "results": results
        })
        
    except Exception as e:
        output_json(False, error=str(e))
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/agent/commands/test_search.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add VibraVid/agent/commands/search.py tests/agent/commands/test_search.py
git commit -m "feat: implement search command"
```

---

### Task 5: Implement Job Manager

**Files:**
- Create: `VibraVid/agent/job_manager.py`
- Test: `tests/agent/test_job_manager.py`

- [ ] **Step 1: Write failing test for job manager**

```python
# tests/agent/test_job_manager.py
import pytest
import tempfile
import os
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

def test_job_manager_list_jobs():
    """Test listing jobs."""
    with tempfile.TemporaryDirectory() as tmpdir:
        jm = JobManager(tmpdir)
        jm.create_job(["cmd1"], "Job 1", "/tmp/1.mkv")
        jm.create_job(["cmd2"], "Job 2", "/tmp/2.mkv")
        
        jobs = jm.list_jobs()
        assert len(jobs) == 2
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/agent/test_job_manager.py -v`
Expected: FAIL with "ModuleNotFoundError"

- [ ] **Step 3: Implement job manager**

```python
# VibraVid/agent/job_manager.py
import os
import json
import signal
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict


class JobManager:
    """Manage background download jobs."""
    
    def __init__(self, jobs_dir: Optional[str] = None):
        """
        Initialize job manager.
        
        Args:
            jobs_dir: Directory to store job files. Defaults to ~/.vibravid-agent/jobs/
        """
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
        """
        Create a new job.
        
        Args:
            command: Command that started the job
            title: Job title
            output_path: Output file path
            pid: Process ID (optional)
        
        Returns:
            Job ID
        """
        job_id = f"job_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        job_data = {
            "job_id": job_id,
            "pid": pid,
            "status": "started",
            "started_at": datetime.utcnow().isoformat() + "Z",
            "command": command,
            "title": title,
            "output_path": output_path,
            "progress": 0.0,
            "error": None
        }
        
        job_file = self.jobs_dir / f"{job_id}.json"
        with open(job_file, 'w') as f:
            json.dump(job_data, f, indent=2)
        
        return job_id
    
    def get_job(self, job_id: str) -> Optional[Dict]:
        """
        Get job data.
        
        Args:
            job_id: Job ID
        
        Returns:
            Job data dict or None
        """
        job_file = self.jobs_dir / f"{job_id}.json"
        if not job_file.exists():
            return None
        
        with open(job_file, 'r') as f:
            return json.load(f)
    
    def update_job(self, job_id: str, **kwargs):
        """
        Update job data.
        
        Args:
            job_id: Job ID
            **kwargs: Fields to update
        """
        job_data = self.get_job(job_id)
        if job_data is None:
            raise ValueError(f"Job not found: {job_id}")
        
        job_data.update(kwargs)
        
        job_file = self.jobs_dir / f"{job_id}.json"
        with open(job_file, 'w') as f:
            json.dump(job_data, f, indent=2)
    
    def list_jobs(self) -> List[Dict]:
        """
        List all jobs.
        
        Returns:
            List of job data dicts
        """
        jobs = []
        for job_file in self.jobs_dir.glob("job_*.json"):
            with open(job_file, 'r') as f:
                jobs.append(json.load(f))
        return jobs
    
    def cancel_job(self, job_id: str) -> bool:
        """
        Cancel a job by sending SIGTERM.
        
        Args:
            job_id: Job ID
        
        Returns:
            True if cancelled, False otherwise
        """
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/agent/test_job_manager.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add VibraVid/agent/job_manager.py tests/agent/test_job_manager.py
git commit -m "feat: implement job manager for background downloads"
```

---

### Task 6: Implement Download Command

**Files:**
- Create: `VibraVid/agent/commands/download.py`

- [ ] **Step 1: Implement download command**

```python
# VibraVid/agent/commands/download.py
import os
import sys
import subprocess
from VibraVid.agent.job_manager import JobManager
from VibraVid.agent.output import output_json


def register(subparsers):
    """Register download command."""
    parser = subparsers.add_parser("download", help="Download media")
    
    # Provider-based download
    parser.add_argument("--provider", "-p", help="Provider name or index")
    parser.add_argument("--id", help="Media ID to download")
    
    # Direct URL download
    parser.add_argument("--url", help="Direct URL to download")
    
    # Selection options
    parser.add_argument("--season", help="Season selection (e.g., '1', '1-3', '*')")
    parser.add_argument("--episode", help="Episode selection (e.g., '1', '1-5', '*')")
    parser.add_argument("--year", help="Year filter")
    
    # Track selection
    parser.add_argument("--video", "-sv", help="Video track filter (e.g., 'best', '1080')")
    parser.add_argument("--audio", "-sa", help="Audio track filter (e.g., 'ita|eng')")
    parser.add_argument("--subtitle", "-ss", help="Subtitle track filter (e.g., 'ita|eng')")
    parser.add_argument("--extension", help="Output container (mkv, mp4)")
    
    # Direct download options
    parser.add_argument("--header", action="append", help="HTTP header (repeatable)")
    parser.add_argument("--license-url", help="DRM license server URL")
    parser.add_argument("--key", action="append", help="Decryption key KID:KEY (repeatable)")
    parser.add_argument("--drm", choices=["widevine", "playready", "auto"], default="auto", help="DRM system")
    parser.add_argument("--max-segments", type=int, help="Limit to N segments")
    parser.add_argument("--max-time", help="Limit duration (HH:MM:SS or seconds)")
    
    # Execution options
    parser.add_argument("--background", action="store_true", help="Run in background")
    parser.add_argument("--use-proxy", action="store_true", help="Use configured proxy")


def execute(args):
    """Execute download command."""
    try:
        # Build command for subprocess
        cmd = [sys.executable, "-m", "VibraVid"]
        
        if args.url:
            # Direct URL download
            cmd.extend(["--down", args.url])
            if args.header:
                for h in args.header:
                    cmd.extend(["--headers", h])
            if args.license_url:
                cmd.extend(["--license-url", args.license_url])
            if args.key:
                for k in args.key:
                    cmd.extend(["--key", k])
            cmd.extend(["--drm", args.drm])
            if args.max_segments:
                cmd.extend(["--max-segments", str(args.max_segments)])
            if args.max_time:
                cmd.extend(["--max-time", args.max_time])
        elif args.provider and args.id:
            # Provider-based download
            cmd.extend(["--site", args.provider, "--search", args.id, "--auto-first"])
            if args.season:
                cmd.extend(["--season", args.season])
            if args.episode:
                cmd.extend(["--episode", args.episode])
            if args.year:
                cmd.extend(["--year", args.year])
        else:
            output_json(False, error="Either --url or (--provider and --id) required")
            return
        
        # Track selection
        if args.video:
            cmd.extend(["-sv", args.video])
        if args.audio:
            cmd.extend(["-sa", args.audio])
        if args.subtitle:
            cmd.extend(["-ss", args.subtitle])
        if args.extension:
            cmd.extend(["--extension", args.extension])
        if args.use_proxy:
            cmd.append("--use_proxy")
        
        # Close console after download
        cmd.extend(["--close-console", "true"])
        
        if args.background:
            # Start in background
            job_manager = JobManager()
            job_id = job_manager.create_job(
                command=cmd,
                title=args.url or args.id,
                output_path="pending"
            )
            
            # Start subprocess
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            
            job_manager.update_job(job_id, pid=process.pid)
            
            output_json(True, data={
                "job_id": job_id,
                "status": "started",
                "pid": process.pid
            })
        else:
            # Run in foreground
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                output_json(True, data={
                    "status": "completed",
                    "stdout": result.stdout,
                    "stderr": result.stderr
                })
            else:
                output_json(False, error=f"Download failed: {result.stderr}")
    
    except Exception as e:
        output_json(False, error=str(e))
```

- [ ] **Step 2: Commit**

```bash
git add VibraVid/agent/commands/download.py
git commit -m "feat: implement download command"
```

---

### Task 7: Implement Status and Cancel Commands

**Files:**
- Create: `VibraVid/agent/commands/status.py`
- Create: `VibraVid/agent/commands/cancel.py`

- [ ] **Step 1: Implement status command**

```python
# VibraVid/agent/commands/status.py
from VibraVid.agent.job_manager import JobManager
from VibraVid.agent.output import output_json


def register(subparsers):
    """Register status command."""
    parser = subparsers.add_parser("status", help="Check job status")
    parser.add_argument("--job-id", help="Specific job ID to check")
    parser.add_argument("--all", action="store_true", help="Show all jobs")


def execute(args):
    """Execute status command."""
    try:
        job_manager = JobManager()
        
        if args.job_id:
            # Show specific job
            job = job_manager.get_job(args.job_id)
            if job is None:
                output_json(False, error=f"Job not found: {args.job_id}")
                return
            
            output_json(True, data=job)
        
        elif args.all:
            # Show all jobs
            jobs = job_manager.list_jobs()
            output_json(True, data={"jobs": jobs})
        
        else:
            # Show recent jobs (last 10)
            jobs = job_manager.list_jobs()
            jobs = sorted(jobs, key=lambda j: j.get("started_at", ""), reverse=True)[:10]
            output_json(True, data={"jobs": jobs})
    
    except Exception as e:
        output_json(False, error=str(e))
```

- [ ] **Step 2: Implement cancel command**

```python
# VibraVid/agent/commands/cancel.py
from VibraVid.agent.job_manager import JobManager
from VibraVid.agent.output import output_json


def register(subparsers):
    """Register cancel command."""
    parser = subparsers.add_parser("cancel", help="Cancel a job")
    parser.add_argument("--job-id", required=True, help="Job ID to cancel")


def execute(args):
    """Execute cancel command."""
    try:
        job_manager = JobManager()
        
        success = job_manager.cancel_job(args.job_id)
        
        if success:
            output_json(True, data={
                "job_id": args.job_id,
                "status": "cancelled"
            })
        else:
            output_json(False, error=f"Failed to cancel job: {args.job_id}")
    
    except Exception as e:
        output_json(False, error=str(e))
```

- [ ] **Step 3: Commit**

```bash
git add VibraVid/agent/commands/status.py VibraVid/agent/commands/cancel.py
git commit -m "feat: implement status and cancel commands"
```

---

### Task 8: Implement Config Command

**Files:**
- Create: `VibraVid/agent/commands/config.py`

- [ ] **Step 1: Implement config command**

```python
# VibraVid/agent/commands/config.py
from VibraVid.utils import config_manager
from VibraVid.agent.output import output_json


def register(subparsers):
    """Register config command."""
    parser = subparsers.add_parser("config", help="Show or modify configuration")
    parser.add_argument("--show", action="store_true", help="Show full configuration")
    parser.add_argument("--get", help="Get specific config value (e.g., 'DOWNLOAD.thread_count')")
    parser.add_argument("--set", help="Set config value (e.g., 'DOWNLOAD.thread_count=20')")
    parser.add_argument("--dependencies", action="store_true", help="Show dependency paths")


def execute(args):
    """Execute config command."""
    try:
        if args.dependencies:
            # Show dependency paths
            from VibraVid.setup.system import (
                get_ffmpeg_path, get_ffprobe_path, get_bento4_decrypt_path,
                get_wvd_path, get_prd_path
            )
            
            deps = {
                "ffmpeg": get_ffmpeg_path(),
                "ffprobe": get_ffprobe_path(),
                "bento4": get_bento4_decrypt_path(),
                "widevine_device": get_wvd_path(),
                "playready_device": get_prd_path()
            }
            
            output_json(True, data={"dependencies": deps})
        
        elif args.get:
            # Get specific value
            parts = args.get.split(".")
            if len(parts) != 2:
                output_json(False, error="Invalid format. Use SECTION.KEY")
                return
            
            section, key = parts
            value = config_manager.config.get(section, key, None)
            output_json(True, data={"key": args.get, "value": value})
        
        elif args.set:
            # Set value
            if "=" not in args.set:
                output_json(False, error="Invalid format. Use SECTION.KEY=VALUE")
                return
            
            key_part, value_part = args.set.split("=", 1)
            parts = key_part.split(".")
            if len(parts) != 2:
                output_json(False, error="Invalid format. Use SECTION.KEY=VALUE")
                return
            
            section, key = parts
            
            # Try to parse value as JSON (for numbers, booleans, etc.)
            try:
                import json
                value = json.loads(value_part)
            except:
                value = value_part
            
            config_manager.config.set_key(section, key, value)
            config_manager.save_config()
            
            output_json(True, data={"key": key_part, "value": value})
        
        else:
            # Show full config
            output_json(True, data={"config": config_manager._config_data})
    
    except Exception as e:
        output_json(False, error=str(e))
```

- [ ] **Step 2: Commit**

```bash
git add VibraVid/agent/commands/config.py
git commit -m "feat: implement config command"
```

---

### Task 9: Implement Main CLI Dispatcher

**Files:**
- Create: `VibraVid/agent/main.py`
- Create: `agent.py`

- [ ] **Step 1: Implement main dispatcher**

```python
# VibraVid/agent/main.py
import sys
import argparse

from VibraVid.agent.commands import providers, search, download, status, config, cancel
from VibraVid.agent.output import output_json
from VibraVid.upload.version import __version__, __title__


def main():
    """Main entry point for vibravid-agent CLI."""
    parser = argparse.ArgumentParser(
        prog="vibravid-agent",
        description="VibraVid CLI for AI agents - structured JSON output"
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"{__title__} {__version__}"
    )
    
    subparsers = parser.add_subparsers(dest="command", required=True)
    
    # Register commands
    providers.register(subparsers)
    search.register(subparsers)
    download.register(subparsers)
    status.register(subparsers)
    cancel.register(subparsers)
    config.register(subparsers)
    
    args = parser.parse_args()
    
    try:
        # Dispatch to command
        commands = {
            "providers": providers.execute,
            "search": search.execute,
            "download": download.execute,
            "status": status.execute,
            "cancel": cancel.execute,
            "config": config.execute,
        }
        
        commands[args.command](args)
    
    except Exception as e:
        output_json(False, error=str(e))
```

- [ ] **Step 2: Create entry point**

```python
# agent.py
#!/usr/bin/env python3
"""Entry point for vibravid-agent CLI."""

from VibraVid.agent.main import main

if __name__ == "__main__":
    main()
```

- [ ] **Step 3: Test CLI locally**

Run: `python agent.py --version`
Expected: `VibraVid <version>`

Run: `python agent.py providers`
Expected: JSON output with providers list

- [ ] **Step 4: Commit**

```bash
git add VibraVid/agent/main.py agent.py
git commit -m "feat: implement main CLI dispatcher"
```

---

### Task 10: Create Installation Script

**Files:**
- Create: `install.sh`

- [ ] **Step 1: Create installation script**

```bash
#!/bin/bash
set -e

REPO="andrea9293/VibraVid"
BINARY_NAME="vibravid-agent"
INSTALL_DIR="${HOME}/.local/bin"

# Detect OS and architecture
OS=$(uname -s | tr '[:upper:]' '[:lower:]')
ARCH=$(uname -m)

case "$ARCH" in
    x86_64) ARCH="x64" ;;
    aarch64|arm64) ARCH="arm64" ;;
    *) echo "Unsupported architecture: $ARCH"; exit 1 ;;
esac

# Map OS/arch to GitHub asset name
case "$OS" in
    linux) ASSET_PATTERN="linux.*${ARCH}" ;;
    darwin) ASSET_PATTERN="mac.*${ARCH}" ;;
    mingw*|msys*|cygwin*) ASSET_PATTERN="win.*x64.exe"; BINARY_NAME+=".exe" ;;
    *) echo "Unsupported OS: $OS"; exit 1 ;;
esac

# Create installation directory
mkdir -p "$INSTALL_DIR"

# Download latest release
echo "Downloading latest release from ${REPO}..."
LATEST_URL=$(curl -sL "https://api.github.com/repos/${REPO}/releases/latest" | \
    grep "browser_download_url" | \
    grep -E "$ASSET_PATTERN" | \
    head -1 | \
    cut -d '"' -f 4)

if [ -z "$LATEST_URL" ]; then
    echo "Error: no asset found for ${OS}/${ARCH}"
    exit 1
fi

curl -L "$LATEST_URL" -o "${INSTALL_DIR}/${BINARY_NAME}"
chmod +x "${INSTALL_DIR}/${BINARY_NAME}"

# Verify installation
if ! command -v "$BINARY_NAME" &> /dev/null; then
    echo "Warning: ${INSTALL_DIR} is not in PATH"
    echo "Add to your ~/.bashrc or ~/.zshrc:"
    echo "  export PATH=\"${INSTALL_DIR}:\$PATH\""
fi

echo "✓ ${BINARY_NAME} installed successfully in ${INSTALL_DIR}/${BINARY_NAME}"
echo "Run '${BINARY_NAME} --version' to verify"
```

- [ ] **Step 2: Make script executable**

Run: `chmod +x install.sh`

- [ ] **Step 3: Commit**

```bash
git add install.sh
git commit -m "feat: add global installation script"
```

---

### Task 11: Update Build Workflow

**Files:**
- Modify: `.github/workflows/build.yml`

- [ ] **Step 1: Add agent binary build step**

After the existing PyInstaller build step (around line 190), add:

```yaml
            - name: Build agent executable with PyInstaller
              shell: bash
              run: |
                pyinstaller --onefile \
                --hidden-import=ua_generator \
                --hidden-import=bs4 \
                --hidden-import=rich \
                --hidden-import=rich._unicode_data \
                --collect-all rich \
                --hidden-import=unidecode \
                --hidden-import=editorconfig \
                --hidden-import=six \
                --hidden-import=pathvalidate \
                --hidden-import=xml.etree.ElementTree \
                --hidden-import=mutagen \
                --hidden-import=pywidevine \
                --hidden-import=pyplayready \
                --hidden-import=ttconv \
                --collect-all ttconv \
                --collect-all mutagen \
                --hidden-import=curl_cffi \
                --hidden-import=_cffi_backend \
                --collect-all curl_cffi \
                --hidden-import=Cryptodome \
                --hidden-import=Cryptodome.Cipher \
                --hidden-import=Cryptodome.Cipher.AES \
                --hidden-import=Cryptodome.Util \
                --hidden-import=Cryptodome.Util.Padding \
                --collect-all Cryptodome \
                --exclude-module Cryptodome.SelfTest \
                --additional-hooks-dir=pyinstaller/hooks \
                --add-data "VibraVid${{ matrix.separator }}VibraVid" \
                --name=${{ matrix.artifact_name }}-agent agent.py
```

- [ ] **Step 2: Update artifact upload**

Modify the artifact upload step to include both binaries:

```yaml
            - name: Upload executables to Artifacts
              uses: actions/upload-artifact@v4
              with:
                  name: ${{ matrix.artifact_name }}-bundle
                  path: |
                      dist/${{ matrix.executable }}
                      dist/${{ matrix.executable }}-agent
```

- [ ] **Step 3: Commit**

```bash
git add .github/workflows/build.yml
git commit -m "feat: build agent binary in CI workflow"
```

---

### Task 12: Create OpenCode Skill

**Files:**
- Create: `skills/vibravid-agent/SKILL.md`

- [ ] **Step 1: Create skill documentation**

```markdown
# VibraVid Agent Skill

Use this skill to interact with VibraVid media downloader via CLI for AI agents.

## Installation

```bash
curl -sL https://raw.githubusercontent.com/andrea9293/VibraVid/main/install.sh | bash
```

## Usage

All commands output JSON to stdout. Exit code 0 = success, 1 = error.

### List Providers

```bash
vibravid-agent providers
```

### Search Titles

```bash
vibravid-agent search --query "interstellar" --provider streamingcommunity
```

### Download Media

**Provider-based:**
```bash
vibravid-agent download --provider streamingcommunity --id "123" \
  --season 1 --episode "1-5" --video 1080 --audio "ita|eng"
```

**Direct URL:**
```bash
vibravid-agent download --url "https://example.com/video.m3u8" \
  --header "User-Agent:Mozilla" --key "KID:KEY"
```

**Background download:**
```bash
vibravid-agent download --provider streamingcommunity --id "123" --background
```

### Check Job Status

```bash
vibravid-agent status --job-id job_20260623_103000
vibravid-agent status --all
```

### Cancel Job

```bash
vibravid-agent cancel --job-id job_20260623_103000
```

### Configuration

```bash
vibravid-agent config --show
vibravid-agent config --get DOWNLOAD.thread_count
vibravid-agent config --set DOWNLOAD.thread_count=20
vibravid-agent config --dependencies
```

## Output Format

```json
{
  "success": true,
  "data": {...},
  "error": null,
  "metadata": {
    "version": "1.0.0",
    "timestamp": "2026-06-23T10:30:00Z"
  }
}
```

## Workflow Example

1. List providers: `vibravid-agent providers`
2. Search: `vibravid-agent search --query "title" --provider streamingcommunity`
3. Download: `vibravid-agent download --provider streamingcommunity --id "123" --background`
4. Monitor: `vibravid-agent status --job-id <job_id>`
```

- [ ] **Step 2: Commit**

```bash
git add skills/vibravid-agent/SKILL.md
git commit -m "docs: add OpenCode skill for AI agents"
```

---

## Summary

This plan implements a complete CLI tool `vibravid-agent` with:
- 6 commands: providers, search, download, status, config, cancel
- JSON output for all commands
- Background job management
- Global installation via bash script
- OpenCode skill for AI agent integration
- CI/CD integration for binary builds

Total estimated time: 2-3 hours
