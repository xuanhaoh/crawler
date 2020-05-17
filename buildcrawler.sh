#!/bin/bash
docker rmi -f crawler:2.0 xuanhaoh/crawler:2.0
docker build -t crawler:2.0 .
docker tag crawler:2.0 xuanhaoh/crawler:2.0
docker push xuanhaoh/crawler:2.0
