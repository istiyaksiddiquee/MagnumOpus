FROM docker:23.0.1

RUN apk update && \
    apk upgrade && \
    apk add --no-cache --update bash curl 7zip python3 py3-pip&& \
    rm /var/cache/apk/*

RUN  pip3 install --upgrade pip && \
  pip3 install --no-cache-dir awscli 

COPY aws_credentials.txt /root/.aws/credentials
COPY aws_config.txt /root/.aws/config

# Install terraform
RUN curl "https://releases.hashicorp.com/terraform/1.3.8/terraform_1.3.8_linux_amd64.zip" -o "terraform.zip" \
  && 7z x terraform.zip \
  && mv terraform /usr/local/bin/terraform \
  && chmod +x /usr/local/bin/terraform

RUN mkdir -p /opt/terraform
WORKDIR /opt/terraform

COPY listen-docker-events.sh /var/listen-docker-events.sh

CMD ["/bin/bash", "/var/listen-docker-events.sh"]
