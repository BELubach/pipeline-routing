# Pipeline Data Checks

Quick diagnostic scripts to verify data import and routing functionality.

## Scripts

**check_pipeline_data.py**
- Node/edge counts
- Cost calculation status
- Nearest nodes to test coordinates

**check_edge_connectivity.py**
- Self-loop detection
- Valid edge count
- Node connectivity check

**detailed_routing_debug.py**
- Step-by-step routing diagnosis
- Tests nearest_node() function
- Checks if nodes are in same network component

**find_working_route.py**
- Finds connected nodes that can route
- Returns working API test coordinates

**debug_routing.sql**
- Raw SQL diagnostic queries
- Run with: `python manage.py run-sql boot/db_checks/debug_routing.sql`

## Usage

From project root:
```bash
python boot/db_checks/check_pipeline_data.py
python boot/db_checks/checks/check_edge_connectivity.py
python boot/db_checks/checks/detailed_routing_debug.py
python boot/db_checks/checks/find_working_route.py
```
