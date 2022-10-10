import os
import time
import grpc
import datetime
import logging
from pyspark.sql.functions import pandas_udf, PandasUDFType
from pyspark.sql.types import *
from pyspark.sql.functions import udf

from libpycommon.inoutput.sparkdf import get_by_sql_cols, set_df_overwrite, set_df_append, set_df_truncate
from libpycommon.inoutput.constant import *
from libpycommon.common.misc import get_env, get_env_encrypted
from libpycommon.common import mylog
mylogger=mylog.logger

from mykey.me import package_key_res_path,package_key_abs_path

def entry(ss,sep="$|$",part_num=18):
    d_db = {
        jdbc_connection_keyname_host: get_env('DB_HOST'),
        jdbc_connection_keyname_port: 1433,
        jdbc_connection_keyname_user: get_env_encrypted('DB_USER', package_key_res_path),  #
        jdbc_connection_keyname_password: get_env_encrypted('DB_PASSWD', package_key_res_path),  #
        jdbc_connection_keyname_catalog: get_env('DB_DATABASE')
    }
    d_redis = {
        'redis_host': get_env('REDIS_HOST'),
        'redis_port': int(get_env('REDIS_PORT')),
        'redis_max_conn': get_env('REDIS_MAX_CONN'),
        'redis_passwd': get_env_encrypted('REDIS_PASSWD', package_key_res_path),
        'redis_expire': int(get_env('REDIS_EXPIRE'))
    }

    #需要找到目标df,要改
    start_time_str = str(datetime.datetime.now()-datetime.timedelta(hours=2))[:-12]+'00:00.000'
    end_time_str=str(datetime.datetime.now()-datetime.timedelta(hours=1))[:-12]+'00:00.000'
    SQL=f"SELECT Id,Id as WechatNoReplyAnalysisInfoId,IsNoReply2, " \
        f"CONCAT(LastContentsAllSupport,'{sep}',LastContentsALL) AS text " \
        f"FROM WechatNoReplyAnalysisInfoByHour WHERE CreateTime > '{start_time_str}' and CreateTime < '{end_time_str}' and IsNoReply2 = 1"

    df = get_by_sql_cols(ss, jdbc_alchemy_mssql, jdbc_driver_name_mssql, d_db,
                         SQL,
                         'Id', part_num)

    df.show(10)
    # set_df_overwrite(jdbc_alchemy_mssql, jdbc_driver_name_mssql, d_db, df, 'WechatMessageList_filtered_30days')
    set_df_append(jdbc_alchemy_mssql, jdbc_driver_name_mssql, d_db, df, 'WechatMessageNoReplyAlgorithm')
    # set_df_truncate(jdbc_alchemy_mssql, jdbc_driver_name_mssql, d_db, df, 'WechatMessageList_filtered_30days')

if __name__ == '__main__':
    s=time.time()
    from pyspark.sql import SparkSession
    part_num = 6
    sep = "$|$"
    ss = SparkSession \
        .builder \
        .appName("pyspark-tensorflow-test") \
        .config('spark.sql.execution.arrow.maxRecordsPerBatch', '100000') \
        .config("spark.sql.execution.arrow.pyspark.enabled", 'true') \
        .config("spark.executor.instances", '6') \
        .getOrCreate()

    entry(ss, sep="$|$", part_num=18)

