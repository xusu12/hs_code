from threading import Thread
import time


class Keyword(Thread):
    def __init__(self, asin):
        self.asin = asin
        Thread.__init__(self)

    def run(self):
        print('*'*10, self.asin)
        time.sleep(2)


asin_list = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]
while len(asin_list) > 0:
    for i in range(5):
        if len(asin_list) > 0:
            asin = asin_list.pop(0)
            print('asin:', asin)
            t = Keyword(asin)
            t.start()
    t.join()
