FROM python:3.10-slim
WORKDIR /app
RUN pip install --no-cache-dir flask psycopg2-binary requests
COPY . /app
EXPOSE 8001
CMD ["python", "app.py"]
