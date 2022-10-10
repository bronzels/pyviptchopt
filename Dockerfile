FROM harbor.my.org:1080/base/py/spark

RUN whoami

ADD data /opt/spark/work-dir/mykey
ADD mykey /opt/spark/work-dir/mykey
ADD *.py /opt/spark/work-dir/
ADD requirements.txt /opt/spark/work-dir/

#USER root
RUN pip config list
RUN cat /root/.pip/pip.conf
RUN pip install --trusted-host pypi.my.org -r requirements.txt
#ARG spark_uid=185
#USER ${spark_uid}

#CMD ["python3", "main.py"]


