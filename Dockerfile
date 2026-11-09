FROM python:3.12-slim

WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/furnace \
    SKYGUARD_EMULATION=true \
    BLACKBOX_PORT=19090 \
    EVIDENCE_PORT=18765

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt pytest

COPY . .
RUN mkdir -p furnace/logs

# Default: run the emulation demo then exit (CI-friendly)
CMD ["python", "furnace/07_Emulation/run_emulation_demo.py"]
