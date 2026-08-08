# Deploys api/main.py. Build context is the project root (not api/) because
# main.py imports scanner/ as a sibling directory via sys.path - the image
# has to preserve that same relative layout, not just copy api/ alone.
#
# Deliberately NOT Docker-in-Docker: scanner/sandbox.py shells out to a
# real `docker` binary for Milestone 3's sandboxed scans, which this image
# doesn't have and standard container hosts don't support nesting anyway.
# That's fine - ALLOW_LIVE_PACKAGE_SCAN defaults to false, so the one
# endpoint that would reach that code path (POST /api/scan-package)
# returns 403 before ever importing a real Docker call. Everything else
# (static scans, the registry, history) has no Docker dependency.
FROM python:3.12-slim

WORKDIR /app
COPY scanner/ ./scanner/
COPY api/ ./api/
RUN pip install --no-cache-dir -r api/requirements.txt

WORKDIR /app/api
EXPOSE 8080
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
