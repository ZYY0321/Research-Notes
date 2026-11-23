# 评估脚本使用说明

## 1. HumanEvalFix 一键运行脚本

### 功能
在多个不同的tmux会话中并行运行不同语言的HumanEvalFix评估。

### 用法
```bash
cd /mnt/afs/zhangyingying
./run_humanevalfix_all.sh <api-url> <model-name> [languages]
```

### 示例
```bash
# 运行所有默认语言（python, js, cpp, java, go）
./run_humanevalfix_all.sh http://10.119.31.130:8000/v1 code_ablation_lingcoder_multilang_humanevalx_go_v1_20251203

# 只运行特定语言
./run_humanevalfix_all.sh http://10.119.31.130:8000/v1 model_name "python,js,cpp"
```

### 参数说明
- `api-url`: API服务地址
- `model-name`: 模型名称
- `languages` (可选): 逗号分隔的语言列表，默认: python,js,cpp,java,go

### 结果位置
结果保存在: `/mnt/afs/zhangyingying/results_<语言>_full/`

### 管理会话
```bash
# 查看所有会话
tmux ls | grep humanevalfix

# 附加到某个会话
tmux attach -t humanevalfix_python
tmux attach -t humanevalfix_js
tmux attach -t humanevalfix_cpp

# 终止所有会话
tmux kill-session -t humanevalfix_python
tmux kill-session -t humanevalfix_js
tmux kill-session -t humanevalfix_cpp
tmux kill-session -t humanevalfix_java
tmux kill-session -t humanevalfix_go
```

---

## 2. CruxEval 一键运行脚本

### 功能
运行8个CruxEval任务（4个生成 + 4个评估），支持并行或串行运行。

### 用法
```bash
cd /mnt/afs/zhangyingying
./run_cruxeval_all.sh <output_model> <input_model> [api_url] [temperature] [n_samples]
```

### 示例
```bash
# 使用默认参数
./run_cruxeval_all.sh \
  code_ablation_lingcoder_set2_data_science_python_v1_20251203 \
  code_ablation_lingcoder_set2_data_science_python_v1_20251203

# 指定所有参数
./run_cruxeval_all.sh \
  code_ablation_lingcoder_set2_data_science_python_v1_20251203 \
  code_ablation_lingcoder_set2_data_science_python_v1_20251203 \
  http://10.119.19.90:8000/v1 \
  0.2 \
  800
```

### 参数说明
- `output_model`: OUTPUT模式使用的模型名称
- `input_model`: INPUT模式使用的模型名称
- `api_url` (可选): API服务地址，默认: http://10.119.19.90:8000/v1
- `temperature` (可选): 温度参数，默认: 0.2
- `n_samples` (可选): 样本数量，默认: 800

### 运行的任务
脚本会运行以下8个任务（4个生成 + 4个评估）：
1. OUTPUT模式 + CoT
2. OUTPUT模式 + 非CoT
3. INPUT模式 + CoT
4. INPUT模式 + 非CoT

### 结果位置
结果保存在: `/mnt/afs/zhangyingying/cruxeval/model_generations/<模型名>+cot_temp<温度>_<模式>_n<样本数>/`

### 管理会话（如果使用tmux）
```bash
# 查看所有会话
tmux ls | grep cruxeval

# 附加到某个会话
tmux attach -t cruxeval_output_cot
tmux attach -t cruxeval_output_nocot
tmux attach -t cruxeval_input_cot
tmux attach -t cruxeval_input_nocot

# 终止所有会话
tmux kill-session -t cruxeval_output_cot
tmux kill-session -t cruxeval_output_nocot
tmux kill-session -t cruxeval_input_cot
tmux kill-session -t cruxeval_input_nocot
```

---

## 注意事项

1. **tmux要求**: 如果系统未安装tmux，脚本会串行运行所有任务（CruxEval）或提示错误（HumanEvalFix）。

2. **API服务**: 确保API服务已启动并可访问。

3. **资源占用**: 并行运行会占用更多资源，请确保有足够的GPU/CPU资源。

4. **结果检查**: 任务完成后，检查结果文件是否正常生成。

5. **错误处理**: 如果某个任务失败，可以单独重新运行该任务。







