FROM python:3.7
COPY ./crawler /crawler
WORKDIR /crawler
RUN pip install -r requirements.txt --proxy=http://wwwproxy.unimelb.edu.au:8000/
CMD ["python", "crawler.py"]
