# 测试目录

按被验证的职责分类；文件名和测试方法保持可追溯，不把测试代码并入业务安装包。

|目录|验证范围|
|---|---|
|architecture|核心与外部实验的依赖边界、安装导入契约|
|source|SDK扫描、共享样式、插桩实例、工程复制和配置路径|
|planning|算子预检、基线选参、页面影响与组合冲突|
|mutation|源码模板、补丁和算子回归夹具|
|execution|构建、设备采集、回放、恢复、续跑和失败隔离|
|review|质量审核、重建、导出、版本关系与多批次统计|
|imaging|冻结真实截图上的前景测量回归|
|research|独立商业比较、历史对照与外部检测器的研究工具回归|
|fixtures|多个测试共享的数据原件|

在仓库根目录运行：

```powershell
python -m unittest discover -s tests -t . -q
python -m unittest discover -s tests/review -t . -q
```

`-t .`固定导入根目录，因此测试可明确使用`tests.planning`等包路径，避免依赖平铺目录中的隐式导入。部分SDK测试读取`profiles/apps/ohbill.json`；对应真实源码和SDK需在本机可用。设备流程多数采用离线夹具，实际模拟器验证另有运行记录，二者分别统计。

## 构建后的回归要求

每次HAP构建或Python安装包构建后，运行完整测试命令`python -m unittest discover -s tests -t . -q`，保留对应构建与测试日志。上面的单目录命令用于定位问题，不能代替完整回归。失败应记录并修复后复测。

修改算子、选参、布局或采集行为时，还要对照受影响的历史案例：检查生成补丁、截图、UI树、内容身份和恢复结果。此次构建成功与完整测试通过分别记录；实际注入效果由运行证据核实。已有示例见[两例滚动修复记录](../docs/verification/scroll-fix.md)。
