ARG SOURCE
FROM ${SOURCE}

WORKDIR /elastic-password-setup
COPY src /tmp/src

RUN chmod +x /tmp/src/add-pkg.sh \
&& /tmp/src/add-pkg.sh \
&& cp -r /tmp/src/app/* . \
&& rm -rf /tmp/src

CMD [ "python3", "app.py" ]