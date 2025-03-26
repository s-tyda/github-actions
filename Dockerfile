FROM python:3.11-slim

COPY requirements.txt .

RUN pip install --no-cache-dir --upgrade -r ./requirements.txt

COPY main.py .

CMD ["fastapi", "run", "main.py", "--port", "80"]