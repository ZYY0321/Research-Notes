目的
构造符合实际使用场景的PPTAgent的测试集和训练集
可能的场景清单
编号
任务形式
功能需求（不包含基本的大纲和代码生成）
考察点
1
一句话让模型做个展示的ppt
搜索，搜图，
信息的准确性，图片是否匹配，最终结果和query有没有冲突
2
有比较详细要求输入的ppt生成
任务规划，指令遵循，结果检查，搜索搜图
+ 对用户要求的遵循
3
提供了部分内容，包含文档和要求，做个新的ppt
文档解析，搜索，搜图
+ 文档解析的效果，自主判断是否需要引入搜索/搜图
4
提供了ppt模板，和部分资料和要求，按照模板做个ppt
ppt模板解析，文档解析，搜索，搜图
+ PPT模板样式解析，模型还原PPT效果能力
5
提供了一版已有的PPT、部分资料、以及一些要求
同上
对ppt分析和指令跟随更高的要求
现有数据现状
1. pptx-svg-html数据
  1. [260224] svg2html管线
  2. aoss地址：https://console.ms-sc-01.maoshanwangtech.com/aoss/list/bucket?bucket_name=ppt-data&storage_class=standard&cluster_id=x86-mssc-01a-uuid&tab=overview&out_endpoint=aoss.ms-sc-01.maoshanwangtechapi-oss.com&zone=ms-sc-01a
  3. 约10w高质量的pptx
  4. 仅是模板，无内容，需要模型填充
  5. html管线尚未完成，需要调试开发
2. 回流数据
  1. 待收集过滤
TODO
1. 维护数据信息文档 @王博 @马征 
2. 针对不同场景，设计构造query的方案 @刘波 
3. 针对不同场景，利用已有数据，设计数据构造管线，包含生成和检查 @刘波 

