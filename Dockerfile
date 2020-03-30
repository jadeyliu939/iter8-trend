FROM python:3.7-alpine

COPY requirements.txt .
COPY watcher.py .
RUN pip install --no-cache-dir -r requirements.txt

CMD [ "/usr/local/bin/python", "./watcher.py"]
