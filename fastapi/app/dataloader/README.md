# Pipeline Batch Loader

A Spring Batch-style data import system for loading large GEM pipeline GeoJSON files with progress tracking and error handling.

## Quick Start

### 1. Run the Migration

```bash
alembic upgrade head
```

This creates two new tables:
- `pipeline_import_jobs` - tracks import jobs
- `pipeline_import_segments` - tracks individual segment processing

### 2. Run the Import

```bash
python -m app.dataloader.run_import --file ./data/GEM-GGIT-Gas-Pipelines-2025-11.geojson
```

Options:
- `--file`: Path to GeoJSON file (required)
- `--batch-size`: Segments per commit batch (default: 100)
- `--europe-only`: Import only Europe data
- `--resume`: Resumes any previously stopped run 

### 3. Use Programmatically

```python
from app.db.session import SessionLocal
from app.dataloader.pipeline_batch_loader import PipelineBatchLoader, get_import_status

db = SessionLocal()
try:
    loader = PipelineBatchLoader(db)
    job = loader.load_file(
        geojson_path="./data/GEM-GGIT-Gas-Pipelines-2025-11.geojson",
        batch_size=100,
        europe_only=True
    )
    
    print(f"Job {job.id}: {job.status}")
    print(f"Success: {job.successful_segments}/{job.total_segments}")
    
    status = get_import_status(db, job.id)
    print(status)
finally:
    db.close()
```

