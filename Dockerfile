FROM python:3.12-slim-bookworm AS runtime
ARG VERSION=0.5.0
ARG VCS_REF=unknown
LABEL org.opencontainers.image.title="ComAgent" \
      org.opencontainers.image.description="Database and document question answering with traceable evidence" \
      org.opencontainers.image.source="https://github.com/gaara119/ComAgent" \
      org.opencontainers.image.version=$VERSION \
      org.opencontainers.image.revision=$VCS_REF
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1 \
    RAG_MANIFEST_PATH=data/docs/local-manifest.csv RAG_INDEX_PATH=data/indexes/local \
    BGE_MODEL_PATH=data/models/bge-m3 RAG_RETRIEVAL_STRATEGY=hybrid_rerank \
    AW_CATALOG_PATH=data/catalog/adventureworks-manual-applied-v1.yaml \
    AW_SCHEMA_INDEX_PATH=data/indexes/schema-aw-manual-applied-v1 \
    VALUE_INDEX_PATH=data/indexes/values-manual-applied-v1 \
    LLM_MODEL=deepseek-flash LLM_BASE_URL=https://api.deepseek.com LLM_REQUEST_MAX_ATTEMPTS=12 \
    CHINOOK_DB_URL="" DB_URL="" AW_DB_URL=""
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends libgomp1 \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --gid 10001 comagent && useradd --uid 10001 --gid comagent --create-home comagent
COPY requirements-runtime.txt ./
RUN pip install --disable-pip-version-check -r requirements-runtime.txt
COPY api/ ./api/
COPY qa_agent/ ./qa_agent/
COPY frontend-workbench/run_ui.py ./frontend-workbench/run_ui.py
COPY frontend-workbench/dist/ ./frontend-workbench/dist/
COPY frontend-workbench/LICENSES/ ./frontend-workbench/LICENSES/
COPY data/catalog/ ./data/catalog/
COPY data/rules/ ./data/rules/
COPY data/aliases/ ./data/aliases/
COPY data/model_manifest/ ./data/model_manifest/
COPY deployment/container_entrypoint.py ./deployment/container_entrypoint.py
COPY scripts/smoke_container.py ./scripts/smoke_container.py
COPY scripts/download_embeddings.py scripts/ingest_docs.py scripts/build_catalog.py scripts/build_value_index.py scripts/build_schema_index.py ./scripts/
COPY README.md ./
RUN mkdir -p data/docs data/indexes data/models .runtime \
    && chown -R comagent:comagent /app
USER comagent
EXPOSE 8501
VOLUME ["/app/data", "/app/.runtime"]
HEALTHCHECK --interval=15s --timeout=10s --start-period=30s --retries=3 \
    CMD python -c "import urllib.request,json; assert json.load(urllib.request.urlopen('http://127.0.0.1:8501/ui-health',timeout=3))['status']=='ok'; assert json.load(urllib.request.urlopen('http://127.0.0.1:8501/health',timeout=5))['status']=='ok'"
ENTRYPOINT ["python", "deployment/container_entrypoint.py"]

FROM runtime AS test
USER root
RUN pip install --disable-pip-version-check pytest==9.1.1
COPY tests/test_document_imports.py tests/test_database_ui_proxy.py tests/test_rag_multidocument_service.py tests/test_registry_portable_codec.py tests/test_container_runtime.py ./tests/
USER comagent
ENTRYPOINT ["python", "-m", "pytest", "-q", "-p", "no:cacheprovider", "--basetemp=/tmp/comagent-tests", "tests/"]

FROM runtime AS final
