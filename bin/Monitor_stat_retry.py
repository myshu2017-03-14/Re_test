#!/root/Software/miniconda3/bin/python
####!/usr/bin/python
# -*-coding:utf8 -*-
import sys
import os
import time
import re
import subprocess
import shutil
import configparser
import argparse

sys.path.append("/root/16s/Reanalysis/result/shumingyue/lib/")

sys.path.append("/root/16s/Modules_v2/lib")
sys.path.append("/root/16s/Modules/")

# 自定义一个设置log的模块
from MyLogger import Logger
import traceback

'''
    不断对当前所有项目的状态进行更新：
    1.需要对现有的所有项目的状态进行记录（retry_monitor_stat.txt）
    2.需要不断刷新，并且一直不断的运行（60s）
    3.利用crontab -e编辑加入定时任务
        -crontab -l查看是否在定时任务中）
        -crontab -e定时任务命令："*/1 * * * * /root/16s/Reanalysis/result/shumingyue/bin/Monitor_stat_retry.py"
    
'''

class Monitor_stat_retry():
    def __init__(self, outdir):
        # --
        self.outdir = outdir
        if os.path.exists(self.outdir + "/retry_monitor_stat.txt"):
            os.remove(self.outdir + "/retry_monitor_stat.txt")
        self.stat_txt = open(self.outdir + "/retry_monitor_stat.txt", "w")

    def restart(self):
        # while True:
        try:
            self.stat_txt = open(self.outdir + "/retry_monitor_stat.txt", "w")
            # 调用查询函数
            # self.monitor_stat_main()废弃，去除函数外调用，避免栈溢出
            cmd = monitor_soft + " stat"
            p_stat = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                      encoding='utf8')
            stdout, stderr = p_stat.communicate()
            # 不管输出啥，都写入retry_monitor_stat.txt文件
            self.stat_txt.write(stdout)
            self.stat_txt.flush()

            # 写入完成Tag，"Finish!Finish!Finish!"重要的事说三遍！！！
            self.stat_txt.write("\nFinish!Finish!Finish!\n")
            self.stat_txt.flush()
        except Exception as e:
            # 当程序报错时，也写入retry_monitor_stat.txt文件
            # 写入报错Tag，"Error!Error!Error!"重要的事说三遍！！！
            # print(e)
            self.stat_txt.write("\nError!Error!Error!\n")
            self.stat_txt.flush()
            self.stat_txt.write(e)
            self.stat_txt.flush()
            # time.sleep(60)

if (__name__ == "__main__"):
    parser = argparse.ArgumentParser(description='Refrush for 60s!')
    parser.add_argument('--monitor', '-t', required=False, help='monitor full path', default="/root/Software/monitor2020/monitor")
    parser.add_argument('--outdir', '-o', required=False, help='output path', default="/maindata/F18FTSECWLJ1207/Retry_monitor_test/")
    args = parser.parse_args()
    monitor_soft = args.monitor
    # outdir = args.outdir
    outdir = os.path.abspath(sys.path[0] + "/")
    # --- 运行程序，并返回log ---
    process = Monitor_stat_retry(outdir)
    process.restart()

