FROM alpine:3.12.1
RUN apk add python3 && apk add py3-requests
COPY app.py /
WORKDIR /
CMD [ "python3", "app.py" ]