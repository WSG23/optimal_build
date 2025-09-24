import sys

if __name__.startswith("backend.app"):
    sys.modules["app.utils"] = sys.modules[__name__]
else:  # pragma: no cover
    sys.modules["backend.app.utils"] = sys.modules[__name__]

parent = sys.modules.get("backend.app")
if parent is not None:
    setattr(parent, "utils", sys.modules[__name__])
