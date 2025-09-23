# Python dependencies

Python dependencies are installed from the pinned requirement files using the
standard `pip install` flow. SQLAlchemy is resolved from
`backend/requirements.txt`, so there is no longer a vendored wheel committed in
this directory.

To install the backend dependencies for development or CI, run:

```bash
pip install -r backend/requirements-dev.txt
```

The directory remains in the repository as a placeholder should we need to add
future offline mirrors, but it is intentionally empty.
