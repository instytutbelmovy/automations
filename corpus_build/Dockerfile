FROM public.ecr.aws/lambda/python:3.11

COPY corpus_build/requirements.txt ${LAMBDA_TASK_ROOT}

RUN pip install -r requirements.txt

COPY corpus_build/corpus_build.py ${LAMBDA_TASK_ROOT}
COPY corpus_build/template.conf ${LAMBDA_TASK_ROOT}

CMD ["corpus_build.lambda_handler"] 