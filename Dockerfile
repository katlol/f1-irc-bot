FROM python:3.11-alpine
WORKDIR /app
COPY requirements.txt /app/requirements.txt
RUN apk --virtual=.build-deps add gcc build-base && \
    pip install --no-cache-dir -r requirements.txt && \
    apk del .build-deps
COPY . /app
CMD ["python", "app.py"]
