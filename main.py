import os
import time
import logging
from pyspark.sql import SparkSession

from libpycommon.common.misc import get_env
from libpycommon.common import mylog
mylogger=mylog.logger

from data.vipteacher_schedule_optimizer import entry, mylogger

BOOL_DEBUG_SWITCH = get_env('DEBUG_SWITCH', 'off') == 'on'
if __name__ == "__main__":
    # .master("local[*]")\
    if BOOL_DEBUG_SWITCH:
        ss = SparkSession \
            .builder \
            .appName("pyviptchopt") \
            .config('spark.sql.execution.arrow.maxRecordsPerBatch', '20000') \
            .config("spark.sql.execution.arrow.pyspark.enabled", 'true') \
            .getOrCreate()
    else:
        ss = SparkSession \
            .builder \
            .appName("pyviptchopt") \
            .config('spark.sql.execution.arrow.maxRecordsPerBatch', '20000') \
            .config("spark.sql.execution.arrow.pyspark.enabled", 'true') \
            .config("spark.jars.ivy", "/tmp/.ivy") \
            .config("spark.driver.extraJavaOptions", "-Dio.netty.tryReflectionSetAccessible=true") \
            .config("spark.executor.extraJavaOptions", "-Dio.netty.tryReflectionSetAccessible=true") \
            .getOrCreate()
    s=time.time()
    entry(ss)
    ss.stop()
    mylogger.info(f'duration@{time.time() - s}')

    