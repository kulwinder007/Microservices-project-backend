FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .

EXPOSE 4999
CMD [ "flask", "run", "--host=0.0.0.0", "--port=4999"]