# Асноўны image для AWS Lambda
FROM public.ecr.aws/lambda/python:3.11

# Капіруем файлы залежнасцяў
COPY corpus_build/requirements.txt ${LAMBDA_TASK_ROOT}

# Усталёўваем залежнасці
RUN pip install -r requirements.txt

# Капіруем код функцыі
COPY corpus_build/corpus_build.py ${LAMBDA_TASK_ROOT}

# Наладжваем entrypoint
CMD ["corpus_build.lambda_handler"] 