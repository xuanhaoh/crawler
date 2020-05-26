#!/bin/bash
docker rm -f crawler
docker rmi -f crawler
docker build -t crawler .
docker run -d --name=crawler --env HOST=$(hostname -s) --env IP=$(hostname -I | cut -f 1 -d " ") crawler
