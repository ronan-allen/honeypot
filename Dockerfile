FROM python:3.10-slim

WORKDIR /app

COPY requirements .
RUN pip install --no-cache-dir -r /app/requirements

COPY config.ini .
COPY main.py .
COPY entrypoint.sh .

RUN chmod +x entrypoint.sh
ENTRYPOINT ["/app/entrypoint.sh"]