import argparse

from VibraVid.agent.job_manager import JobManager
from VibraVid.agent.output import output_json

CANCEL_EXAMPLES = """examples:
  vibravid-agent cancel --job-id job_20260623_193000_123456"""


def register(subparsers):
    parser = subparsers.add_parser(
        "cancel",
        help="Cancel a running job",
        description="Cancel a background download job by its ID. Sends SIGTERM to the job process.",
        epilog=CANCEL_EXAMPLES,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
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
