一、功能简介
	ReAnalysis_main.py主要用于根据【流程分析名】和【参数文件】调取夏展峰搭建的分析模块，生成脚本，并投递monitor运行，输出监控文件。运行完成后对结果进行检查和拷贝到Report目录下。

二、模块路径
	模块路径：/root/16s/Reanalysis/result/shumingyue/bin/ReAnalysis_main.py
	输出文件检查list：（程序中在固定路径调用，不用自定义）
	    1.文件路径：（check_output.py程序中调用）
	        -/root/16s/Reanalysis/result/shumingyue/bin/output_file.list（main流程使用）
	        -/root/16s/Reanalysis/result/shumingyue/bin/output_file_every_module.list（单个模块使用）
	    2.文件格式说明：包括三列<modelname> <result_file> <Report_file>
	    3.文件中的标识符说明：
	        <g> 分组名
	        <g2> 两个分组的分组名
	        <difference_method> 差异检验方法（kruskal/wilcox）
	        <Group_number> 分组数
	lib路径：
		1./root/16s/Reanalysis/result/shumingyue/lib/ （需要的包code_to_module.py、check_output.py、MyLogger.py、judge_monitor_run.py）
		2./root/16s/Modules/lib  （用于调用夏展峰的模块）
		3./root/16s/Modules/（用于调用夏展峰的模块）
	软件及数据库配置文件：（需要链接到程序的同一目录下！！）
		1./root/16s/Modules/Generate_pipeline/software
		2./root/16s/Modules/Generate_pipeline/database
	示例数据：/maindata/F18FTSECWLJ1207/result3

三、参数说明
usage: ReAnalysis_main.py [-h] --config CONFIG --modelname MODELNAME
                             [--project PROJECT] [--queue QUEUE]

optional arguments:
  -h, --help            show this help message and exit
  --config CONFIG, -c CONFIG
  --modelname MODELNAME, -m MODELNAME module name （如果是运行主流程则为main）
  --project PROJECT, -p PROJECT project name （可选，默认Test16s）
  --queue QUEUE, -q QUEUE queue name （可选，默认re16s.q）


四、输入文件
Config文件：按照夏展峰提供的模块输入文件即可（其中包括输入文件和输出路径）
module名称：输入王龙飞这边提供的【重分析类型代号】即可。对应关系可以参照代码/root/16s/Reanalysis/result/shumingyue/lib/code_to_module.py进行对应

五、输出文件
    输出结果在Config文件中提供的输出路径中（eg: result/）
1. 结果路径结构如下：
result/
├── Listdir/	# 跑monitor需要的list文件
│   └── *.list
├── *.log	# 此程序运行的Log日志
├── *_output_file_check.log	# 此程序运行的检查输出结果文件的log日志
├── *.Run.tag	# 此程序的监控tag文件（只有运行中和成功/失败输出）
├── process/	# 结果存储路径
└── shell/	# 运行脚本存储路径
    └── *.sh
2. Report/	# 数据拷贝路径

六、使用示例
参考示例：/maindata/F18FTSECWLJ1207/

七、常见问题与处理方法
1. 程序提交会一直保持运行，同时任务投递到monitor上运行，直至监控monitor运行完成/失败后停止
2. 程序如果报错可以查看运行日志：result/*.log（eg: main.log）
3. 如果要增添/修改/删除【重分析类型代号】，请修改/root/16s/Reanalysis/result/shumingyue/lib/code_to_module.py即可
4. 如果主流程(main)的"module_option"参数为"all"有变化，则需要在当前程序进行同步！
5. 如果要增添/修改/删除【Report/】目录下的拷贝文件情况，请修改/root/16s/Reanalysis/result/shumingyue/bin/output_file.list

八、修订记录
1.2020年3月31日修订：
    -在输入module参数中增加可以识别【重分析类型代号】
2.2020年4月1日修订：
    -优先使用config中的"project_id"(如果存在)作为monitor运行的"-P"参数，否则使用程序默认值
    -增加了可以识别主流程(main)的"module_option"参数为"all"的情况
    -增加了生成脚本和运行monitor程序块的try...except...如果程序运行出错会在*Run.tag文件中写入“失败”
3.2020年4月3日修订：（ReAnalysis_main.v3.py）
    -增加了"--monitor"参数，用于指定使用的monitor路径，默认为/root/Software/monitor2020/monitor
    -修改了JudgeRun()函数对monitor状态的判断，只有当搜不到project的时候才会报错，否则会重新调用函数，再次进行刷新
    -增加了可选的JudgeRun2()函数，这个函数是调用夏展峰写的/root/Software/monitor2020/read_db.py，直接读取monitor的db
    -v3默认使用的是JudgeRun2()函数
4.2020年4月10日修订：（修改output_file.list和模块check_output.py）
    -在output_file.list增加了识别标志符"<g2>"，表示两个分组的分组名（由于difference分析中wilcox结果与kruskal结果结构不一致）
    -在output_file.list增加了识别标志符"<Group_number>"，在enterotypes分析中需要输出带有"分组数"的结果（eg: *.JSD_hclust_4_Enterotypes.txt），其中4表示4个分组的分组数
    -将外置程序/root/Software/monitor2020/read_db.py链接到本地，避免程序转移的时候出现问题
5.2020年4月17日修订：（ReAnalysis_main.v4.py）
    -运行主程序函数变为RunReAnalysis()，用于判断如果出现重复投递的情况下是如何继续进行监控的。
    -modelname（模块名），log（程序*.log文件），tag（程序标志文件*Run.tag）变为全局变量，可以在所有函数中调用
    -增加了一个read_conf()函数，读取monitor主/root/.new.pymonitor.conf文件，获取当前所有正在运行的project ID，用于判断当前投递的任务中是否已有投递的任务
    -修改JudgeRun2()函数，增加/root/Software/monitor2020/read_db.py程序参数"-l 1"，列出所有程序状态，遍历输出判断状态
    -增加MkReport()函数，将stat状态判断和写入Report这部分代码单独放到这个函数中，便于直接调用
    -修改RunModule()函数，改为直接调用JudgeRun2()判断状态，MkReport()生成Report目录；增加qsub_*.sh脚本输出便于备份qsub投递命令
    -废弃JudgeRun()函数(使用monitor stat来判断运行状态)
6.2020年4月21日修订：（ReAnalysis_main.v4.py，更改运行程序状态判断的函数）
    -废弃JudgeRun2()函数，增加外置的judge_monitor_run.py模块的JudgeRun()函数用于处理project状态监控，返回当前运行状况。（需要挂起/root/16s/Reanalysis/result/shumingyue/bin/Monitor_stat_retry.py程序，每隔60s不断运行monitor stat命令）
    -修改主程序，去掉所有调用monitor查询和更新的代码，全部改为调用judge_monitor_run.py模块的JudgeRun()函数
    -在运行投递monitor项目后先停顿8s，再进行状态判断
7.2020年4月22日修订：（Monitor_stat_retry.py程序优化和judge_monitor_run.py模块）
    -优化挂起的Monitor_stat_retry.py程序，解决由于调用递归函数出现的栈溢出错误，改为while循环调用
    -进一步修改judge_monitor_run.py模块，将Monitor_stat_retry.py程序不断更新的文件拷贝到当前项目路径后读取
    -测试变更处理运行状态之后的跑主程序运行的稳定性
8.2020年4月23日修订：（ReAnalysis_main.v5.py）
    -更改单个模块的运行方式，全部改为main形式的调取（即只选其中的一个或几个模块运行），因为存在几个模块的相互依赖关系，如Network分析，需要先跑barplot
    -main模块（CheckOutput）和单个模块（CheckOutput2）分别使用不同的函数进行结果文件判断和拷贝到Report目录
    -废弃了code_to_module.py重分析代号，因为所有输入运行的程序都是使用“main”，原来的分析代号(fake_modelname)仅用于命名投递monitor的project
    -解决之前v4模块测试时遗留的一些bug
9.2020年4月24日修订：（ReAnalysis_main.v5.py）
    -优化MkReport()函数，去除冗余代码
    -解决之前v4模块测试时遗留的一些bug
    -增加了单个重新分模块的输出文件检查列表（output_file_every_module.list）
10.2020年4月27日修订：（ReAnalysis_main.v5.py）
    -将【重分析代号】定义为“fake_modelname”，用于提交monitor任务时命名；另一方面用于判断是主程序还是单个模块的分析
    -优化check_output.py模块代码。其他单个重分析流程的fake_modelname必须包含在Report路径下（已定义好），main流程对应ReadList()和CheckOutput()函数；其他重分析流程对应ReadList2()和CheckOutput2()函数进行处理
    -优化程序报错输出
    -单个重分析模块测试，检查Report/输出结果
11.2020年4月28日修订：
    -在judge_monitor_run.py模块中的JudgeRun()函数增加一个"run_time"参数，用于比较当前提交的时间与定时程序生成的文件是否存在时间差
12.2020年5月6日修订：
    -修改output_file.list。增加一列文件名（用于平行判断几个文件是否存在）（check_output.20200507.py）
    -增加”main“程序运行中的heatmap几个文件的平行检查，只要有一个文件缺失就报错，返回失败
    -增加”main“程序运行中OTU以及ANNO的几个必须文件的检查，如果不存在就返回失败
    -修复当程序重复刷新查询状态5次时意外退出的情况。并增加刷新5次仍然报错的log输出；将刷新次数变为9次，刷新时间间隔改为45s
    -修改judge_monitor_run.py模块：将grep匹配换成直接读取定时记录的文件，提高代码运行的稳定性
    -test123


