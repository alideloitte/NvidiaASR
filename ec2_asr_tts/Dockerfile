FROM python:3.11

COPY . ${LAMBDA_TASK_ROOT}

COPY ./config/requirements.txt .
RUN pip3 install -r requirements.txt

EXPOSE 80

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80"]