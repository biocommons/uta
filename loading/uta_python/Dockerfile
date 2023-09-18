# Use the official Python image as the base image
FROM python:3.8

# Set the working directory inside the container
WORKDIR /uta_build


# Install system dependencies
RUN apt-get update
RUN apt-get -y install make
RUN apt-get -y install curl
RUN apt-get -y install git

# Install any Python dependencies
RUN pip install git+https://github.com/ecalifornica/uta-align@fix-possible-bug
RUN git clone https://github.com/biocommons/uta.git
RUN cd uta && pip install .

# Uncomment for hgvs testing
#RUN pip install hgvs

# Define the command to run when the container starts
# CMD ["python", "app.py"]
CMD ["sleep", "infinity"]


# uta --conf=../etc/global.conf --conf=../etc/uta_dev@postgres.conf shell
