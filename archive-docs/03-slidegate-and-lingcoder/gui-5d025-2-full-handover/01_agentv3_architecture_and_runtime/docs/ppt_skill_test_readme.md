# 输出地址
## 结果地址
/home/wangbo4/Workspace/Prjs/xhx_agent_v3/backend/database
统一以uid命名

## 日志地址
/home/wangbo4/Workspace/Prjs/xhx_agent_v3/logs/demo
按时间戳命名

# 可用工具
uv run scripts/capture_ppt_html_screenshots.py --root <target_dir>
用于渲染<target_dir>中以及所有子文件夹中的html，保存成同级的screenshot。

# 测试用例
## 无模板模式
uv run agents/agentv3/tests/manual_multi_turn_cli.py --config conf_v3_zh_claude.yaml --query "制作一 份2026世界杯参赛队伍介绍PPT，主要是要有世界杯相关的图片，总页数6页。"

## 模板模式
uv run agents/agentv3/tests/manual_multi_turn_cli.py --config conf_v3_zh_claude.yaml --query "制作一 份2026世界杯参赛队伍介绍PPT，要有世界杯相关的图片，用/mnt/data/skill/templates/dark-purple 这个模板，总页数4页，全程自动生成。"

# skill所在
/home/wangbo4/Workspace/Prjs/xhx_agent_v3/skills
