# Test target #2: a server we wrote ourselves, whose tool description is
# completely honest-sounding. This image needs no network to build (pure
# stdlib) - which is itself the point: nothing here needs to reach out
# anywhere, so if it's ever caught trying to, that's unambiguous.
FROM python:3.12-slim
COPY server.py /server.py
ENTRYPOINT ["python", "/server.py"]
