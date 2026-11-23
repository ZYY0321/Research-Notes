#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
蒸馏Python代码中使用第三方库的数据

流程：
1. 使用 extract_libraries.py 分类数据，区分出 Python+标准库 和 Python+第三方库
2. 保存中间分类结果
3. 提取Python+第三方库的数据，删除原模型回复，保存为种子数据
4. 调用 DeepSeek V3.2 API (10.119.25.241:8000)，禁止思考模式
5. 让模型只输出代码块，格式是 ```python```
6. 结果保存到 /mnt/afs/zhangyingying/sft_tag/distilled_data

使用方法：
    python 蒸馏非Python和第三方库数据.py <input_file> [start_idx] [max_items]
    
示例：
    python 蒸馏非Python和第三方库数据.py seed_data_all_ds.jsonl 0 100
"""

import json
import os
import re
import sys
import time
import hashlib
import threading
import socket
import requests
import uuid as uuid_module
from pathlib import Path
from typing import Dict, List, Set, Any
from concurrent.futures import ThreadPoolExecutor, as_completed

# DNS 覆盖：将 api.schedule.mtc.sensetime.com 解析到 172.19.57.3
_original_getaddrinfo = socket.getaddrinfo

def _patched_getaddrinfo(*args):
    host = args[0]
    if host == 'api.schedule.mtc.sensetime.com':
        return _original_getaddrinfo('172.19.57.3', *args[1:])
    return _original_getaddrinfo(*args)

socket.getaddrinfo = _patched_getaddrinfo

# 导入 openai_proxy
gpt_proxy_path = Path(__file__).parent.parent / 'distill_proxy' / 'gpt_proxy_client'
sys.path.insert(0, str(gpt_proxy_path))

try:
    import openai_proxy
    from openai_proxy import generate as openai_proxy_generate
    
    # 修改 URL 为 IP 地址并添加 Host 头
    if hasattr(openai_proxy_generate, 'default_url'):
        original_url = openai_proxy_generate.default_url
        if 'api.schedule.mtc.sensetime.com' in original_url:
            openai_proxy_generate.default_url = original_url.replace(
                'api.schedule.mtc.sensetime.com', '172.19.57.3'
            )
            
            # Patch: 添加 Host 头支持
            original_init = openai_proxy_generate.GptProxy.__init__
            original_post_json = openai_proxy_generate.GptProxy._post_json
            
            def patched_init(self, api_key=None, base_url=None):
                original_init(self, api_key, base_url)
                if '172.19.57.3' in self.url_base:
                    self._original_host = 'api.schedule.mtc.sensetime.com'
                else:
                    self._original_host = None
            
            def patched_post_json(self, url, json_data={}, params={}):
                headers = self.headers.copy()
                headers['Content-Type'] = 'application/json'
                if hasattr(self, '_original_host') and self._original_host:
                    headers['Host'] = self._original_host
                data = json.dumps(json_data, ensure_ascii=False).encode('utf8')
                # 增加超时时间到120秒
                return requests.post(url, headers=headers, params=params, data=data, timeout=120)
            
            openai_proxy_generate.GptProxy.__init__ = patched_init
            openai_proxy_generate.GptProxy._post_json = patched_post_json
            
except ImportError:
    print("错误: 无法导入 openai_proxy")
    print(f"请先安装: cd {gpt_proxy_path} && pip install -e .")
    sys.exit(1)

# 添加 extract_libraries.py 的路径
sys.path.insert(0, str(Path(__file__).parent.parent / 'Tag_multi_data' / 'library_classification_tools'))
from extract_libraries import (
    extract_code_from_conversations,
    extract_imports_from_code,
    classify_libraries
)

# 配置
# 支持多个模型，可以轮换使用以分散资源压力
AVAILABLE_MODELS = [
    "deepseek-v3.2-251201-2",
    "deepseek-v3.2-251201"
]
API_MODEL = AVAILABLE_MODELS[0]  # 默认模型
API_KEY_FILE = Path(__file__).parent.parent / 'distill_proxy' / 'apikey.txt'
SEED_DATA_DIR = Path(__file__).parent / "种子数据"
DISTILLED_DATA_DIR = Path(__file__).parent.parent / "distilled_data"
INTERMEDIATE_DATA_DIR = Path(__file__).parent / "中间结果"

# 创建必要的目录
DISTILLED_DATA_DIR.mkdir(parents=True, exist_ok=True)
INTERMEDIATE_DATA_DIR.mkdir(parents=True, exist_ok=True)


def extract_code_from_conversations_enhanced(conversations: List[Dict]) -> str:
    """增强版代码提取函数，支持SWE数据格式（--- BEGIN FILE ---标记）
    
    从conversations中提取代码文本，包括：
    1. SWE格式的代码文件（--- BEGIN FILE ---标记）
    2. 普通代码块（```python或```py标记）
    3. 包含Python特征的文本内容
    """
    code_blocks = []
    
    for conv in conversations:
        content = conv.get("value", "") or conv.get("content", "")
        if not content:
            continue
        
        # 移除推理标签（支持多种格式）
        content = re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL | re.IGNORECASE)
        content = re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL | re.IGNORECASE)
        
        # 1. 提取 SWE 格式的代码文件（--- BEGIN FILE ---标记）
        # 格式: --- BEGIN FILE ---\n```\n### path/to/file.py\n代码内容\n```\n--- END FILE ---
        file_pattern = re.compile(
            r'---\s*BEGIN\s+FILE\s*---.*?```\s*\n###\s+([^\n]+\.py)\s*\n(.*?)```',
            re.DOTALL | re.IGNORECASE
        )
        file_matches = file_pattern.findall(content)
        for file_path, code in file_matches:
            # 只提取Python文件
            if '.py' in file_path.lower():
                code_blocks.append(code.strip())
        
        # 2. 提取普通代码块（```python 或 ```py）
        code_pattern = re.compile(r'```(?:python|py)?\s*\n(.*?)```', re.DOTALL)
        blocks = code_pattern.findall(content)
        if blocks:
            code_blocks.extend(blocks)
        
        # 3. 如果包含Python特征但没有代码块标记，也尝试提取
        if not blocks and not file_matches:
            # 检查是否包含Python代码特征
            if re.search(r'^\s*(?:import|from|def|class|if\s+__name__|for\s+|while\s+)', content, re.MULTILINE):
                # 提取看起来像代码的部分（跳过markdown标记和说明文字）
                lines = content.split('\n')
                code_lines = []
                in_code_section = False
                for line in lines:
                    # 跳过明显的markdown标记和说明
                    if line.strip().startswith('#') or line.strip().startswith('```') or \
                       line.strip().startswith('---') or not line.strip():
                        continue
                    if re.match(r'^\s*(import|from|def|class)', line):
                        in_code_section = True
                    if in_code_section:
                        code_lines.append(line)
                if code_lines:
                    code_blocks.append('\n'.join(code_lines))
    
    return "\n".join(code_blocks)


def detect_language_from_code(code_text: str) -> str:
    """从代码中检测编程语言"""
    # 简单的语言检测
    code_lower = code_text.lower()
    
    # JavaScript/TypeScript
    if re.search(r'\b(function|const|let|var|=>|\.map\(|\.filter\(|console\.)', code_lower):
        if re.search(r'<script|document\.|window\.|require\(', code_lower):
            return 'javascript'
        if re.search(r'interface\s+\w+|type\s+\w+\s*=|:\s*\w+\s*[=&]', code_lower):
            return 'typescript'
        return 'javascript'
    
    # Java
    if re.search(r'\b(public\s+class|import java\.|System\.out\.|@Override)', code_lower):
        return 'java'
    
    # C/C++
    if re.search(r'#include\s*<|std::|using namespace std;|int main\(', code_lower):
        if re.search(r'std::|using namespace|cout\s*<<', code_lower):
            return 'cpp'
        return 'c'
    
    # Go
    if re.search(r'package\s+\w+|func\s+\w+|:=|fmt\.Print', code_lower):
        return 'go'
    
    # Rust
    if re.search(r'fn\s+\w+|let\s+\w+:|println!|use\s+std::', code_lower):
        return 'rust'
    
    # Python (default)
    return 'python'


def extract_question_from_data(data_item: Dict) -> str:
    """从数据项中提取问题（user/human的输入）"""
    conversations = data_item.get("conversations", [])
    if not conversations:
        conversations = data_item.get("messages", [])
    
    for conv in conversations:
        if conv.get("from") == "human" or conv.get("role") == "user":
            return conv.get("value", "") or conv.get("content", "")
    
    return ""


def build_prompt(question: str) -> str:
    """构建提示词：要求只输出代码块"""
    return f"""你是一位经验丰富的编程专家。请为以下编程问题提供代码解决方案。

重要要求：
1. 只输出代码，不要任何解释说明、注释或其他文字
2. 代码必须放在代码块中，使用 ```语言 标记（语言根据问题自动判断，如python、javascript、java、cpp等）
3. 代码要完整、可直接运行
4. 不要输出思考过程，不要输出"解释说明"、"示例演示"等文字

请直接输出代码：

---
{question}
---
"""


def call_deepseek_api(client, question: str, api_key: str, model: str = None, max_retries: int = 5, thread_id: int = 0) -> Dict[str, Any]:
    """调用 DeepSeek V3.2 API 生成代码回答（禁止思考模式，使用 openai_proxy）
    
    改进的重试策略：
    - 增加重试次数到5次
    - 对连接错误使用更长的等待时间
    - 智能退避策略
    
    Args:
        model: 指定使用的模型，如果为None则使用默认模型
        thread_id: 线程ID，用于生成唯一的transaction_id
    """
    if model is None:
        model = API_MODEL
    
    messages = [
        {"role": "system", "content": "You are a helpful programming assistant."},
        {"role": "user", "content": build_prompt(question)}
    ]
    
    # 生成唯一的transaction_id，包含模型标识和线程ID，避免冲突
    # 使用模型名、线程ID、毫秒时间戳和UUID确保唯一性
    model_safe = model.replace('-', '_').replace('.', '_')[:20]  # 模型名简化
    unique_id = str(uuid_module.uuid4())[:8]  # 使用UUID确保唯一性
    timestamp_ms = int(time.time() * 1000)
    
    for attempt in range(max_retries):
        try:
            # transaction_id格式: distill_{model}_{thread_id}_{timestamp_ms}_{unique_id}_{attempt}
            transaction_id = f"distill_{model_safe}_{thread_id}_{timestamp_ms}_{unique_id}_{attempt}"
            
            rsp = client.generate(
                messages=messages,
                model=model,
                channel_code="doubao",
                transaction_id=transaction_id,
                max_tokens=32768,
                # 不传 thinking 参数，禁止思考模式
            )
            
            if rsp.ok:
                result = rsp.json()
                if result.get('code') == 10000:
                    response_data = result.get('data', {})
                    response_content = response_data.get('response_content', '')
                    
                    if isinstance(response_content, str):
                        try:
                            response_content = json.loads(response_content)
                        except:
                            pass
                    
                    if isinstance(response_content, dict):
                        choices = response_content.get('choices', [])
                        if choices:
                            message = choices[0].get('message', {})
                            content = message.get('content', '')
                            
                            return {
                                'success': True,
                                'content': content
                            }
                    
                    return {'success': True, 'content': str(response_content)}
                else:
                    error_msg = result.get('msg', 'Unknown error')
                    print(f"  ✗ API 错误: {error_msg}")
                    if attempt < max_retries - 1:
                        # 智能退避：系统繁忙等待更久
                        if '系统繁忙' in error_msg or 'busy' in error_msg.lower():
                            wait_time = min(60, 5 * (2 ** attempt))  # 5s, 10s, 20s, 40s, 60s
                        else:
                            wait_time = 2 ** attempt
                        print(f"    等待 {wait_time}秒后重试...")
                        time.sleep(wait_time)
                        continue
                    return {'success': False, 'error': error_msg}
            else:
                error_text = rsp.text[:200] if hasattr(rsp, 'text') else str(rsp.status_code)
                print(f"  ✗ HTTP 错误: {rsp.status_code} - {error_text}")
                if attempt < max_retries - 1:
                    wait_time = min(30, 3 * (2 ** attempt))
                    print(f"    等待 {wait_time}秒后重试...")
                    time.sleep(wait_time)
                    continue
                return {'success': False, 'error': f"HTTP {rsp.status_code}"}
        
        except Exception as e:
            error_str = str(e)
            error_type = type(e).__name__
            
            # 判断错误类型并采用不同的退避策略
            is_connection_error = (
                'Connection' in error_str or 
                'Connection refused' in error_str or
                'Connection reset' in error_str or
                'Connection aborted' in error_str or
                'reset' in error_str.lower()
            )
            
            print(f"  ✗ 异常: {error_str[:100]}")
            if attempt < max_retries - 1:
                # 连接错误使用更长的等待时间（5s, 10s, 20s, 40s）
                if is_connection_error:
                    wait_time = min(45, 5 * (2 ** attempt))
                else:
                    wait_time = 2 ** attempt
                print(f"    等待 {wait_time}秒后重试...")
                time.sleep(wait_time)
                continue
            return {
                'success': False,
                'error': f"{error_type}: {error_str[:200]}"
            }
    
    return {'success': False, 'error': 'Max retries exceeded'}


def extract_code_from_response(content: str) -> str:
    """从回答中提取代码块，格式化为 ```语言``` 格式"""
    # 提取所有代码块
    code_pattern = re.compile(r'```(\w+)?\s*\n(.*?)```', re.DOTALL)
    matches = code_pattern.findall(content)
    
    if matches:
        # 如果有多个代码块，合并它们
        code_blocks = []
        for lang, code in matches:
            lang = lang.strip() if lang else 'python'
            code_blocks.append(f"```{lang}\n{code}\n```")
        
        if len(code_blocks) == 1:
            return code_blocks[0]
        else:
            # 多个代码块，合并
            return '\n\n'.join(code_blocks)
    else:
        # 如果没有代码块标记，但包含明显的代码特征，尝试检测语言并包装
        if re.search(r'^\s*(?:import|from|def|class|if __name__|function|const|let|var|public\s+class|#include)', content, re.MULTILINE):
            lang = detect_language_from_code(content)
            return f"```{lang}\n{content.strip()}\n```"
        # 如果没有代码特征，返回空
        return ""


def classify_data(input_file: str, output_classification_file: str) -> List[Dict]:
    """使用 extract_libraries.py 分类数据，并在处理过程中定期保存结果"""
    print("=" * 80)
    print("步骤1: 分类数据（区分 Python+标准库 和 Python+第三方库）")
    print("=" * 80)
    
    classification_results = []
    stats = {
        'total': 0,
        'python_stdlib_only': 0,  # Python但只使用标准库（跳过）
        'python_third_party': 0,  # Python且使用第三方库（需要蒸馏）
        'skip': 0,  # 非Python或没有代码（跳过）
    }
    
    # 检查是否已有部分结果（支持断点续传）
    existing_results = []
    if Path(output_classification_file).exists():
        print(f"发现已有分类结果文件，读取已处理的数据...")
        with open(output_classification_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    try:
                        existing_results.append(json.loads(line.strip()))
                    except:
                        pass
        if existing_results:
            # 统计已有结果
            for result in existing_results:
                category = result.get('category', 'unknown')
                if category in stats:
                    stats[category] += 1
                stats['total'] += 1
            print(f"已读取 {len(existing_results)} 条已有分类结果")
    
    # 打开文件进行追加或写入
    file_mode = 'a' if existing_results else 'w'
    f_out = open(output_classification_file, file_mode, encoding='utf-8')
    
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                if not line.strip():
                    continue
                
                try:
                    data = json.loads(line.strip())
                    conversations = data.get("conversations", [])
                    if not conversations:
                        conversations = data.get("messages", [])
                    
                    if not conversations:
                        continue
                    
                    stats['total'] += 1
                    
                    # 生成稳定的标识符（如果没有uuid，使用数据内容的hash）
                    uuid = data.get('uuid', '')
                    if not uuid:
                        # 使用数据内容的hash作为稳定的标识符
                        # 只hash关键字段，保证稳定性
                        key_data = {
                            'source': data.get('source', ''),
                            'category': data.get('category', ''),
                            'messages': data.get('messages', data.get('conversations', []))
                        }
                        key_str = json.dumps(key_data, sort_keys=True, ensure_ascii=False)
                        uuid = hashlib.md5(key_str.encode('utf-8')).hexdigest()
                    
                    # 提取代码（使用增强版，支持SWE格式）
                    code_text = extract_code_from_conversations_enhanced(conversations)
                    
                    # 检查是否为Python代码（通过检查代码中是否有Python特征）
                    is_python = False
                    if code_text:
                        # 检查是否有Python代码特征
                        python_patterns = [
                            r'\b(import|from)\s+\w+',
                            r'\bdef\s+\w+\s*\(',
                            r'\bclass\s+\w+',
                            r'\bif\s+__name__\s*==',
                            r'print\s*\(',
                        ]
                        is_python = any(re.search(pattern, code_text, re.MULTILINE) for pattern in python_patterns)
                    
                    # 只处理Python代码
                    if is_python and code_text:
                        libraries = extract_imports_from_code(code_text)
                        classification = classify_libraries(libraries)
                        is_stdlib_only = classification['is_stdlib_only']
                        
                        if is_stdlib_only:
                            # Python但只使用标准库，不需要蒸馏
                            category = 'python_stdlib_only'
                            stats['python_stdlib_only'] += 1
                        else:
                            # Python且使用了第三方库，需要蒸馏
                            category = 'python_third_party'
                            stats['python_third_party'] += 1
                    else:
                        # 非Python代码或没有代码，不需要蒸馏（跳过）
                        category = 'skip'
                        stats['skip'] += 1
                    
                    result = {
                        'uuid': uuid,  # 使用生成的或原有的uuid
                        'line_num': line_num,
                        'category': category,
                        'original_data': data,  # 保持原始数据不变，不添加uuid字段
                        'code_text': code_text[:500] if code_text else '',
                        'is_python': is_python,
                    }
                    classification_results.append(result)
                    
                    # 立即保存到文件（追加模式）
                    f_out.write(json.dumps(result, ensure_ascii=False) + '\n')
                    f_out.flush()  # 确保立即写入磁盘
                    
                    if line_num % 1000 == 0:
                        print(f"已处理 {line_num} 条... (Python+标准库: {stats['python_stdlib_only']}, Python+第三方库: {stats['python_third_party']}, 跳过: {stats['skip']})")
                        print(f"  已保存到: {output_classification_file}")
                
                except json.JSONDecodeError as e:
                    print(f"第 {line_num} 行JSON解析错误: {e}")
                    continue
                except Exception as e:
                    print(f"第 {line_num} 行处理错误: {e}")
                    continue
    
    finally:
        f_out.close()
    
    # 合并已有结果和新结果
    all_results = existing_results + classification_results
    
    print(f"\n分类完成:")
    print(f"  总计: {stats['total']} 条")
    print(f"  Python+标准库（跳过）: {stats['python_stdlib_only']} 条 ({stats['python_stdlib_only']/stats['total']*100:.2f}%)")
    print(f"  Python+第三方库（需要蒸馏）: {stats['python_third_party']} 条 ({stats['python_third_party']/stats['total']*100:.2f}%)")
    print(f"  非Python或没有代码（跳过）: {stats['skip']} 条 ({stats['skip']/stats['total']*100:.2f}%)")
    print(f"\n分类结果已保存到: {output_classification_file}")
    print(f"总计保存: {len(all_results)} 条分类结果")
    
    return all_results


def create_seed_data(classification_results: List[Dict], output_seed_file: str):
    """创建种子数据（删除原模型回复）"""
    print("\n" + "=" * 80)
    print("步骤2: 创建种子数据（删除原模型回复）")
    print("=" * 80)
    
    seed_data = []
    uuid_mapping = []  # 保存uuid到数据的映射关系
    
    for result in classification_results:
        if result['category'] == 'python_third_party':  # 只处理Python+第三方库的数据
            original_data = result['original_data'].copy()
            
            # 删除 assistant/gpt 的回复
            conversations = original_data.get("conversations", [])
            if not conversations:
                conversations = original_data.get("messages", [])
            
            filtered_conversations = []
            for conv in conversations:
                # 保留 user/human 的消息
                if conv.get("from") in ["human", "user"] or conv.get("role") in ["user", "human"]:
                    filtered_conversations.append(conv)
                # 跳过 assistant/gpt 的回复
            
            # 根据原始数据格式设置（保持原始格式，不修改其他字段）
            if "conversations" in original_data:
                original_data["conversations"] = filtered_conversations
            if "messages" in original_data:
                original_data["messages"] = filtered_conversations
            
            # 保存uuid映射关系（不修改原始数据）
            uuid_mapping.append(result['uuid'])
            seed_data.append(original_data)
    
    # 保存种子数据（不包含uuid字段，保持原始数据格式）
    with open(output_seed_file, 'w', encoding='utf-8') as f:
        for data in seed_data:
            f.write(json.dumps(data, ensure_ascii=False) + '\n')
    
    print(f"种子数据已保存: {len(seed_data)} 条")
    print(f"保存位置: {output_seed_file}")
    
    # 返回seed_data和uuid_mapping的元组，以便distill_data可以使用uuid
    return seed_data, uuid_mapping


# 文件写入锁（用于多线程安全）
file_lock = threading.Lock()

def distill_data(seed_data: List[Dict], uuid_mapping: List[str], output_file: str, start_idx: int = 0, max_items: int = None, num_threads: int = 1, model: str = None):
    """使用 DeepSeek API 蒸馏数据（支持单线程或多线程并发）
    
    Args:
        model: 指定使用的模型，如果为None则使用默认模型。也可以传入模型列表进行轮换
    """
    print("\n" + "=" * 80)
    print("步骤3: 使用 DeepSeek API 生成新回复")
    print("=" * 80)
    
    if model:
        print(f"使用模型: {model}")
    
    if num_threads > 1:
        print(f"使用 {num_threads} 个线程并发处理")
        return distill_data_multithreaded(seed_data, uuid_mapping, output_file, start_idx, max_items, num_threads, model)
    else:
        print("使用单线程处理")
        return distill_data_serial(seed_data, uuid_mapping, output_file, start_idx, max_items, model)


def load_api_key():
    """加载 API Key"""
    if API_KEY_FILE.exists():
        with open(API_KEY_FILE, 'r') as f:
            return f.read().strip()
    else:
        print(f"警告: API Key 文件不存在: {API_KEY_FILE}")
        return "dummy"

def distill_data_serial(seed_data: List[Dict], uuid_mapping: List[str], output_file: str, start_idx: int = 0, max_items: int = None, model: str = None):
    """单线程版本的蒸馏数据
    
    Args:
        model: 指定使用的模型，如果为None则使用默认模型
    """
    # 加载 API Key
    api_key = load_api_key()
    
    # 初始化 API 客户端（使用 openai_proxy）
    client = openai_proxy.GptProxy(api_key=api_key)
    
    # 检查已处理的数据（支持断点续传）
    processed_uuids = set()
    if os.path.exists(output_file):
        with open(output_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    try:
                        item = json.loads(line.strip())
                        uuid = item.get('uuid', '')
                        if uuid:
                            processed_uuids.add(uuid)
                    except:
                        pass
    
    print(f"已处理: {len(processed_uuids)} 条")
    print(f"开始处理: 从第 {start_idx} 条开始，最多处理 {max_items or '全部'} 条\n")
    
    # 处理数据
    end_idx = start_idx + max_items if max_items else len(seed_data)
    data_to_process = seed_data[start_idx:end_idx]
    uuid_to_process = uuid_mapping[start_idx:end_idx]
    
    success_count = 0
    fail_count = 0
    
    with open(output_file, 'a', encoding='utf-8') as f:
        for idx, data_item in enumerate(data_to_process):
            # 从uuid_to_process获取uuid
            uuid = uuid_to_process[idx] if idx < len(uuid_to_process) else ''
            if uuid in processed_uuids:
                print(f"[{idx+1}/{len(data_to_process)}] 跳过已处理: {uuid[:8]}...")
                continue
            
            print(f"[{idx+1}/{len(data_to_process)}] 处理: {uuid[:8]}...", end=' ', flush=True)
            
            # 提取问题
            question = extract_question_from_data(data_item)
            if not question:
                print("✗ 无法提取问题")
                fail_count += 1
                continue
            
            # 调用 API
            result = call_deepseek_api(client, question, api_key, model)
            
            if result['success']:
                # 提取代码块
                generated_code = extract_code_from_response(result['content'])
                
                if generated_code:
                    # 构建输出数据
                    output_data = {
                        'uuid': uuid,
                        'original_question': question,
                        'metadata': {
                            'model': API_MODEL,
                            'thinking_mode': False,
                            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
                        },
                        'generated_answer': generated_code
                    }
                    
                    f.write(json.dumps(output_data, ensure_ascii=False) + '\n')
                    f.flush()
                    
                    print(f"✓ 成功")
                    success_count += 1
                else:
                    print(f"✗ 无法提取代码块")
                    fail_count += 1
            else:
                print(f"✗ API失败: {result.get('error', 'Unknown error')}")
                fail_count += 1
            
            # 避免请求过快
            time.sleep(0.5)
    
    print(f"\n蒸馏完成:")
    print(f"  成功: {success_count} 条")
    print(f"  失败: {fail_count} 条")
    print(f"  结果已保存到: {output_file}")


def process_single_item(item_data: tuple, thread_id: int, api_key: str, model: str = None) -> Dict:
    """处理单个数据项（用于多线程）
    
    Args:
        model: 指定使用的模型，如果为None则使用默认模型
    """
    data_item, uuid = item_data
    
    # 每个线程创建自己的客户端（使用 openai_proxy）
    client = openai_proxy.GptProxy(api_key=api_key)
    
    # 提取问题
    question = extract_question_from_data(data_item)
    if not question:
        return {
            'uuid': uuid,
            'success': False,
            'error': '无法提取问题'
        }
    
    # 调用 API（传入thread_id确保transaction_id唯一）
    result = call_deepseek_api(client, question, api_key, model, thread_id=thread_id)
    
    if result['success']:
        # 提取代码块
        generated_code = extract_code_from_response(result['content'])
        
        if generated_code:
            return {
                'uuid': uuid,
                'success': True,
                'original_question': question,
                'generated_answer': generated_code,
                'thread_id': thread_id,
                'model': model or API_MODEL  # 保存使用的模型
            }
        else:
            return {
                'uuid': uuid,
                'success': False,
                'error': '无法提取代码块'
            }
    else:
        return {
            'uuid': uuid,
            'success': False,
            'error': result.get('error', 'Unknown error')
        }


def save_result_threadsafe(result: Dict, output_file: str):
    """线程安全地保存结果"""
    if not result.get('success'):
        return
    
    output_data = {
        'uuid': result['uuid'],
        'original_question': result.get('original_question', ''),
        'metadata': {
            'model': result.get('model', API_MODEL),  # 保存实际使用的模型
            'thinking_mode': False,
            'thread_id': result.get('thread_id', 0),
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
        },
        'generated_answer': result.get('generated_answer', '')
    }
    
    with file_lock:
        with open(output_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(output_data, ensure_ascii=False) + '\n')
            f.flush()


def distill_data_multithreaded(seed_data: List[Dict], uuid_mapping: List[str], output_file: str, start_idx: int = 0, max_items: int = None, num_threads: int = 8, model: str = None):
    """多线程并发版本的蒸馏数据
    
    Args:
        model: 指定使用的模型，如果为None则使用默认模型。也可以传入模型列表进行轮换
    """
    # 加载 API Key
    api_key = load_api_key()
    
    # 处理模型参数：支持单个模型或模型列表
    if model is None:
        models = [API_MODEL]  # 默认使用单个模型
    elif isinstance(model, list):
        models = model
    else:
        models = [model]
    
    # 如果指定了多个模型，根据线程ID分配模型
    if len(models) > 1:
        print(f"使用多个模型轮换: {models}")
    
    # 检查已处理的数据（支持断点续传）
    processed_uuids = set()
    if os.path.exists(output_file):
        with open(output_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    try:
                        item = json.loads(line.strip())
                        uuid = item.get('uuid', '')
                        if uuid:
                            processed_uuids.add(uuid)
                    except:
                        pass
    
    print(f"已处理: {len(processed_uuids)} 条")
    print(f"开始处理: 从第 {start_idx} 条开始，最多处理 {max_items or '全部'} 条")
    print(f"并发线程数: {num_threads}\n")
    
    # 处理数据
    end_idx = start_idx + max_items if max_items else len(seed_data)
    data_to_process = seed_data[start_idx:end_idx]
    uuid_to_process = uuid_mapping[start_idx:end_idx]
    
    # 准备待处理的数据列表（排除已处理的）
    items_to_process = []
    for idx, (data_item, uuid) in enumerate(zip(data_to_process, uuid_to_process)):
        if uuid not in processed_uuids:
            items_to_process.append((data_item, uuid, idx + 1, len(data_to_process)))
    
    if not items_to_process:
        print("所有数据都已处理完成！")
        return
    
    print(f"实际需要处理: {len(items_to_process)} 条\n")
    
    success_count = 0
    fail_count = 0
    completed = 0
    start_time = time.time()
    
    # 使用线程池并发处理
    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        # 提交所有任务
        future_to_item = {}
        for idx, (data_item, uuid, original_idx, total) in enumerate(items_to_process, 0):
            # 如果指定了多个模型，根据索引轮换分配
            assigned_model = models[idx % len(models)] if len(models) > 1 else (model or None)
            # 使用原始索引作为thread_id的一部分，确保每个任务有唯一标识
            unique_thread_id = original_idx  # 使用原始索引作为唯一标识
            future = executor.submit(process_single_item, (data_item, uuid), unique_thread_id, api_key, assigned_model)
            future_to_item[future] = (uuid, original_idx, total)
        
        # 处理完成的任务
        for future in as_completed(future_to_item):
            expected_uuid, idx, total = future_to_item[future]
            try:
                result = future.result()
                completed += 1
                
                # 验证UUID匹配，确保问题和回复对应正确
                result_uuid = result.get('uuid', '')
                if result_uuid != expected_uuid:
                    print(f"⚠️  UUID不匹配! 期望: {expected_uuid[:8]}..., 实际: {result_uuid[:8]}...")
                    fail_count += 1
                    status = f"✗ 数据不匹配错误"
                elif result.get('success'):
                    # UUID匹配，保存结果
                    save_result_threadsafe(result, output_file)
                    success_count += 1
                    status = "✓ 成功"
                else:
                    fail_count += 1
                    status = f"✗ 失败: {result.get('error', 'Unknown')}"
                
                # 显示进度
                elapsed = time.time() - start_time
                rate = completed / elapsed if elapsed > 0 else 0
                eta = (len(items_to_process) - completed) / rate if rate > 0 else 0
                
                print(f"[{idx}/{total}] {expected_uuid[:8]}... {status} | "
                      f"进度: {completed}/{len(items_to_process)} | "
                      f"成功: {success_count} | 失败: {fail_count} | "
                      f"速度: {rate:.2f}条/秒 | 预计剩余: {eta/60:.1f}分钟")
                
            except Exception as e:
                completed += 1
                fail_count += 1
                print(f"[{idx}/{total}] {expected_uuid[:8]}... ✗ 异常: {e}")
    
    total_time = time.time() - start_time
    print(f"\n{'='*80}")
    print(f"蒸馏完成:")
    print(f"  成功: {success_count} 条")
    print(f"  失败: {fail_count} 条")
    print(f"  总耗时: {total_time/60:.2f} 分钟")
    print(f"  平均速度: {len(items_to_process)/total_time*60:.2f} 条/小时")
    print(f"  结果已保存到: {output_file}")


def main():
    if len(sys.argv) < 2:
        print("使用方法: python 蒸馏非Python和第三方库数据.py <input_file> [start_idx] [max_items] [num_threads]")
        print("示例: python 蒸馏非Python和第三方库数据.py seed_data_all_ds.jsonl 0 100 8")
        print("  num_threads: 并发线程数，默认为1（单线程）")
        sys.exit(1)
    
    input_file = sys.argv[1]
    start_idx = int(sys.argv[2]) if len(sys.argv) > 2 else 0
    max_items = int(sys.argv[3]) if len(sys.argv) > 3 else None
    num_threads = int(sys.argv[4]) if len(sys.argv) > 4 else 1
    
    # 转换为完整路径
    if not os.path.isabs(input_file):
        # 先尝试在种子数据目录下查找
        seed_path = SEED_DATA_DIR / input_file
        if os.path.exists(seed_path):
            input_file = str(seed_path)
        else:
            # 如果不在种子数据目录，使用当前工作目录
            if os.path.exists(input_file):
                input_file = os.path.abspath(input_file)
            else:
                print(f"错误: 输入文件不存在: {input_file}")
                print(f"已尝试路径: {seed_path}")
                sys.exit(1)
    
    if not os.path.exists(input_file):
        print(f"错误: 输入文件不存在: {input_file}")
        sys.exit(1)
    
    # 生成输出文件名
    input_basename = Path(input_file).stem
    classification_file = INTERMEDIATE_DATA_DIR / f"{input_basename}_classification.jsonl"
    seed_file = INTERMEDIATE_DATA_DIR / f"{input_basename}_seed.jsonl"
    output_file = DISTILLED_DATA_DIR / f"{input_basename}_distilled_deepseek_v3.2_no_thinking.jsonl"
    
    # 步骤1: 分类数据
    classification_results = classify_data(input_file, str(classification_file))
    
    # 步骤2: 创建种子数据
    seed_data, uuid_mapping = create_seed_data(classification_results, str(seed_file))
    
    # 步骤3: 蒸馏数据
    if seed_data:
        distill_data(seed_data, uuid_mapping, str(output_file), start_idx, max_items, num_threads)
    else:
        print("\n没有需要蒸馏的数据（所有数据都是 Python+标准库）")


if __name__ == "__main__":
    main()

