# Legacy scaffold module. The live /healthz endpoint is app.api.routers.health
# (wired in app.main); this alias is kept only so old imports resolve.
from app.api.routers.health import router

__all__ = ["router"]
