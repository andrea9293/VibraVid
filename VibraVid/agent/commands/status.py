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
            job = job_manager.get_job(args.job_id)
            if job is None:
                output_json(False, error=f"Job not found: {args.job_id}")
                return
            output_json(True, data=job)

        elif args.all:
            jobs = job_manager.list_jobs()
            output_json(True, data={"jobs": jobs})

        else:
            jobs = job_manager.list_jobs()
            jobs = sorted(jobs, key=lambda j: j.get("started_at", ""), reverse=True)[:10]
            output_json(True, data={"jobs": jobs})

    except Exception as e:
        output_json(False, error=str(e))
