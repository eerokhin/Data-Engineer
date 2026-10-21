FROM spark:4.0.1-python3

USER root

RUN python3 -m pip install --no-cache-dir jupyterlab pandas

WORKDIR /home/spark/work

EXPOSE 8888 4040 7078 7079

CMD ["python3", "-m", "jupyterlab", \
     "--ip=0.0.0.0", \
     "--port=8888", \
     "--no-browser", \
     "--allow-root", \
     "--ServerApp.token=", \
     "--ServerApp.password=", \
     "--ServerApp.root_dir=/home/spark/work"]

