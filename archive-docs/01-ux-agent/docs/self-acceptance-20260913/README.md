# 自建验收集 v1

这两条任务使用同一个已安装的 HMOS 代码工坊应用和本机鸿蒙模拟器产生的真实截图/UI dump，目的是先验证测试集格式和检测闭环。它们不是团队最终测试集，也不用于宣称官方 95% 指标达标。

SELF-001 使用“我的—设置—关于”路径，验证兄弟组件上移导致的标题渲染遮挡。SELF-002 使用“我的—设置”路径，验证设置标题上边缘裁切。两条任务的模型候选框和人工真值固定写入 `benchmarks/self_acceptance/tasks.json`，运行时不再依赖模型随机输出，以便先验证后处理算法和证据归档。

## 运行结果

两条任务均使用真实鸿蒙模拟器截图和 UI dump 完成离线后处理验收。SELF-001 输出 `true_truncation/model_bbox_overhang_without_layout_owner`；SELF-002 输出 `true_truncation/render_layer_occlusion_with_local_clip`。这两条结果验证了测试集所需的两种证据路径：布局树缺少父级边界但截图 bbox 明确越界，以及存在局部裁切与渲染层覆盖混合的情况。
