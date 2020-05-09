#!/usr/bin/python
# -*-coding:utf8 -*-

__author__ = "shumingyue"

import sys
import os
import re

import configparser
import argparse

sys.path.append("./")
# import logging
from MyLogger import Logger

'''
    功能：对每个模块的输出文件进行一一检查及修改
    1. 手动编写的文件列表：output_file.list Format: <modelname> <result_file> <Report_file>
    2. 调用修改模块edit_report_file.py，用于修改一一对应的report文件。
    3. 其他重分析流程的fake_modelname必须包含在Report路径下！
    4. main流程对应ReadList()和CheckOutput()函数；其他重分析流程对应ReadList2()和CheckOutput2()函数
'''
def JudgeFile(file):
    '''
        判断文件或文件夹，在outdir是否存在并且不为空
    '''
    if os.path.exists(file) and os.path.getsize(file):
        # return "File exist!"
        return 1
    else:
        # return "File not exist! Please check!"
        return 0

def ReadList(file, outdir, report_dir, Modelname, diff_plan):
    '''
        读取手动编写的相对路径的输出文件列表
        返回模块的所有结果，存为字典数组
        results: [modelname] => [file1,file2,file3,...]
        cp_report: [modelname] => ["cp file1 Reprot/file1","cp file2 Report/HF-NF/file2",...]
    '''
    results = {}
    results[Modelname] = []
    cp_report = {}
    cp_report[Modelname] = []
    for line in open(file):
        if re.match('^\s*$', line):
            continue
        if line.startswith("#"):
            continue
        # 替换<Report>,为实际的目录
        line = line.replace("<Report>", report_dir)

        line = line.strip().split("\t")
        if line[0] == Modelname:
            # 替换文件路径中包含的组名（<g>），方法名（<difference_method>）
            if not diff_plan:
                # 如果没有设置分组，则表示不包含有分组，直接拷贝即可
                file_name = out_dir + "/" + line[1]
                out_name = line[2]
                # # 判断Report文件中的文件路径是否存在，不存在则创建
                # out_dir = os.path.dirname(os.path.abspath(out_name))
                # if not os.path.exists(out_dir):
                #     os.makedirs(out_dir)
                # # 判断Report中的文件是否存在，存在则删除
                # if os.path.exists(out_name):
                #     os.remove(out_name)
                # 录入结果文件到results字典，录入拷贝命令到字典cp_report
                # print(file_name + "\n" + out_name)
                results[line[0]].append(file_name)
                cp_report[line[0]].append("cp " + file_name + " " + out_name)
            else:
                # 包含有分组信息，则需要遍历分组，分别得到各个分组的文件
                for group in diff_plan:
                    group_num = len(group.split("-"))
                    file_name = line[1]
                    out_name = line[2]
                    if group_num > 2:
                        difference_method = "kruskal"
                        # 当大于三组时，判断结果中是否是指定两组的结果，如果是的话则直接掠过
                        if "<g2>" in line[1]:
                            # print(group)
                            continue
                    else:
                        difference_method = "wilcox"
                        file_name = file_name.replace("<g2>", group)
                        out_name = out_name.replace("<g2>", group)
                    file_name = file_name.replace("<g>", group)
                    file_name = file_name.replace("<difference_method>", difference_method)
                    file_name = file_name.replace("<Group_number>", str(group_num))
                    # 将相对路径变成绝对路径
                    file_name = outdir + "/" + file_name
                    out_name = out_name.replace("<g>", group)
                    out_name = out_name.replace("<difference_method>", difference_method)
                    out_name = out_name.replace("<Group_number>", str(group_num))
                    # # 判断Report文件中的文件路径是否存在，不存在则创建
                    # out_dir = os.path.dirname(os.path.abspath(out_name))
                    # if not os.path.exists(out_dir):
                    #     os.makedirs(out_dir)
                    # # 判断Report中的文件是否存在，存在则删除
                    # if os.path.exists(out_name):
                    #     os.remove(out_name)
                    # 录入结果文件到results字典，录入拷贝命令到字典cp_report
                    # print(file_name + "\n" + out_name)
                    results[line[0]].append(file_name)
                    cp_report[line[0]].append("cp " + file_name + " " + out_name)
        else:
            # 如果不包括在output_file.list中的模块，则忽略
            pass

    return results, cp_report


def CheckOutput(Modelname, config, outdir, report_dir, diff_plan):
    '''
        1.（废弃）如果是主程序，则需要判断所有的运行模块(这个步骤放在了ReAnalysis_main.py程序中进行)
        2.当调用主流程时，分别按照main结果中的模块多次调用此程序，默认输出文件list进行判断即可output_file.list
        3.并在outdir生成一个Report目录用于王龙飞提取数据的需求
        4.return返回值为字符串，如果为空的话表示数据完成，否则输出缺失的文件列表str
    '''
    # 设置log
    log = Logger(Modelname + "_output_file_check", outdir)

    # 读取config文件，判断是否存在多个分组，并得到分组列表
    config_paras = configparser.ConfigParser()
    config_paras.read(config)
    # diff_plan = []
    # if config_paras[Modelname].get(Modelname + "_diff_plan"):
    #     anosim_diff_plan = HF-NF,HF-HFH-HFL-HFM,HFH-HFL-HFM-NF,HF-HFH-HFL-HFM-NF
        # diff_plan = config_paras[Modelname].get(Modelname + "_diff_plan").split(",")
    # elif config_paras[Modelname].get(Modelname + "diff_plan"):
        # main程序中的参数
        # diff_plan = HF-NF,HF-HFH-HFL-HFM,HFH-HFL-HFM-NF,HF-HFH-HFL-HFM-NF
        # diff_plan = config_paras[Modelname].get(Modelname + "diff_plan").split(",")

    # 设置检验不存在的文件列表
    no_files = []

    # 新建一个Report目录
    # 在输出目录的前一级目录/maindata/F18FTSECWLJ1207/result/../Report
    # report_dir = outdir + "/../Report"
    if not os.path.exists(report_dir):
        os.makedirs(report_dir)

    # output_file.list是自定义的
    list_file = sys.path[0] + "/output_file.list"
    # list_file = sys.path[0] + "/output_file2.list"
    # 获取对应模块的输出文件列表
    # 如果是文件夹的话要怎么判断呢？？JudgeFile()函数都可以判断
    results, cp_report = ReadList(list_file, outdir, report_dir, Modelname, diff_plan)

    r_index = 0
    for file in results[Modelname]:
        # 遍历所有的results，判断[文件/文件夹]是否存在，以及是否为空
        tag = JudgeFile(file)
        if tag == 0:
            no_files.append(file)
            # log.error(file + " does not exist! Please check!")
            log.warning(file + " does not exist! Please check!")
        else:
            # 如果存在则拷贝到Report目录下面
            # 判断Report文件中的文件路径是否存在，不存在则创建
            report_filename = str(cp_report[Modelname][r_index]).split(" ")[2]
            report_filedir = os.path.dirname(os.path.abspath(report_filename))
            if not os.path.exists(report_filedir):
                os.makedirs(report_filedir)
            # 判断Report中的文件是否存在，存在则删除
            if os.path.exists(report_filename):
                os.remove(report_filename)

            os.system(str(cp_report[Modelname][r_index]))
            log.info(file + " exist, and copy command: " + cp_report[Modelname][r_index])
        r_index += 1

    return no_files

def ReadList2(file, outdir, report_dir, Modelname, diff_plan, fake_modelname):
    '''
        读取手动编写的相对路径的输出文件列表
        返回模块的所有结果，存为字典数组
        results: [modelname] => [file1,file2,file3,...]
        cp_report: [modelname] => ["cp file1 Reprot/file1","cp file2 Report/HF-NF/file2",...]
    '''
    results = {}
    results[Modelname] = []
    cp_report = {}
    cp_report[Modelname] = []
    for line in open(file):
        if re.match('^\s*$', line):
            continue
        if line.startswith("#"):
            continue
        # 替换<Report>,为实际的目录
        line = line.replace("<Report>", report_dir)

        line = line.strip().split("\t")
        # 只匹配包含fake_modelname的文件
        if re.search(r"Report.*" + fake_modelname, line[2], re.I):
            if line[0] == Modelname:
                # 替换文件路径中包含的组名（<g>），方法名（<difference_method>）
                if not diff_plan:
                    # 如果没有设置分组，则表示不包含有分组，直接拷贝即可
                    file_name = out_dir + "/" + line[1]
                    out_name = line[2]
                    # 判断Report文件中的文件路径是否存在，不存在则创建
                    out_dir = os.path.dirname(os.path.abspath(out_name))
                    if not os.path.exists(out_dir):
                        os.makedirs(out_dir)
                    # 判断Report中的文件是否存在，存在则删除
                    if os.path.exists(out_name):
                        os.remove(out_name)
                    # 录入结果文件到results字典，录入拷贝命令到字典cp_report
                    # print(file_name + "\n" + out_name)
                    results[line[0]].append(file_name)
                    cp_report[line[0]].append("cp " + file_name + " " + out_name)
                else:
                    # 包含有分组信息，则需要遍历分组，分别得到各个分组的文件
                    for group in diff_plan:
                        group_num = len(group.split("-"))
                        file_name = line[1]
                        out_name = line[2]
                        if group_num > 2:
                            difference_method = "kruskal"
                            # 当大于三组时，判断结果中是否是指定两组的结果，如果是的话则直接掠过
                            if "<g2>" in line[1]:
                                # print(group)
                                continue
                        else:
                            difference_method = "wilcox"
                            file_name = file_name.replace("<g2>", group)
                            out_name = out_name.replace("<g2>", group)
                        file_name = file_name.replace("<g>", group)
                        file_name = file_name.replace("<difference_method>", difference_method)
                        file_name = file_name.replace("<Group_number>", str(group_num))
                        # 将相对路径变成绝对路径
                        file_name = outdir + "/" + file_name
                        out_name = out_name.replace("<g>", group)
                        out_name = out_name.replace("<difference_method>", difference_method)
                        out_name = out_name.replace("<Group_number>", str(group_num))
                        # 判断Report文件中的文件路径是否存在，不存在则创建
                        out_dir = os.path.dirname(os.path.abspath(out_name))
                        if not os.path.exists(out_dir):
                            os.makedirs(out_dir)
                        # 判断Report中的文件是否存在，存在则删除
                        if os.path.exists(out_name):
                            os.remove(out_name)
                        # 录入结果文件到results字典，录入拷贝命令到字典cp_report
                        # print(file_name + "\n" + out_name)
                        results[line[0]].append(file_name)
                        cp_report[line[0]].append("cp " + file_name + " " + out_name)
            else:
                # 如果不包括在output_file.list中的模块，则忽略
                pass

    return results, cp_report


def CheckOutput2(Modelname, config, outdir, report_dir, diff_plan, fake_modelname):
    '''
        1.如果是单个流程（可能包括多个模块，需要循环调用），则直接调用默认输出文件list进行判断即可output_file_every_module.list
        2.并在outdir生成一个Report目录用于王龙飞提取数据的需求
        3.return返回值为字符串，如果为空的话表示数据完成，否则输出缺失的文件列表str
    '''
    # 设置log
    log = Logger(Modelname + "_output_file_check", outdir)

    # 读取config文件，判断是否存在多个分组，并得到分组列表
    config_paras = configparser.ConfigParser()
    config_paras.read(config)

    # 设置检验不存在的文件列表
    no_files = []

    # 新建一个Report目录
    # 在输出目录的前一级目录/maindata/F18FTSECWLJ1207/result/../Report
    # report_dir = outdir + "/../Report"
    if not os.path.exists(report_dir):
        os.makedirs(report_dir)

    # output_file.list是自定义的
    list_file = sys.path[0] + "/output_file_every_module.list"
    # 获取对应模块的输出文件列表
    # 如果是文件夹的话要怎么判断呢？？JudgeFile()函数都可以判断
    results, cp_report = ReadList2(list_file, outdir, report_dir, Modelname, diff_plan, fake_modelname)

    r_index = 0
    for file in results[Modelname]:
        # 遍历所有的results，判断[文件/文件夹]是否存在，以及是否为空
        tag = JudgeFile(file)
        if tag == 0:
            no_files.append(file)
            log.error(file + " does not exist! Please check!")
        else:
            # 如果存在则拷贝到Report目录下面
            os.system(str(cp_report[Modelname][r_index]))
            log.info(file + " exist, and copy command: " + cp_report[Modelname][r_index])
        r_index += 1

    return no_files