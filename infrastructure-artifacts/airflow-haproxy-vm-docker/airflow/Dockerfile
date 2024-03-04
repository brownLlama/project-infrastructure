FROM apache/airflow:2.8.1

USER airflow

# Copy the dependencies file to the working directory
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

USER root

RUN apt-get update

RUN apt-get install apt-transport-https ca-certificates gnupg -y

# Install GCloud utility
RUN echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] http://packages.cloud.google.com/apt cloud-sdk main" | tee -a /etc/apt/sources.list.d/google-cloud-sdk.list && curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | apt-key --keyring /usr/share/keyrings/cloud.google.gpg  add - && apt-get update -y && apt-get install google-cloud-sdk -y

# RUN gcloud services enable containerregistry.googleapis.com
# RUN gcloud init

RUN groupadd docker

RUN usermod -a -G docker root
