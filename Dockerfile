FROM public.ecr.aws/lambda/python:3.11

COPY . ${LAMBDA_TASK_ROOT}

COPY ./config/requirements.txt .
RUN pip3 install -r requirements.txt