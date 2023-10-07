FROM python:3.8

RUN pip install --upgrade pip

RUN pip install gunicorn

COPY . .

# Then, we need to copy requirements.txt
COPY requirements.txt /tmp/requirements.txt

# Last, we install the dependency and then we can start the Gunicorn.
RUN pip install -r /tmp/requirements.txt

COPY . /tmp/app

WORKDIR /tmp/app

CMD ["gunicorn", "--bind", "0.0.0.0:5001", "discoverWeekly:app"]