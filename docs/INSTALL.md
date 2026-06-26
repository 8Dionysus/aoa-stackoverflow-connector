# Install

## Fresh Clone

```bash
python -m venv .venv
. .venv/bin/activate
python -m pip install -e ".[dev]"
python scripts/validate_connector.py
python -m pytest -q
```

## No-Network Starter Proof

```bash
aoa-stackoverflow doctor
aoa-stackoverflow materialize fixture
aoa-stackoverflow build-index --run starter-fixture
aoa-stackoverflow build-graph --run starter-fixture
aoa-stackoverflow answer "Python datetime.utcnow deprecated prefer datetime.now(timezone.utc)" --run starter-fixture
aoa-stackoverflow eval claim-relations
aoa-stackoverflow eval answer-packets
```

## External Storage

For larger local runs:

```bash
export CONNECTOR_FAMILY_ROOT=/path/to/connector-databases
export CONNECTOR_INSTANCE_ROOT="$CONNECTOR_FAMILY_ROOT/aoa-stackoverflow-connector"
export CONNECTOR_DATA_ROOT="$CONNECTOR_INSTANCE_ROOT/data"
export CONNECTOR_CACHE_ROOT="$CONNECTOR_INSTANCE_ROOT/cache"
export CONNECTOR_ARTIFACT_ROOT="$CONNECTOR_INSTANCE_ROOT/artifacts"
```

Do not commit generated state from those roots.
