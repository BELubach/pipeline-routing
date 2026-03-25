"""
Example usage of the pipeline batch loader.
Run this script to import pipeline data from GeoJSON.

Usage:
    python -m app.dataloader.run_import --file ./data/GEM-GGIT-Gas-Pipelines-2025-11.geojson
"""
import argparse
import logging
from pathlib import Path

from app.db.session import SessionLocal
from app.batchdataloader.pipeline_batch_loader import PipelineBatchLoader, get_import_status

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(description="Import GEM pipeline data")
    parser.add_argument(
        '--file', 
        required=True,
        help='Path to GeoJSON file'
    )
    parser.add_argument(
        '--batch-size',
        type=int,
        default=100,
        help='Number of segments to commit per batch (default: 100)'
    )
    parser.add_argument(
        '--europe-only',
        action='store_true',
        help='Filter to Europe bounding box'
    )
    parser.add_argument(
        '--resume',
        action='store_true',
        help='Resume previous incomplete import job for this file if available'
    )
    args = parser.parse_args()
    
    # Check file exists
    filepath = Path(args.file)
    if not filepath.exists():
        logger.error(f"File not found: {filepath}")
        return 1
    

    db = SessionLocal()

    try:
        logger.info(f"Starting import from {filepath}")

        # Resume logic
        existing_job = None
        if args.resume:
            from app.models.pipeline_import import PipelineImportJob
            existing_job = db.query(PipelineImportJob).filter(
                PipelineImportJob.filename == filepath.name,
                PipelineImportJob.status.in_(['running', 'partial'])
            ).order_by(PipelineImportJob.started_at.desc()).first()
            if existing_job:
                logger.info(f"Resuming previous job ID {existing_job.id} for file {filepath.name}")
            else:
                logger.info("No incomplete job found, starting new import.")

        # Create loader and run import
        loader = PipelineBatchLoader(db)
        job = loader.load_file(
            geojson_path=str(filepath),
            batch_size=args.batch_size,
            europe_only=args.europe_only,
            existing_job=existing_job
        )
        
        # Print results
        logger.info("=" * 60)
        logger.info(f"Import job {job.id} completed with status: {job.status}")
        logger.info(f"Total segments: {job.total_segments}")
        logger.info(f"Successful: {job.successful_segments}")
        logger.info(f"Failed: {job.failed_segments}")
        
        if job.error_message:
            logger.error(f"Error: {job.error_message}")
        
        # Get detailed status
        status = get_import_status(db, job.id)
        logger.info(f"Segment breakdown: {status['segment_breakdown']}")
        logger.info("=" * 60)
        
        return 0 if job.status in ('completed', 'partial') else 1
        
    except Exception as e:
        logger.error(f"Import failed: {e}", exc_info=True)
        return 1
    finally:
        db.close()


if __name__ == "__main__":
    exit(main())
