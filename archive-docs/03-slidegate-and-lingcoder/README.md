# Code Data Pipeline

多模态AI处理管道框架，支持并行处理、续传检查和多种AI模型。

## 组件更新日志

* `2025/07/08` repo创建，从pixmo-docs中迁移到新的repo，更新readme和管道级并行功能

## 🚀 功能特性

- **🔗 灵活的管道架构**：基于Step和Pipeline的模块化设计
- **⚡ 并行处理**：支持管道级别和步骤级别的并行执行
- **💾 智能续传**：自动检查已完成的步骤，支持断点续传
- **🤖 多模型支持**：集成Gemini、Claude、豆包（含dsr1）等多种AI模型
- **🖼️ 多模态输入**：支持文本、图像等多种输入格式
- **📊 统计监控**：实时跟踪处理进度和token使用情况
- **🔄 错误处理**：完善的异常处理和重试机制

## 📦 安装要求

```bash
pip install -r requirements.txt
from string import Template
```
豆包api安装参考代码中的doubao_api_readme.md

或者使用wangbo的环境，公有云：/mnt/afs/wangbo4/.conda/envs/pixmo

## 🏗️ 核心架构

### BaseStep - 处理步骤基类

每个处理步骤继承自`BaseStep`，包含：
- **模型推理**：集成各种AI模型API
- **前处理**：数据预处理和prompt构建
- **后处理**：结果解析和格式化
- **并行控制**：可配置的并发数量

### BasePipeline - 管道基类

管道负责：
- **步骤编排**：管理多个处理步骤的执行顺序
- **并行调度**：协调多线程处理
- **状态管理**：跟踪处理进度和结果缓存
- **数据流转**：在步骤间传递和转换数据

## 📋 快速开始

### 1. 导入key
导入相关模型的key和api，均以环境变量方式设置，具体参考credential.py，相关key按需找相关人员获得
```python
from pipeline.credential import *
```

### 2. 定义prompt模板
**prompt前缀**需包含 **< image >**
```python
ANALYSIS_PROMPT = """<image>
You are an expert in image analysis.

Please analyze the provided image with tags and describe what you see.

The tag of this image is:
{tag}

The answer should follow the following format:
<analysis>
Your detailed analysis here
</analysis>

Please follow the format strictly."""
```

### 3. 定义自定义步骤
**修改引用** 需注意修改import相关模型，同时，需注意init中修改llm为对应模型类
```python
import os
import re

from pipeline.core.base_step import BaseStep
from pipeline.models.gemini_model import GeminiModel

class ImageAnalysisStep(BaseStep):
    def __init__(self, llm: GeminiModel, parallel_num: int, step_name: str, prompt_template: str, prompt_args: list[str]):
        super().__init__(llm=llm, parallel_num=parallel_num, step_name=step_name, prompt_template=prompt_template, prompt_args=prompt_args)
        # 注册结果键，用于续传检查和结果保存
        self.result_key = ["analysis_result"]
        
    def pre_process_prompt(self, data: dict) -> str:
        """重载前处理，用于对数据进行预处理"""
        prompt = super().pre_process_prompt(data)
        return prompt
        
    def post_process(self, data: dict, result: str) -> dict:
        """重载后处理，用于对模型返回结果进行处理"""
        try:
            # 从结果中提取特定信息
            analysis = re.search(r'<analysis>(.*?)</analysis>', result, re.DOTALL).group(1)
            data["analysis_result"] = analysis
        except Exception as e:
            data["analysis_result"] = None
        return data
```

### 4. 定义管道类

```python
from pipeline.core.base_pipeline import BasePipeline

class ImageAnalysisPipeline(BasePipeline):
    def __init__(self, steps: list[BaseStep]):
        super().__init__(steps)
        
    def generate_init_data(self, image_folder: str) -> list[dict]:
        """生成初始数据，对原始输入进行预处理"""
        images = os.listdir(image_folder)
        data = []
        for image in images:
            image_path = os.path.join(image_folder, image)
            # 构建填入prompt template所需要的数据
            data.append({"id": image, "image": image_path, "tag": os.path.splitext(image)[0]})
        return data
```



### 5. 运行管道
**修改注意** 需修改模型名，以及定义Step类中llm名称，使用Claude时，图片需要为jpg格式
```python
def run_image_analysis_pipeline(src_image_folder: str, save_root: str):
    # 配置参数
    parallel_num = 10
    model_name = "gemini-2.0-flash"
    
    # 定义步骤
    analysis_step = ImageAnalysisStep(
        llm=GeminiModel(model_name=model_name),
        parallel_num=parallel_num,
        step_name="ImageAnalysis",
        prompt_template=ANALYSIS_PROMPT,
        # 填入prompt_template所需要的参数名称
        prompt_args=["image", "tag"]
    )
    
    # 创建管道
    pipeline = ImageAnalysisPipeline([analysis_step])
    
    # 生成初始数据
    data = pipeline.generate_init_data(src_image_folder)
    
    # 运行管道（自动并行处理、续传检查）
    pipeline.run_pipeline_parallel(data, save_root, std_log=False,max_workers=10)

if __name__ == "__main__":
    src_image_folder = "/path/to/images"
    save_root = "/path/to/results"
    run_image_analysis_pipeline(src_image_folder, save_root)
```

## 🔧 高级用法

### 多步骤管道

```python
def run_multi_step_pipeline(src_folder: str, save_root: str):
    # 步骤1：图表类型判断
    judge_step = JudgeChartTypeStep(
        llm=GeminiModel(model_name="gemini-2.0-flash"),
        parallel_num=10,
        step_name="JudgeChartType",
        prompt_template=JUDGE_CHART_TYPE_PROMPT,
        prompt_args=["image"]
    )
    
    # 步骤2：代码生成
    code_step = GenerateCodeStep(
        llm=GeminiModel(model_name="gemini-2.0-flash"),
        parallel_num=5,
        step_name="GenerateCode", 
        prompt_template=GENERATE_CODE_PROMPT,
        prompt_args=["image", "chart_type"]
    )
    
    # 创建多步骤管道
    pipeline = MultiStepPipeline([judge_step, code_step])
    data = pipeline.generate_init_data(src_folder)
    pipeline.run_pipeline_parallel(data, save_root)
```

## 📊 运行模式

### 1. 管道级并行 (推荐)
```python
# 每个数据项在独立线程中完成所有步骤
pipeline.run_pipeline_parallel(data, save_root, std_log=False)
```

### 2. 步骤级并行
```python
# 完成一个步骤后再开始下一个步骤
pipeline.run_step_parallel(data, save_root)
```
log构建中

### 3. 单线程处理
```python
# 单个数据项的串行处理
result = pipeline.run_single(data_item)
```

## 📁 输出结构

```
save_root/
├── StepName1_results.jsonl                             # 第一步结果
├── StepName2_20240101_120000_statistics.json           # 第一步统计  
├── StepName2_results.jsonl                             # 第二步结果  
├── StepName2_20240101_120000_statistics.json           # 第二步统计  
├── pipeline_20240101_120000.log                        # 执行日志
├── pipeline_20240101_120000_statistics.json            # 管线统计信息
└── pipeline_final_results.jsonl                        # 最终生成结果
```

## 🛠️ 支持的模型

- **Gemini**: `GeminiModel` - Google的多模态模型
- **Claude**: `ClaudeModel` - Claude-3.7模型
- **Claude**: `Claude4Model` - Claude-4模型
- **豆包**: `DoubaoModel` - 豆包 & DeepSeek模型
- **自定义模型**: 继承`BaseModel`实现

## ⚙️ 配置选项

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `parallel_num` | 并发线程数 | 1 |
| `std_log` | 是否输出到控制台 | False |
| `result_key` | 结果键列表(用于续传) | [] |
| `temperature` | 模型温度参数 | 1.0 |
| `max_tokens` | 最大token数 | 8192 |

## 🔍 续传机制

框架自动实现续传功能：
1. **结果缓存**：每步结果保存到`.jsonl`文件
2. **状态检查**：启动时自动加载已完成的步骤
3. **智能跳过**：只处理未完成的数据项
4. **数据一致性**：确保上游步骤完成才执行下游步骤

## 📈 监控和统计

- **实时进度**：tqdm进度条显示处理状态
- **Token统计**：自动跟踪API调用消耗
- **成功率统计**：监控处理成功/失败/跳过数量
- **详细日志**：完整的执行日志记录

## 🤝 贡献

欢迎提交Issue和Pull Request来改进这个项目！

# 代码管理规范

## 更新日志

* `20250708` 规范第一版

## 基础功能更新要求
1. 在各自分支开发测试，提pr合并到主分支

## 新任务管线开发
1. 在各自开发分支开发测试。
2. 参考xhx_back，在src下新建文件夹，作为项目文件夹。
3. **git主要用于代码托管，不用做试验版本管理。**
3. 基础功能，通过git托管。
4. 不同方案的管线试验，新建代码文件建议以_d{日期}作为脚本后缀来避免重复
5. 避免修改已经产生过数据的管线代码，以保证数据可以以相同方式复现，方便溯源。
6. 尽量固定方法，变量以参数的形式传递到管线中，方便试验时留痕。