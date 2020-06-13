FROM python:3.8-alpine
RUN apk add git
RUN git clone -b myinvestment https://github.com/justmeandopensource/mybanker /mybanker
RUN apk del git
RUN rm -rf /var/cache/apk/*
WORKDIR /mybanker
RUN pip install --no-cache-dir -r requirements.cfg
ENTRYPOINT [ "python" ]
CMD [ "mybanker.py" ]