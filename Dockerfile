FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV HOME=/tmp


WORKDIR /streamlit_app

COPY requirements.txt .

RUN apt-get update && apt-get install -y --no-install-recommends \
    libexpat1 \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt


COPY streamlit_app/ .

RUN chgrp -R 0 /streamlit_app && \
    chmod -R g=u /streamlit_app

EXPOSE 8501

CMD ["streamlit", "run", "Introduction.py", "--server.address=0.0.0.0", "--server.port=8501"]
