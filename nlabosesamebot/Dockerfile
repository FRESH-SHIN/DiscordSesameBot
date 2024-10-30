FROM alpine:3.16

ENV PIP_ROOT_USER_ACTION=ignore

RUN apk add --update --no-cache python3 && ln -sf python3 /usr/bin/python
RUN apk add --no-cache python3-dev libffi-dev gcc build-base bluez dbus 
RUN python3 -m ensurepip
RUN pip3 install --upgrade pip 
RUN mkdir -p /usr/src/app
WORKDIR /usr/src/app

COPY requirements.txt /usr/src/app/

RUN pip3 install --no-cache-dir -r requirements.txt
RUN pip3 install bleak>=0.21.0 --no-dependencies

COPY . /usr/src/app

ENTRYPOINT ["python3"]

CMD ["."]
