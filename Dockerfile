FROM python:3.13-slim-bookworm

RUN apt-get update

RUN apt-get install -y tzdata
ENV TZ=Asia/Tokyo
RUN ln -sf /usr/share/zoneinfo/Japan /etc/localtime && \
    echo $TZ > /etc/timezone


RUN apt-get install -y \
    sqlite3 procps locales vim curl gnupg apt-transport-https xvfb
RUN echo "ja_JP.UTF-8 UTF-8" >> /etc/locale.gen && locale-gen

ENV LANG ja_JP.UTF-8
ENV LANGUAGE ja_JP:en
ENV LC_ALL ja_JP.UTF-8

RUN curl -fsSL https://dl.google.com/linux/linux_signing_key.pub | gpg --dearmor -o /usr/share/keyrings/google-chrome.gpg
RUN echo "deb [arch=amd64 signed-by=/usr/share/keyrings/google-chrome.gpg] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list

ENV DISPLAY :99

RUN apt update && apt install -y google-chrome-stable

WORKDIR /app
RUN mkdir /app/db && mkdir /app/log

COPY requirements.txt ./

RUN python3 -m venv /app/venv && . /app/venv/bin/activate && pip install -Ur requirements.txt

ENV PATH /app/venv/bin:$PATH

COPY . .

EXPOSE 8090

# The user's example had "WORKDIR /app/{projectname}"
# Since our code is in the `app` directory, and the main file is `main.py`,
# we need to make sure the CMD instruction can find it.
# The `COPY . .` command already places the `app` directory inside `/app`.
# So the structure will be `/app/app/main.py`.
# The python path needs to be set correctly.
# A simpler approach is to set the WORKDIR to /app and adjust the CMD.
WORKDIR /app

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8090"]
