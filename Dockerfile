FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Install build deps (kept minimal). If you need full LaTeX support set
# build arg INSTALL_TEX=1 to install texlive packages (image size will grow).
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       build-essential \
       gcc \
       libffi-dev \
       ca-certificates \
       curl \
    && rm -rf /var/lib/apt/lists/*

ARG INSTALL_TEX=0
RUN if [ "$INSTALL_TEX" = "1" ] ; then \
      apt-get update && apt-get install -y --no-install-recommends \
        texlive-latex-base texlive-latex-recommended texlive-fonts-recommended \
        && rm -rf /var/lib/apt/lists/* ; \
    fi

COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy project
COPY . .

# Expose the HTTP port (if running HTTP mode)
EXPOSE 8000

# Default to HTTP mode in containers; you can override by setting MCP_TRANSPORT=stdio
ENV MCP_TRANSPORT=http

CMD ["python", "run_server.py"]
