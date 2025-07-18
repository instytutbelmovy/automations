FROM public.ecr.aws/lambda/python:3.12-x86_64

# Капіруем файлы залежнасцей
COPY devops/requirements.txt ${LAMBDA_TASK_ROOT}

# Усталёўваем залежнасці
RUN pip install -r requirements.txt

# Капіруем код функцыі
COPY devops/verti_conversion.py ${LAMBDA_TASK_ROOT}

# Капіруем модуль automations
COPY automations ${LAMBDA_TASK_ROOT}/automations

# Пераканайцеся, што файл мае правільныя permissions
RUN chmod 644 ${LAMBDA_TASK_ROOT}/verti_conversion.py

# Пераканайцеся, што мы ў правільнай дырэкторыі
WORKDIR ${LAMBDA_TASK_ROOT}

# Усталёўваем handler
CMD ["verti_conversion.lambda_handler"] 