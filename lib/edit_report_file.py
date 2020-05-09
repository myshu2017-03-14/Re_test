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
    对每个模块的输出文件进行一一修改，得到王龙飞上传到数据库需要的文件
    传入参数为模块名称，及Report文件, 输出文件
'''
class JudgeAndEditFile():
    def __init__(self, modelname, report_file, output_file):
        self.report_file = os.path.abspath(report_file)
        self.modelname = modelname
        self.output_file = os.path.abspath(output_file)
        # 运行编辑程序
        self.RunEdit()
    def otu_file_edit(self):
        pass
    def run_judge_and_edit(self, modelname):
        # 根据模块名称调用相应的编辑函数
        if self.modelname == "otu":
            self.otu_file_edit()
        # elif self.modelname == "anno":
        #     self.anno_file_edit()
        # elif self.modelname == "basic":
        #     self.basic_file_edit()
        # elif self.modelname == "barplot":
        #     self.barplot_file_edit()
        # elif self.modelname == "pca":
        #     self.pca_file_edit()
        # elif self.modelname == "nmds":
        #     self.nmds_file_edit()
        # elif self.modelname == "plsda":
        #     self.plsda_file_edit()
        # elif self.modelname == 'beta':
        #     self.beta_file_edit()
        # elif self.modelname == "alpha":
        #     self.alpha_file_edit()

