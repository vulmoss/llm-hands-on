FROM python:3.12-slim

WORKDIR /app
COPY pyproject.toml README.md ./
COPY src ./src
RUN pip install --no-cache-dir '.[api]' \
    && useradd --create-home learner \
    && mkdir /app/.data \
    && chown learner:learner /app/.data
USER learner
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s CMD python -c "from urllib.request import urlopen; urlopen('http://127.0.0.1:8000/health', timeout=3)" || exit 1
CMD ["llm-lab", "serve", "--host", "0.0.0.0", "--port", "8000"]
