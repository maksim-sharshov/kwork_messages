FROM python:3.12-slim

WORKDIR /bot

COPY requirements.txt .

RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

RUN rm -rf /etc/localtime
RUN ln -s /usr/share/zoneinfo/Africa/Tripoli /etc/localtime
RUN echo "Europe/Moscow" > /etc/timezone

COPY . .

CMD ["python", "-u", "main.py"]
