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
