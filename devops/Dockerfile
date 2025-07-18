FROM public.ecr.aws/lambda/python:3.12-x86_64

# Build args для git інфармацыі
ARG GIT_COMMIT_HASH=unknown
ARG GIT_COMMIT_DATE=unknown
ARG GIT_BRANCH=unknown

# Капіруем файлы залежнасцей
COPY devops/requirements.txt ${LAMBDA_TASK_ROOT}

# Усталёўваем залежнасці
RUN pip install -r requirements.txt

# Капіруем код функцыі
COPY devops/verti_conversion.py ${LAMBDA_TASK_ROOT}

# Капіруем модуль automations
COPY automations ${LAMBDA_TASK_ROOT}/automations

# Ствараем файл з git інфармацыяй
RUN echo "{\"git_commit_hash\": \"${GIT_COMMIT_HASH}\", \"git_commit_date\": \"${GIT_COMMIT_DATE}\", \"git_branch\": \"${GIT_BRANCH}\", \"build_time\": \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\"}" > ${LAMBDA_TASK_ROOT}/git_info.json

# Пераканайцеся, што файл мае правільныя permissions
RUN chmod 644 ${LAMBDA_TASK_ROOT}/verti_conversion.py

# Пераканайцеся, што мы ў правільнай дырэкторыі
WORKDIR ${LAMBDA_TASK_ROOT}

# Усталёўваем handler
CMD ["verti_conversion.lambda_handler"] 