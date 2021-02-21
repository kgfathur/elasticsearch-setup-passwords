#!/bin/sh

source /tmp/src/build.env \
&& INSTALL_PKGS=$(cat /tmp/src/pkg-list.txt) \
&& apk add $INSTALL_PKGS \
&& unset $(cat /tmp/src/build.env | cut -d'=' -f1) \
&& rm -rf /var/cache/apk/* \
&& rm -rf /var/log/*
