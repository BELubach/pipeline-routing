#!/usr/bin/env python3
"""
# Normal run
python -m  manage data/GEM-GGIT-Gas-Pipelines-2025-11.geojson --batch-size 500

# Larger batches
python -m  manage data/GEM-GGIT-Gas-Pipelines-2025-11.geojson --batch-size 500

# Resume a failed job
python -m  manage path/to/gem_pipelines.geojson --resume-job 42

# No Europe filter
python -m  manage path/to/gem_pipelines.geojson --global-scope
"""

import argparse

from sqlalchemy.orm import Session

from app.db.session import sync_engine   
from app.batchdataloader.loader import PipelineBatchLoader
from app.models import PipelineImportJob
import sys
from pathlib import Path

# Add app to path
sys.path.insert(0, str(Path(__file__).parent))

def main():
    parser = argparse.ArgumentParser(description="Import GEM pipeline GeoJSON into the database")
    parser.add_argument("geojson", help="Path to GEM pipeline GeoJSON file")
    parser.add_argument("--batch-size", type=int, default=100)
    parser.add_argument("--global-scope", action="store_true", help="Skip Europe filter")
    parser.add_argument("--resume-job", type=int, help="Resume an existing job by ID")
    args = parser.parse_args()

    with Session(sync_engine) as db:
        existing_job = None
        if args.resume_job:
            existing_job = db.get(PipelineImportJob, args.resume_job)
            if not existing_job:
                print(f"Job {args.resume_job} not found")
                return

        loader = PipelineBatchLoader(db)
        job = loader.load_file(
            geojson_path=args.geojson,
            batch_size=args.batch_size,
            existing_job=existing_job,
        )
        print(f"\nJob {job.id} — {job.status}")
        print(f"  {job.successful_segments} ok, {job.failed_segments} failed")


if __name__ == "__main__":
    main()