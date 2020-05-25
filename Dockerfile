FROM python:3.8-slim-buster

RUN apt-get update -y \
	&& apt-get install -y \
		libglib2.0-0 \
		libsm6 \
	&& apt-get autoremove -y \
	&& apt-get clean -y

RUN yes | pip3 install numpy opencv-python-headless requests

COPY . /bin/

ENTRYPOINT ["/bin/main.py"]
