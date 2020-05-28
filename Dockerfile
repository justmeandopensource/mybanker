FROM python:3.8
RUN git clone -b myinvestment https://github.com/justmeandopensource/mybanker /mybanker
WORKDIR /mybanker
RUN pip install --no-cache-dir -r requirements.cfg
ENTRYPOINT [ "python" ]
CMD [ "mybanker.py" ]