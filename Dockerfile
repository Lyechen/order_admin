FROM liubiao/alpine-python3.6
ENV PYTHONUNBUFFERED 1


COPY src/ /project/orderserver

WORKDIR /project/orderserver

RUN pip install -r requirements.txt \
    && mkdir -p /project/orderserver/logs

CMD ["uwsgi", "/project/orderserver/order_admin/wsgi/uwsgi.ini"]