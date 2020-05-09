#!/usr/bin/python
# -*-coding:utf8 -*-

__author__ = "shumingyue"

import sys
import os
import re
import time
import datetime
import subprocess

'''
    用于处理当前project的monitor运行状态: JudgeRun(project_name, outdir, log_file) 
    1. 主要有三个返回值
        - Running: 继续刷新
        - Fail: 退出程序，报错（多种情况）
        - Done: 运行完成
    2. 读取Monitor_stat_retry.py运行的结果retry_monitor_stat.txt(这个脚本每60s刷新一次)
        - 读取之前先拷贝到本地outdir目录下<project_name>_retry_monitor_stat.txt（避免冲突）
        - <project_name>_retry_monitor_stat.txt文件中有判断文件是否完整的tag (Finish!Finish!Finish!)
        - 如果返回Fail则，每30s读取一次retry_monitor_stat.txt文件；重复5次还是Fail，则抛出异常，程序终止
    4. 记录报错信息log日志：读入log_file，与主程序中保持一致
'''


def TimeFormat(time_n):
    '''
        用于格式化时间
    '''
    # eg: 2020_03_20_09_26_47
    time_now = time.strftime('%Y_%m_%d_%H_%M_%S', time.localtime(time_n / 1000))
    return time_now

def Read_retry(project_name, outdir, log_file, run_time):
    '''
        读取retry_monitor_stat.txt文件进行判断
    :param project_name:
    :return:
        - Running: 继续刷新
        - Fail: 退出程序，报错 (有很多种情况)
        - Done: 运行完成
        - Error:程序运行报错，直接返回退出
    '''
    # 初始化存储monitor stat的任务数
    stat_p = []
    # 初始化报错信息存储字符串
    error_p = ""
    # 读取文件，对不同的情况进行记录
    try:
        # -- 先拷贝文件到本地 --
        # 比较时间，若程序提交的时间晚于定时文件的更新时间，则不断循环，直至定时文件被更新
        # 如果是重复投递，则直接读取之前投递的情况进行读取
        strptime = datetime.datetime.strptime(run_time, "%Y_%m_%d_%H_%M_%S")
        # 定时命令生成的文件的修改时间
        time_stat = int(round(os.path.getmtime(sys.path[0] + "/../bin/retry_monitor_stat.txt") * 1000))
        time_stat_file = TimeFormat(time_stat)
        strptime2 = datetime.datetime.strptime(time_stat_file, "%Y_%m_%d_%H_%M_%S")
        while strptime > strptime2:
            time.sleep(5)
            log_file.info("retry_monitor_stat.txt未刷新，5s后继续检查是否更新...")
            # print("1---")
            # print(strptime)
            # print("2---")
            # print(strptime2)
            time_stat = int(round(os.path.getmtime(sys.path[0] + "/../bin/retry_monitor_stat.txt") * 1000))
            time_stat_file = TimeFormat(time_stat)
            strptime2 = datetime.datetime.strptime(time_stat_file, "%Y_%m_%d_%H_%M_%S")

        os.system("cp " + sys.path[0] + "/../bin/retry_monitor_stat.txt " + outdir + "/retry_monitor_stat.txt")
        # -- 判断是否有Finish的标志（文件是否输出完整） --
        cmd = "grep \"Finish!Finish!Finish!\" " + outdir + "/retry_monitor_stat.txt"
        # cmd = "cat " + outdir + "/retry_monitor_stat.txt"
        # cmd = "grep \"Finish!Finish!Finish!\" /maindata/F18FTSECWLJ1207/Retry_monitor_test/retry_monitor_stat.txt"
        line_cmd = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, encoding='utf8')
        stdout, stderr = line_cmd.communicate()
        if "Finish!Finish!Finish!" in stdout:
            # print(stdout)
            # -- 如果文件是完整的，则匹配到项目 --
            cmd = "grep -i " + project_name + " " + outdir + "/retry_monitor_stat.txt"
            # cmd = "grep -i \"" + project_name + "\" /maindata/F18FTSECWLJ1207/Retry_monitor_test/retry_monitor_stat.txt"
            line_cmd = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                        encoding='utf8')
            stdout_p, stderr_p = line_cmd.communicate()
            # 查看匹配情况（用于测试）
            # log_file.info("grep -i " + project_name + " " + outdir + "/retry_monitor_stat.txt 输出：" + stdout_p)
            if stdout_p:
                for line in stdout_p.strip().split("\n"):
                    if re.match(r"^" + project_name.lower(), line.lower(), re.I):
                        # print(line)
                        # 1.如果是首行匹配到，则拆分，获取任务状态数目；并重新更新error_p为空
                        # 会不会有首行出现，但是也是报错的情况呢？？
                        log_file.info(project_name + "已匹配，匹配信息如下：")
                        log_file.info(line)
                        stat_p = line.split('\t')
                        if error_p:
                            error_p = ""
                        break
                    else:
                        # 2.如果不是首行匹配，那么就是报错了，获取报错信息
                        error_p = line
                if error_p:
                    # print(project_name + "运行出错，报错信息：" + error_p + "\n")
                    log_file.error(project_name + "运行出错，报错信息：" + error_p)
                    return "Fail"
                else:
                    # print(stat_p)
                    p_error = int(stat_p[8])
                    if p_error > 0:
                        log_file.error(project_name + "运行出现fail任务！请使用如下命令查看出错程序：\n" +
                                                      "/root/Software/monitor2020/monitor stat -m 3 -p" + project_name + " | grep fail")
                        return "Error"
                    p_done = int(stat_p[7])
                    p_total = int(stat_p[9])
                    # print(p_error)
                    # print(p_done)
                    # print(p_total)
                    if p_total == p_done:
                        return "Done"
                    elif p_total > p_done and p_error == 0:
                        return "Running"
            else:
                # -- 没有匹配到，则打印找不到这个项目，返回Fail --
                # print(project_name + "没有找到！请检查是否投递成功或被删除！返回Fail，30s后刷新...\n")
                log_file.info(project_name + "没有找到！请检查是否投递成功或被删除！返回Fail，30s后刷新...")
                return "Fail"
        # elif "Error!Error!Error!" in stdout:
        #     # -- 如果监测到程序运行异常，则报出提示 --
        #     log_file.error(sys.path[0] + "/../bin/Monitor_stat_retry.py运行异常：" + stdout)
        #     return "Fail"
        else:
            # -- 返回monitor stat监控文件不完整的报错 --
            # print("retry_monitor_stat.txt 文件不完整，返回Fail，30s后刷新...\n")
            log_file.info(outdir + "/retry_monitor_stat.txt 文件不完整，或请检查" + sys.path[0] + "/../bin/Monitor_stat_retry.py是否运行？，返回Fail，30s后刷新...")
            return "Fail"
    except Exception as e:
        # -- 记录程序抛出异常的报错 --
        log_file.error("judge_monitor_run.py程序运行异常，错误如下：" + str(e) + "\n返回Fail，30s后刷新...")
        return "Fail"

def JudgeRun(project_name, outdir, log_file, run_time):
    '''
        1.如果是"Fail"则重复运行5次，如果还是Fail则报错；
        2.如果是"Error"则表示monitor中有任务报错，直接返回Fail
        3.其他情况正常输出
        4.
    :param project_name:
    :return: Run_tag (即Read_retry函数的返回值)
    '''
    run_tag = Read_retry(project_name, outdir, log_file, run_time)
    if run_tag == "Fail":
        # 重复执行5次，一旦不是Fail，则立即停止循环，否则继续
        i = 0
        j = 0
        while i < 5:
            time.sleep(30)
            run_tag = Read_retry(project_name, outdir, log_file, run_time)
            if run_tag == "Fail":
                j += 1
                log_file.info("第" + str(j) + "次刷新失败！")
            else:
                break
            i += 1
        if j == 4:
            # print(project_name + " something is wrong. Please check!")
            # print(project_name + "连续5次刷新均报错！程序终止！找不到该项目或投递出错，请检查！")
            log_file.error(project_name + "连续5次刷新均报错！程序终止！找不到该项目或投递出错，请检查！")
            exit(1)
        else:
            return run_tag
    elif run_tag == "Error":
        return "Fail"
    else:
        return run_tag
