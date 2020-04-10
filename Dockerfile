FROM python:3.7-alpine

COPY requirements.txt .
COPY iter8-trend.py .
RUN pip install --no-cache-dir -r requirements.txt

CMD [ "/usr/local/bin/python", "./iter8-trend.py"]
