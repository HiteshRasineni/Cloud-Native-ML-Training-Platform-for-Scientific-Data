FROM python:3.12-slim

WORKDIR /app

ENV PIP_NO_CACHE_DIR=1
COPY requirements.txt .
# CPU-only torch keeps the image much smaller than the CUDA default
RUN pip install torch==2.5.1 --index-url https://download.pytorch.org/whl/cpu
RUN pip install -r requirements.txt

COPY . .

CMD ["python", "main.py"]
