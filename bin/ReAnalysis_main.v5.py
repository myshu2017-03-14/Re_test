#!/usr/bin/python
# -*-coding:utf8 -*-
import sys
import os
import time
import re
import subprocess
import shutil

sys.path.append("../lib")
# sys.path.append("..")
sys.path.append("/root/16s/Reanalysis/result/shumingyue/lib/")

sys.path.append("/root/16s/Modules_v2/lib")
sys.path.append("/root/16s/Modules/")

# 自定义一个设置log的模块
# import logging
from MyLogger import Logger
import traceback

import configparser
import argparse

# 调用夏展峰写的模块,调用各个模块的信息
from generate_baseclass import ConfigFile, Listfile, Module
from Plan_Module import Module_plan

# 调用check output模块
from check_output_test import CheckOutput, CheckOutput2

# 调用code to module转换龙飞提供的【重分析代码】
from code_to_module import Tranformodule

# 调用判断monitor stat模块
from judge_monitor_run import JudgeRun
# from judge_monitor_run_test import JudgeRun

'''
    处理重分析的实际分析过程。
    1，输入参数必须包括：模块名称(主流程名称为main)、config参数文件
    2，生成主程序并投递
    3，生成监控线程，密切监视流程运行的状况。当流程运行完毕应当第一时间返回。
    4，返回的日志文件有：*.log（流程运行监控log）和*.Run.tag（提供给王龙飞的tag文件，只包括三个值：“运行中”、“失败”/“成功”）
'''

class Processing():
    def __init__(self, modelname, config_file, fake_modelname):
        # 全局变量
        self.modelname = modelname
        self.fake_modelname = fake_modelname.lower()

        # 读取config的参数
        self.config = configparser.ConfigParser()
        self.config.read(config_file)

        # -- 如果是main程序，则读入project_id, 默认为空 --
        if self.config[modelname].get("project_id"):
            self.project_id = self.config[modelname].get("project_id")
        else:
            self.project_id = ""

        # -- 读入输出文件路径 --
        # 这里要求读取的config文件包含输出路径，参数示例如下pca_outdir = /result/
        if self.config[modelname].get(modelname + "_outdir"):
            self.outdir = os.path.abspath(self.config[modelname].get(modelname + "_outdir"))
        # 当输入config文件为主流程（main）参数文件时，输出路径格式有所差异，没有下划线
        elif self.config[modelname].get("outdir"):
            self.outdir = os.path.abspath(self.config[modelname].get("outdir"))
        else:
            print("config文件(" + config_file + ")中找不到输出文件夹参数 outdir，请检查！！\n")
            exit(1)
        # 如果输出文件夹不存在则重新建立
        if not os.path.exists(self.outdir):
            os.makedirs(self.outdir)

        # -- 设置全局的Log --
        self.log = Logger(modelname, self.outdir)

        # -- 设置全局输出Tag文件(eg: result/pca/pca.Run.tag) --
        # 对Run.tag文件进行更新
        if os.path.exists(self.outdir + "/" + self.modelname + ".Run.tag"):
            os.remove(self.outdir + "/" + self.modelname + ".Run.tag")
        self.tag = open(self.outdir + "/" + self.modelname + ".Run.tag", "w")
        # 对运行状态进行判断。
        self.tag.write(self.project_id + "_" + self.modelname + "：运行中\n")
        self.tag.flush()

        # -- 判断fake_modelname的有效性 --
        if self.fake_modelname == "Not Found":
            print("没有找到" + self.fake_modelname + "，请检查！\n")
            self.log.error("没有找到" + self.fake_modelname + "，请检查！\n")
            self.tag.write(self.project_id + "_" + self.modelname + "：失败\n")
            self.tag.flush()
            exit(1)

        # -- 读入差异分组组 --
        if self.config[modelname].get(modelname + "_diff_plan"):
            self.diff_plan = self.config[modelname].get(modelname + "_diff_plan").split(",")
        # 当输入config文件为主流程参数文件时，输出格式有所差异
        elif self.config[modelname].get("diff_plan"):
            self.diff_plan = self.config[modelname].get("diff_plan").split(",")
        else:
            self.diff_plan = []

        # -- 读入main流程需要分析的模块，默认为空 --
        if self.config[modelname].get("module_option"):
            self.module_option = self.config[modelname].get("module_option")
            # 所有模块存成列表，如果是all，则存默认，否则直接split
            # 定义了“all”
            if self.module_option == "all":
                self.module_option = ['otu', 'anno', 'basic', 'pca', 'barplot', 'beta', 'alpha', "plsda", "nmds",
                                      "picrust", "difference", "heatmap", "network", 'rank', 'cumulative', 'ccarda',
                                      'lefse', 'anosim', "randomforest", "permanova", "sourcetracker", "graphlan", "enterotypes"]
            else:
                self.module_option = self.module_option.replace(' ', '').split(",")
        else:
            self.module_option = []
            # 如果为空的话报错！
            print("module_option参数为空或缺失，请检查config文件配置！\n")
            self.log.error("module_option参数为空或缺失，请检查config文件配置！")
            self.tag.write(self.project_id + "_" + self.modelname + "：失败\n")
            self.tag.flush()
            exit(1)

    def PrintTime(self):
        '''
            用于增加monitor运行-p参数时间戳后缀
        '''
        import time
        now = int(round(time.time() * 1000))
        # eg: 2020_03_20_09_26_47
        time_now = time.strftime('%Y_%m_%d_%H_%M_%S', time.localtime(now / 1000))
        return time_now

    def read_conf(self, config_file):
        '''
            读取/root/.new.pymonitor.conf文件，获取当前正在跑的所有任务的project ID
        :param config_file
        :return: project ID list (project_all)
        '''
        project_all = []
        project_tag = 0
        for line in open(config_file, 'r'):
            line = line.strip()
            if re.match("^\s*$", line) or re.match("^\s*#", line):
                continue
            elif re.match("^\[project\]", line):
                project_tag = 1
            elif re.match("^\[base\]", line):
                project_tag = 0
            else:
                if project_tag == 1:
                    line.replace(" ", "")
                    re.sub("#.*", "", line)
                    line = line.split('=')
                    project_all.append(line[0].strip())
        return project_all

    def MkReport(self, run_stat, run_project, run_time):
        '''
            根据运行状态判断是否需要拷贝结果到Report目录：
            1. Running: 继续刷新
            2. Fail: 退出程序，报错
            3. Done: 运行完成，检验结果，并拷贝到Report目录
            4. Exit: 重复刷新5次后仍然Fail，报错退出
        :param run_stat: 运行状态，由JudgeRun()函数(外置了)得到
        :param run_project: project_id
        :return:
        '''

        while run_stat == "Running":
            # 如果是正在运行则刷新项目，并不断调用函数返回状态，直至最后显示"Fail"或"Done"
            time.sleep(5)
            # os.system(monitor_soft + " stat updateproject -p " + run_project)
            # run_stat = self.JudgeRun2(run_project)
            run_stat = JudgeRun(run_project, self.outdir, self.log, run_time)
        if run_stat == "Fail":
            # fail_shell = os.popen(monitor_soft + " stat -m 3 -p " + run_project + " | grep fail")
            print(run_project + "项目monitor运行报错。请检查程序是否正确投递或使用如下命令检查报错程序！\n" + monitor_soft + " stat -m 3 -p " + run_project + " | grep fail\n")
            self.log.error(run_project + "项目monitor运行报错。请检查程序是否正确投递或使用如下命令检查报错程序！\n" + monitor_soft + " stat -m 3 -p " + run_project + " | grep fail")
            self.tag.write(self.project_id + "_" + self.modelname + "：失败\n")
            self.tag.flush()
            exit(1)
            # 删除当前project
            # os.system("/root/Software/monitor2020/monitor removeproject -m 1 -b -p " + run_project)
        if run_stat == "Exit":
            print(run_project + "项目连续5次刷新均报错！程序终止！找不到该项目或投递出错，请检查！")
            self.tag.write(self.project_id + "_" + self.modelname + "：失败\n")
            self.tag.flush()
            exit(1)
        if run_stat == "Done":
            # 如果完成的话，则结束运行，返回log
            self.log.info(run_project + "项目monitor运行完成。结果路径：" + self.outdir)
            self.log.info(run_project + "开始检查输出文件是否完整。")
            # CheckOutput()判断输出数据是否完整，单独拎出来写一个模块
            # 判断输出结果是否完整，如果是的话，则成功运行，否则输出哪些文件缺失（no_files）。
            # main模块和单个模块分别使用不同的函数进行判断
            # 指定reort_dir，并清空目录
            report_dir = self.outdir + "/../Report/"
            if not os.path.exists(report_dir):
                os.makedirs(report_dir)
            else:
                shutil.rmtree(report_dir)
                os.makedirs(report_dir)
            # 检验现有模块输出文件是否完整
            file_check_tag = 0
            # main和单个模块使用不同的CheckOutput函数！
            for module in self.module_option:
                # print(module)
                module = module.lower()
                if not os.path.exists(self.outdir + "/" + module):
                    continue
                if self.fake_modelname == "main":
                    # no_files = CheckOutput(module, self.outdir + "/Configdir/" + module + ".config",
                    # self.outdir + "/" + module, report_dir, self.diff_plan)
                    no_files, file_stat = CheckOutput(module, self.outdir + "/Configdir/" + module + ".config",
                                       self.outdir + "/" + module, report_dir, self.diff_plan, self.log)
                else:
                    # 这里单个模块的config是一个文件，不需要读取Configdir
                    no_files, file_stat = CheckOutput2(module, config, self.outdir + "/" + module, report_dir, self.diff_plan, self.fake_modelname, self.log)
                if len(no_files):
                    # print(len(no_files))
                    # 不为空，有文件缺失，判断是否有必要文件缺失
                    no_files = "\n".join(no_files)
                    if file_stat == "Error":
                        file_check_tag = 1
                        print(run_project + "中" + module + "【重要】结果文件缺失。缺失文件列表：\n" + no_files)
                        self.log.warning(run_project + "中" + module + "【重要】结果文件缺失。缺失文件列表：\n" + no_files)
                        # self.tag.write(self.project_id + "_" + self.modelname + "：失败\n")
                        # self.tag.flush()
                        # exit(1)
                    else:
                        print(run_project + "中" + module + "结果文件缺失。缺失文件列表：\n" + no_files)
                        self.log.warning(run_project + "中" + module + "结果文件缺失。缺失文件列表：\n" + no_files)
                else:
                    # 为空表示文件都存在
                    self.log.info(run_project + "中" + module + "结果文件完整。结果路径：" + self.outdir + "/" + module)
            # 扫描完之后更新tag文件
            if file_check_tag:
                # 也可以把失败更新放到"Error"鉴别，速度会更快，但是Log列出的缺失文件会不全
                self.tag.write(self.project_id + "_" + self.modelname + "：失败\n")
                self.tag.flush()
            else:
                self.tag.write(self.project_id + "_" + self.modelname + "：成功\n")
                self.tag.flush()


            # 输出log
            self.log.info(run_project + " monitor运行log日志： " + run_project + ".db.log")
            os.system(monitor_soft + " logdump -p " + run_project)
        # 最后不管报错与否，删除当前project
        # os.system(monitor_soft + " removeproject -m 1 -b -p " + run_project)

    def RunModule(self, software, database, config, project, queue, monitor_soft):
        '''
            1.如果是运行主流程，则需要用夏展峰的模块Generate_main.py，根据config文件生成各个模块的程序
              同时根据生成的All_dependence.txt进行提交monitor，并返回log
            2.（废弃）如果是运行单个流程，则调用夏展峰的Module模块，生成脚本后提交monitor运行，并返回log
            3.如果是单个流程，可能存在需要依赖关系，需要调用其他的流程，所以这里统一用夏展峰的模块Generate_main.py进行调用
        '''
        # 优先使用config中的project_id作为“-p”参数前缀,否则使用默认的
        if self.project_id != "":
            project = self.project_id

        self.log.info('根据config重新生成运行脚本。输出结果路径：' + self.outdir)
        # -- 定义运行monitor的项目名称 --
        # 根据时间戳设置monitor项目名称：Modelname + time (eg: -p anosim_2020_03_20_09_20_46)
        # 跑main流程/单个的时候monitor运行的-p参数中加上了项目id
        run_project = project + "_" + self.fake_modelname + "_" + self.PrintTime()
        # 如果是主流程，则先调用夏展峰写的Generate_main.py模块，生成所有模块的运行脚本和路径
        status = os.system(
            python_soft + " /root/16s/Modules/Generate_pipeline/Generate_main.py --config " + config + " --database " + database + " --software " + software)
        if status != 0:
            # 如果Generate_main.py模块报错，则查看result1/generate_main.log信息查看报错情况
            print("/root/16s/Modules/Generate_pipeline/Generate_main.py运行错误。报错信息查看log：当前运行路径/generate_main.log\n")
            self.log.error(
                "/root/16s/Modules/Generate_pipeline/Generate_main.py运行错误。报错信息查看log：当前运行路径/generate_main.log")
            self.tag.write(self.project_id + "_" + self.modelname + "：失败\n")
            self.tag.flush()
            exit(1)
        else:
            # 处理result1/Listdir/All.dependence.txt，有的情况下为空，如果为空则报错退出
            if not os.path.getsize(self.outdir + "/Listdir/All.dependence.txt"):
                print(self.outdir + "/Listdir/All.dependence.txt为空！请检查！\n")
                self.log.info(self.outdir + "/Listdir/All.dependence.txt为空！请检查！")
                self.tag.write(self.project_id + "_" + self.modelname + "：失败\n")
                self.tag.flush()
                exit(1)
                # 只有一个module或多个module，直接拷贝到All.dependence.txt(这里的Module之间无关联关系！！)
                # os.system("cat " + self.outdir + "/Listdir/*.list > " + self.outdir + "/Listdir/All.dependence.txt")
            self.log.info("/root/16s/Modules/Generate_pipeline/Generate_main.py运行完成。")

        # Generate_main.py模块会根据参数文件生成result1/qsub.sh，直接提交qsub.sh就可以运行
        # 但是qsub.sh中的project是固定的，如果同时有多个项目投递的时候可能存在重复
        # 所以这里我没有用这个脚本，而是直接调用result1/Listdir/All.dependence.txt，按照时间戳进行提交
        # run_command = "/root/Software/monitor2020/monitor taskmonitor -P " + project + " -q " + queue + " -p " + run_project + " -i " + self.outdir + "/Listdir/All.dependence.txt"
        run_command = monitor_soft + " taskmonitor -q " + queue + " -p " + run_project + " -i " + self.outdir + "/Listdir/All.dependence.txt"

        self.log.info(run_project + "项目monitor开始运行。运行代码： " + run_command)
        # -- 写入qsub命令（用于备份） --
        if os.path.exists(self.outdir + "/qsub_" + self.modelname + ".sh"):
            os.remove(self.outdir + "/qsub_" + self.modelname + ".sh")
        qsub_cmd = open(self.outdir + "/qsub_" + self.modelname + ".sh", "w")
        qsub_cmd.write(run_command)
        qsub_cmd.flush()

        # -- 运行monitor任务 --
        os.system(run_command)
        run_time = self.PrintTime()

        # JudgeRun()判断是否运行完成
        # run_stat = self.JudgeRun2(run_project)
        run_stat = JudgeRun(run_project, self.outdir, self.log, run_time)
        # MkReport()判断运行状态，并生成Report目录，拷贝文件
        self.MkReport(run_stat, run_project, run_time)

    def RunReAnalysis(self, software, database, config, project, queue, monitor_soft):
        '''
            判断是否当前任务之前是否已经投递
            1.是的话则直接进入到判断JudgeRun()和生成Report目录
            2.否则直接重新投递新任务RunModule()
        :return: None
        '''
        # 判断当前project_id是否已经投递，如果是的话则直接跳转到监控模块
        # 有两种思路，一种是用monitor stat -m 2参数(未完成),一种是扫描/root/.new.pymonitor.conf文件获取
        project_all = self.read_conf("/root/.new.pymonitor.conf")
        # 用于标记判断是否是新项目，0为新项目，1表示之前已经投递
        project_all_tag = 0
        # try except监控monitor状态判断及结果判断是否出错
        try:

            for p in project_all:
                # print(p)
                matchObj = re.match(r"^" + self.project_id.lower() + "_" + self.fake_modelname.lower() + "_" + "(\d{4}_\d{2}_\d{2}_\d{2}_\d{2}_\d{2})", p, re.I)
                if matchObj:
                    # print(p)
                    project_all_tag = 1
                    print("项目已被投递monitor，投递编号：" + p)
                    self.log.info("项目已被投递monitor，投递编号：" + p)
                    run_project = p
                    # 刷新Run.tag文件
                    # 对Run.tag文件进行更新
                    if os.path.exists(self.outdir + "/" + self.modelname + ".Run.tag"):
                        os.remove(self.outdir + "/" + self.modelname + ".Run.tag")
                    self.tag = open(self.outdir + "/" + self.modelname + ".Run.tag", "w")
                    self.tag.write(self.project_id + "_" + self.modelname + "：运行中\n")
                    self.tag.flush()
                    # 删除旧的定时记录文件
                    if os.path.exists(self.outdir + "/retry_monitor_stat.txt"):
                        os.remove(self.outdir + "/retry_monitor_stat.txt")
                    # 进行运行状态判断
                    run_time = matchObj.group(1)
                    # print(run_time)
                    run_stat = JudgeRun(run_project, self.outdir, self.log, run_time)
                    # 对运行状态进行处理
                    self.MkReport(run_stat, run_project, run_time)
                    # 当已经识别到旧的monitor任务投递时，不再重复循环，直接退出
                    break
            if project_all_tag == 0:
                self.RunModule(software, database, config, project, queue, monitor_soft)

        except Exception as e:
            # 一旦上述程序块运行中有报错，即返回错误，记录到run.tag文件中，并删除project
            print("程序运行错误!!! \n")
            self.log.error("程序运行错误!!!")
            self.log.error(e)
            self.log.error(traceback.format_exc())
            self.tag.write(self.project_id + "_" + self.modelname + "：失败\n")
            self.tag.flush()
            # os.system(monitor_soft + " removeproject -m 1 -b -p " + run_project)
            exit(1)

if (__name__ == "__main__"):
    parser = argparse.ArgumentParser(description='Please provide module name!')
    parser.add_argument('--config', '-c', required=True, help='')
    parser.add_argument('--modelname', '-m', required=True, help='module name', default="main")
    parser.add_argument('--monitor', '-t', required=False, help='monitor full path', default="/root/Software/monitor2020/monitor")
    # 这里的--project设置的是monitor运行中的-p参数
    parser.add_argument('--project', '-p', required=False, help='project name', default="Test16s")
    parser.add_argument('--queue', '-q', required=False, help='queue name', default="re16s.q")
    # parser.add_argument('--new', '-n', required=False, help='if you want run the project for new, please set!')
    # 需要在config中有输入和输出路径，不需要单独进行设置
    # 还需要有python3的绝对路径，这里要单独写一个softwarelist吗？？只有一个软件暂时先不写
    python_soft = "/root/Software/miniconda3/bin/python3"
    args = parser.parse_args()
    # --- 读取modelname ---
    fake_modelname = args.modelname
    fake_modelname = Tranformodule(fake_modelname)
    # modelname = modelname.lower()
    # 废弃掉了重分析代号，默认全部都为main
    # modelname = Tranformodule(modelname)
    # --- 读取config等 ---
    config = os.path.abspath(args.config)
    # 这里的software和database保留的是所有的模块的！与夏展峰那边的同步！
    software = os.path.abspath(sys.path[0] + "/software")
    database = os.path.abspath(sys.path[0] + "/database")
    project = args.project
    queue = args.queue
    monitor_soft = args.monitor
    # --- 运行程序，并返回log ---
    process = Processing("main", config, fake_modelname)
    process.RunReAnalysis(software, database, config, project, queue, monitor_soft)
