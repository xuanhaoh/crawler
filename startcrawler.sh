#!/bin/bash
docker rm -f crawler
docker run -d --name=crawler --env HOST=$(hostname -s) --env IP=$(hostname -I | cut -f 1 -d " ") xuanhaoh/crawler:2.0
