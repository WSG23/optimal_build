collect_ignore = ["test_migrations"]

# Ensure the lightweight coverage plugin bundled in the repository is always
# available when ``pytest --cov`` is invoked.
pytest_plugins = ["pytest_cov"]
