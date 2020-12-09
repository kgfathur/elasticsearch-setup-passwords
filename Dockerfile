FROM alpine:3.12.1
RUN apk add python3 && apk add py3-requests
WORKDIR /
COPY app.py /
CMD [ "python3", "app.py" ]