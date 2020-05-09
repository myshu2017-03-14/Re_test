#!/usr/bin/python
# -*-coding:utf8 -*-

__author__ = "shumingyue"

import sys
import os

import logging
'''
    设置可以调用Logging单独的模块，设置固定格式直接进行调用
    
'''


def Logger(Modelname, out_dir):
    '''
        日志功能模块
    '''
    # 创建一个logger
    logger = logging.getLogger(Modelname)
    logger.setLevel(logging.DEBUG)

    # 创建一个handler，用于写入日志文件
    fn = logging.FileHandler(out_dir + '/' + Modelname + '.log')
    fn.setLevel(logging.DEBUG)

    # 定义handler的输出格式，eg：[2020-03-17 09:24:40,581 pca] INFO 此处开始运行【pca】
    # formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    formatter = logging.Formatter('[%(asctime)s %(name)s] %(levelname)s %(message)s')
    fn.setFormatter(formatter)

    # 给logger添加handler
    logger.addHandler(fn)
    return logger