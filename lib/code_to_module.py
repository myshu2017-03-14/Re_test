#!/usr/bin/python
# -*-coding:utf8 -*-

__author__ = "shumingyue"

import sys
import os
import re

import configparser
import argparse

sys.path.append("./")

'''
    # 对龙飞提供的【重分析类型代码】，对应到展峰的流程中去，使之能够识别展峰的模块程序
    龙飞提供的【重分析类型代码】对应到fake_modelname
    采用字典的存储方式
'''
# dict_module = {
#     "main": "main",
#     "cca": "ccarda",
#     "pca": "pca",
#     "species_heatmap": "heatmap",
#     "species_abundance": "barplot",
#     "diversity_rarefaction": "alpha",
#     "diversity_alphabox": "alpha",
#     "diversity_betaheatmap": "beta, barplot",
#     "diversity_betabox": "beta, barplot",
#     "distance_pcoa": "beta, barplot",
#     "distance_nmds": "nmds",
#     "distance_plsda": "plsda",
#     "species_wilcoxon": "difference",
#     "species_keydiff": "difference",
#     "function_prediction": "picrust",
#     "function_difffunction": "picrust",
#     "otu_rank": "rank",
#     "correlation_heatmap": "network, barplot",
#     "correlation_network": "network, barplot",
#     "lefse": "lefse",
#     "enterotype": "enterotypes",
#     "phylogeny": "basic",
#     "upgma": "beta, barplot",
#     "roc": "random, barplot"
# }
dict_module = {
    "main": "main",
    "cca": "cca",
    "pca": "pca",
    "species_heatmap": "species_heatmap",
    "species_abundance": "species_abundance",
    "diversity_rarefaction": "diversity_rarefaction",
    "diversity_alphabox": "diversity_alphabox",
    "diversity_betaheatmap": "diversity_betaheatmap",
    "diversity_betabox": "diversity_betabox",
    "distance_pcoa": "distance_pcoa",
    "distance_nmds": "distance_nmds",
    "distance_plsda": "distance_plsda",
    "species_wilcoxon": "species_wilcoxon",
    "species_keydiff": "species_keydiff",
    "function_prediction": "function_prediction",
    "function_difffunction": "function_difffunction",
    "otu_rnak": "otu_rank",  # 后续可以改下
    "correlation_heatmap": "correlation_heatmap",
    "correlation_network": "correlation_network",
    "lefse": "lefse",
    "enterotype": "enterotype",
    "phylogeny": "phylogeny",
    "upgma": "upgma",
    "roc": "roc",

}

def Tranformodule(module):
    '''
        如果module在上述列表中不存在，则报错
    '''
    module = module.lower()
    if module in dict_module.keys():
        return dict_module[module]
    else:
        print("没有找到" + module + "，请检查！可用的module包括：[" + ",".join(dict_module.keys()) + "]")
        # return module
        return "Not Found"
        # exit(1)
