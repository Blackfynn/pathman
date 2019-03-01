FROM python:3.6 as test
WORKDIR /app
COPY requirements.txt requirements-test.txt ./
RUN  pip --no-cache-dir install -r requirements.txt -r requirements-test.txt
ADD pathman ./pathman
ADD tests ./tests
RUN ls
ENTRYPOINT [""]
