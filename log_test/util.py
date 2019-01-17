import pytz


def get_environment():
    env_file = os.path.join(BASE_DIR, 'environment.txt') \
        if re.search('[Ww]in', sys.platform) else os.path.join(ENV_DIR, 'environment.txt')
    if os.path.exists(env_file):
        with open(env_file, 'r', encoding='utf-8') as f:
            env_str = f.readline().lstrip().strip()
            return env_str if env_str in BASE_TYPE_LIST else ''

BASE_TYPE = get_environment() if get_environment() else 'production'


# 覆写Redis类
class MyRedis(Redis):
    obj = None

    def __new__(cls, *args, **kwargs):
        if cls.obj is None:
            cls.obj = object.__new__(cls)
        return cls.obj


# 获取redis实例
class GetRedis:
    def return_redis(self, debug_log):
        try:
            redisObj = MyRedis(**REDIS_CONFIG[BASE_TYPE])
            # print(id(debug_log))
            # print('1[redis连接成功 {}]'.format(redisObj))
            debug_log.info('[redis连接成功 {}]'.format(redisObj))
            # print('2[redis连接成功 {}]'.format(redisObj))
            return redisObj
        except Exception as e:
            debug_log.error('[redis连接失败,1秒后重试] [%s]' % (e))
            time.sleep(1)
            for i in range(10):
                debug_log.error('[redis第%s次连接重试...]' % (i))
                self.return_redis(debug_log)
                time.sleep(1)
            return


class DataOutput:
    def __init__(self, dbObj, cur, db_log, debug_log, dataQ):
        self.dbObj = dbObj
        self.cur = cur
        self.db_log = db_log
        self.debug_log = debug_log
        self.dataQ = dataQ

    @staticmethod
    def get_redis_time():
        debug_log = Logger()
        myRedis = GetRedis().return_redis(debug_log)
        time_tuple = myRedis.time()
        print(time_tuple)
        timestr = '%s.%s' % (time_tuple[0], time_tuple[1])
        print(timestr)
        times = int(float(timestr) * 1000)
        # print(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(times/1000)))
        return times

    def save_data_to_db(self, update_sql, insert_sql, the_asin_or_kw, data_dict, db_name='', md5key=''):
        self.dataQ.record_dbSum_times()
        # print(the_asin_or_kw, data_dict)
        try:
            if update_sql and insert_sql:
                self.cur.execute(update_sql, data_dict)
                row = self.cur.rowcount
                if row > 0:
                    self.dbObj.commit()
                    self.dataQ.record_db_ok_times()
                    self.db_log.info('%s,%s,%s,%s行,更新成功' %
                                     (return_PST().strftime("%Y-%m-%d %H:%M:%S"), db_name, the_asin_or_kw, row))
                    # 评论进程标记第一次
                    if md5key:
                        self.dataQ.the_reviews_first_download(md5key)
                else:
                    self.dbObj.rollback()
                    self.cur.execute(insert_sql, data_dict)
                    row = self.cur.rowcount
                    if row > 0:
                        self.dbObj.commit()
                        self.dataQ.record_db_ok_times()
                        self.db_log.info('%s,%s,%s,%s行,插入成功' %
                                         (return_PST().strftime("%Y-%m-%d %H:%M:%S"), db_name, the_asin_or_kw, row))
                        # 评论进程标记第一次
                        if md5key:
                            self.dataQ.the_reviews_first_download(md5key)
                    else:
                        self.dbObj.rollback()
            else:
                if update_sql and not insert_sql:
                    self.cur.execute(update_sql, data_dict)
                    row = self.cur.rowcount
                    if row > 0:
                        self.dbObj.commit()
                        self.dataQ.record_db_ok_times()
                        self.db_log.info('%s,%s,%s,%s行,更新成功\n' %
                                         (return_PST().strftime("%Y-%m-%d %H:%M:%S"), db_name, the_asin_or_kw, row))
                    else:
                        self.dbObj.rollback()
                if insert_sql and not update_sql:
                    self.cur.execute(insert_sql, data_dict)
                    row = self.cur.rowcount
                    if row > 0:
                        self.dbObj.commit()
                        self.dataQ.record_db_ok_times()
                        self.db_log.info('%s,%s,%s,%s行,插入成功' %
                                         (return_PST().strftime("%Y-%m-%d %H:%M:%S"), db_name, the_asin_or_kw, row))
                    else:
                        self.dbObj.rollback()
        except Exception as e:
            self.dbObj.rollback()
            datas = {the_asin_or_kw: data_dict}
            self.debug_log.error('%s,%s,%s,入库失败,原因%s,失败数据[%s];' % (
            return_PST().strftime("%Y-%m-%d %H:%M:%S"), db_name, the_asin_or_kw, e, datas))
            self.db_log.error('%s,%s,%s,入库失败,原因%s,失败数据[%s];' % (
            return_PST().strftime("%Y-%m-%d %H:%M:%S"), db_name, the_asin_or_kw, e, datas))
            return datas

    @staticmethod
    def save_data_to_db_pool(dbObj, cur, db_log, debug_log, dataQ, update_sql, insert_sql, the_asin_or_kw, data_dict, db_name='', md5key=''):
        dataQ.record_dbSum_times()
        # print(the_asin_or_kw, data_dict)
        try:
            if update_sql and insert_sql:
                cur.execute(update_sql, data_dict)
                row = cur.rowcount
                if row > 0:
                    dataQ.record_db_ok_times()
                    db_log.info('%s,%s,%s,%s行,更新成功' %
                                     (return_PST().strftime("%Y-%m-%d %H:%M:%S"), db_name, the_asin_or_kw, row))
                    # 评论进程标记第一次
                    if md5key:
                        dataQ.the_reviews_first_download(md5key)
                else:
                    cur.execute(insert_sql, data_dict)
                    row = cur.rowcount
                    if row > 0:
                        dataQ.record_db_ok_times()
                        db_log.info('%s,%s,%s,%s行,插入成功' %
                                         (return_PST().strftime("%Y-%m-%d %H:%M:%S"), db_name, the_asin_or_kw, row))
                        # 评论进程标记第一次
                        if md5key:
                            dataQ.the_reviews_first_download(md5key)
            else:
                if update_sql and not insert_sql:
                    cur.execute(update_sql, data_dict)
                    row = cur.rowcount
                    if row > 0:
                        dataQ.record_db_ok_times()
                        db_log.info('%s,%s,%s,%s行,更新成功\n' %
                                         (return_PST().strftime("%Y-%m-%d %H:%M:%S"), db_name, the_asin_or_kw, row))
                elif insert_sql and not update_sql:
                    cur.execute(insert_sql, data_dict)
                    row = cur.rowcount
                    if row > 0:
                        dataQ.record_db_ok_times()
                        db_log.info('%s,%s,%s,%s行,插入成功' %
                                         (return_PST().strftime("%Y-%m-%d %H:%M:%S"), db_name, the_asin_or_kw, row))
        except Exception as e:
            datas = {the_asin_or_kw: data_dict}
            debug_log.error('%s,%s,%s,入库失败,原因%s,失败数据[%s];' % (
            return_PST().strftime("%Y-%m-%d %H:%M:%S"), db_name, the_asin_or_kw, e, datas))
            db_log.error('%s,%s,%s,入库失败,原因%s,失败数据[%s];' % (
            return_PST().strftime("%Y-%m-%d %H:%M:%S"), db_name, the_asin_or_kw, e, datas))
            return datas



    # 获取md5码
    @staticmethod
    def get_md5_key(value_str):
        '''value_str 必须是一个字符串, 只返回其中16位md5码, 节约内存'''
        return hashlib.md5(value_str.encode('utf-8')).hexdigest()[8: -8]


def return_PST():
    # 设置为洛杉矶时区
    time_zone = pytz.timezone('America/Los_Angeles')
    dateNow = datetime.now(time_zone)
    return dateNow