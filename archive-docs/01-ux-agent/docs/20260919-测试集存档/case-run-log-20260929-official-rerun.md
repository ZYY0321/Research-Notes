# 2026-09-29 官方校园网 detect 复测 run-log

说明：本轮只记录走校园网官方接口的有效端到端运行。有效输出目录必须包含 `model_http.json`，且 `snapshot_ux.json` 的 `apiConfig.baseURL` 必须为 `http://10.176.44.15:8000/detect`。

## 三折叠

### trifold_xml_normal_jd_g01_s1

- 数据集：`D:\projects\UX-Agent-rerun-5eafc4b\test-set\测试集0928\trifold_xml_normal\jd\g01\trifold_xml_normal_jd_g01_s1.jpg`，同名 json、xml。GT 为京东单屏普通样例，json 标注 1 个「截断-图标」。
- 设备 / 屏态：Mate XTs `29L0124226000058`，单屏模式；运行前截图为京东首页，和 GT 页面结构一致，商品内容有动态差异。
- 官方接口确认：`snapshot_ux.json` 里 `apiConfig.baseURL=http://10.176.44.15:8000/detect`，`apiConfig.model=campus-http-detect`；输出目录包含 `model_http.json`。
- 模型原文：`image_path=/tmp/ux_upload_ocs8gvlv.png`，`total_inference_sec=12.2049`，`parse_status=valid_root_json`，`inference_error=null`。`pred_text` 是 `{"overall":"bad","issues":[{"issue_type":"截断-文字","bbox":[123,891,455,902],"truncated_edges":["bottom"]},{"issue_type":"截断-文字","bbox":[869,158,907,176],"truncated_edges":["right"]},{"issue_type":"截断-文字","bbox":[927,243,1000,258],"truncated_edges":["right"]},{"issue_type":"截断-图标","bbox":[941,201,1000,241],"truncated_edges":["right"]}]}`。
- layout / 滑动：模型 4 框；layout 4 个均为 `unknown / unsupported_or_unmatched_issue`；滑动核对 4 框均为 `scrollable` 并被消解。最终页级 **ok**，`issues=0`。
- 算法秒数：`algorithmMs=23458`，约 **23.458s**；总耗时 `elapsedMs=36774`。超过预算：`algorithmOverBudget=true`，预算 `algorithmMs=7000`。
- 哪一段：模型阶段多报候选框；layout 未能确认，交给滑动；滑动阶段将候选框全部消解，最终结果与 normal 样例预期一致。
- 什么情况：模型在顶部/右侧/中部识别出 4 个疑似截断框，其中包含 1 个「截断-图标」；端到端滑动分别执行 `up` 和 `left`，对应 diff 为 `34.81`、`30.62`、`14.26`、`22.15`，均判断可滑动消解。
- 改进方向：当前准确性可接受，但耗时明显超预算；后续可优化滑动核对次数或 grouping/提前终止策略。
- 证据：
  - 输出目录：`D:\projects\UX-Agent-rerun-5eafc4b\HarmonyArena-fdu_agent\ux-detect-output\testset_0928\trifold_xml_normal\jd\g01\20260929-222213-217`
  - 现场：`...\snapshot.png`
  - 模型原始返回：`...\model_http.json`
  - 模型框：`...\model_result.json`、`...\snapshot_bbox.png`
  - dump：`...\snapshot_window.json`、`...\snapshot_ui-tree.txt`
  - layout：`...\layout_result.json`
  - 滑动：`...\slide_result.json`、`...\slide-ops.jsonl`
  - 滑后图：`...\snapshot_slide_up_0.png`、`...\snapshot_slide_left_1.png`、`...\snapshot_slide_left_2.png`
  - 恢复图：`...\snapshot_slide_up_0.png.restore.png`、`...\snapshot_slide_left_1.png.restore.png`、`...\snapshot_slide_left_2.png.restore.png`
  - 总结果：`...\snapshot_ux.json`
- 状态：**有效运行。官方校园网模型返回 4 框，端到端滑动全部消解，最终页级 ok；需记录超时。**

### trifold_xml_normal_jd_g01_s2

- 数据集：`D:\projects\UX-Agent-rerun-5eafc4b\test-set\测试集0928\trifold_xml_normal\jd\g01\trifold_xml_normal_jd_g01_s2.jpg`，同名 json、xml。GT 为京东双屏普通样例，json 标注 3 框：`截断-文字`、`截断-图标`、`截断-文字`，均为右切。
- 设备 / 屏态：Mate XTs `29L0124226000058`，双屏宽画幅截图，坐标空间 `2048x2232`。运行前截图为京东首页，整体结构与 GT 一致，但右侧频道/入口动态内容与 GT 有差异。
- 官方接口确认：`snapshot_ux.json` 里 `apiConfig.baseURL=http://10.176.44.15:8000/detect`，`apiConfig.model=campus-http-detect`；输出目录包含 `model_http.json`。
- 模型原文：`image_path=/tmp/ux_upload_glx_ofka.png`，`total_inference_sec=8.2323`，`parse_status=valid_root_json`，`inference_error=null`。`pred_text` 是 `{"overall":"bad","issues":[{"issue_type":"截断-文字","bbox":[964,260,1000,277],"truncated_edges":["right"]},{"issue_type":"截断-图标","bbox":[976,210,1000,258],"truncated_edges":["right"]}]}`。
- layout / 滑动：模型 2 框；layout 2 个均为 `unknown / unsupported_or_unmatched_issue`；滑动核对 2 框均为 `scrollable` 并被消解。最终页级 **ok**，`issues=0`。
- 算法秒数：`algorithmMs=9951`，约 **9.951s**；总耗时 `elapsedMs=19845`。超过预算：`algorithmOverBudget=true`，预算 `algorithmMs=7000`。
- 哪一段：模型阶段与 GT 框数不完全一致；GT 3 框，当前现场模型仅命中右边缘 2 框。layout 未能确认，滑动阶段全部消解。
- 什么情况：当前现场最右侧内容与 GT 不同，GT 顶部右切文字框对应位置没有完全复现；更具体地看，导航栏右侧露出的「美妆/类似频道项」区域太少，字符主体不够明确，模型可能按“无法确认具体字符被切掉”没有标框。模型命中的两个右切框位于右侧入口区域，左滑后 diff 分别为 `10.4`、`29.08`，均判为可滑动消解。最终结果符合 normal 样例页级预期，但候选框数为 **2/3**，需要注明页面动态差异/疑似少一候选。
- 改进方向：若后续要求严格对齐 GT 框数，需要重新调到更接近 GT 的频道位置或固定内容；算法侧可关注右边缘文字框漏检。
- 证据：
  - 输出目录：`D:\projects\UX-Agent-rerun-5eafc4b\HarmonyArena-fdu_agent\ux-detect-output\testset_0928\trifold_xml_normal\jd\g01\20260929-222527-916`
  - 现场：`...\snapshot.png`
  - 模型原始返回：`...\model_http.json`
  - 模型框：`...\model_result.json`、`...\snapshot_bbox.png`
  - dump：`...\snapshot_window.json`、`...\snapshot_ui-tree.txt`
  - layout：`...\layout_result.json`
  - 滑动：`...\slide_result.json`、`...\slide-ops.jsonl`
  - 滑后图：`...\snapshot_slide_left_0.png`
  - 恢复图：`...\snapshot_slide_left_0.png.restore.png`
  - 总结果：`...\snapshot_ux.json`
- 状态：**有效运行，但当前现场与 GT 框数不完全一致。官方校园网模型返回 2 框，端到端滑动全部消解，最终页级 ok；需记录超时和 2/3 框差异。**

## 宽折叠

### widefold_xml_normal_taobao_g01_s1

- 数据集：`D:\projects\UX-Agent-rerun-5eafc4b\test-set\测试集0928\widefold_xml_normal\taobao\g01\widefold_xml_normal_taobao_g01_s1.jpg`，同名 json、xml。GT 为淘宝「我的淘宝」普通样例，json 标注 5 框：3 个 `截断-文字` 上切、1 个 `截断-文字` 右切、1 个 `截断-组件` 右切。
- 设备 / 屏态：Pura X `6HQ0125A11000475`，外屏/单屏画幅；现场截图为淘宝「我的淘宝」页，账号、订单、快递/收藏/关注店铺/足迹等结构与 GT 一致，但当前屏幕效果/页面动态内容已经无法完全复现 GT，底部动态内容与 GT 有差异。
- 官方接口确认：`snapshot_ux.json` 里 `apiConfig.baseURL=http://10.176.44.15:8000/detect`，`apiConfig.model=campus-http-detect`；输出目录包含 `model_http.json`。
- 模型原文：`image_path=/tmp/ux_upload_lysn5e1x.png`，`total_inference_sec=19.6312`，`parse_status=valid_root_json`，`inference_error=null`。`pred_text` 是 `{"overall":"bad","issues":[{"issue_type":"截断-文字","bbox":[902,129,929,161],"truncated_edges":["right"]},{"issue_type":"截断-图标","bbox":[65,855,162,886],"truncated_edges":["bottom"]},{"issue_type":"截断-图标","bbox":[219,855,316,886],"truncated_edges":["bottom"]},{"issue_type":"截断-图标","bbox":[373,855,470,886],"truncated_edges":["bottom"]},{"issue_type":"截断-图标","bbox":[527,855,624,886],"truncated_edges":["bottom"]},{"issue_type":"截断-图标","bbox":[684,855,781,886],"truncated_edges":["bottom"]},{"issue_type":"截断-图标","bbox":[836,855,933,886],"truncated_edges":["bottom"]}]}`。
- layout / 滑动：模型 7 框；layout 7 个均为 `unknown / unsupported_or_unmatched_issue`。滑动阶段第 0 框左滑 `diffPercent=0`，判为 `confirmed`；其余 6 个底部图标框上滑后为 `restore_failed`，最终留下 7 框，页级 **unknown**。
- 算法秒数：`algorithmMs=13186`，约 **13.186s**；总耗时 `elapsedMs=33378`。超过预算：`algorithmOverBudget=true`，预算 `algorithmMs=7000`。
- 哪一段：模型 / 滑动。模型框数和类型与 GT 不一致，GT 5 框，实际 7 框；滑动阶段没有把 normal 样例的候选框消解，且出现恢复失败。
- 什么情况：现场页面结构与 GT 同类，但屏幕效果和页面动态内容与采集 GT 时不完全一致，无法严格复现 GT 的 5 框现场；当前底部多露出一排圆形入口，模型把 6 个底部入口图标报为 `截断-图标/bottom`，同时没有命中 GT 里 3 个顶部上切文字和右侧组件的组合。第 0 个右切文字框左滑无变化被确认，其余 6 框上滑后恢复失败，导致 normal 样例最终不是 ok。
- 改进方向：模型侧需减少底部露出图标的误报，并更贴近 GT 的顶部上切文字/右侧组件框；滑动侧需要处理恢复失败，避免 normal 可滑场景残留为 unknown。
- 证据：
  - 输出目录：`D:\projects\UX-Agent-rerun-5eafc4b\HarmonyArena-fdu_agent\ux-detect-output\testset_0928\widefold_xml_normal\taobao\g01\20260929-224520-665`
  - 现场：`...\snapshot.png`
  - 模型原始返回：`...\model_http.json`
  - 模型框：`...\model_result.json`、`...\snapshot_bbox.png`
  - 最终框：`...\snapshot_bbox_final.png`
  - dump：`...\snapshot_window.json`、`...\snapshot_ui-tree.txt`
  - layout：`...\layout_result.json`
  - 滑动：`...\slide_result.json`、`...\slide-ops.jsonl`
  - 滑后图：`...\snapshot_slide_left_0.png`、`...\snapshot_slide_up_1.png`
  - 恢复图：`...\snapshot_slide_up_1.png.restore.png`
  - 总结果：`...\snapshot_ux.json`
- 状态：**有效运行，但因当前屏幕效果/页面动态无法完全复现 GT，结果只能按差异现场记录。官方校园网模型返回 7 框，和 GT 5 框不一致；端到端最终页级 unknown，需记录超时、误报和恢复失败。**

### widefold_xml_normal_vipshop_g01_s2

- 数据集：`D:\projects\UX-Agent-rerun-5eafc4b\test-set\测试集0928\widefold_xml_normal\vipshop\g01\widefold_xml_normal_vipshop_g01_s2.jpg`，同名 json、xml。GT 为唯品会内屏普通样例，json 标注 1 个 `截断-文字` 右切。
- 设备 / 屏态：Pura X `6HQ0125A11000475`，内屏画幅，坐标空间 `2584x1828`。现场截图左侧为唯品会首页，右侧为搜索/推荐标签面板，结构与 GT 一致；搜索词和商品/推荐词有动态差异。
- 官方接口确认：`snapshot_ux.json` 里 `apiConfig.baseURL=http://10.176.44.15:8000/detect`，`apiConfig.model=campus-http-detect`；输出目录包含 `model_http.json`。
- 模型原文：`image_path=/tmp/ux_upload_yr6siyd7.png`，`total_inference_sec=5.4567`，`parse_status=valid_root_json`，`inference_error=null`。`pred_text` 是 `{"overall":"bad","issues":[{"issue_type":"截断-文字","bbox":[449,223,456,247],"truncated_edges":["right"]}]}`。
- layout / 滑动：模型 1 框；layout 为 `unknown / unsupported_or_unmatched_issue`；滑动核对左滑，`diffPercent=39.06`，判为 `scrollable` 并消解。最终页级 **ok**，`issues=0`。
- 算法秒数：`algorithmMs=8994`，约 **8.994s**；总耗时 `elapsedMs=15736`。超过预算：`algorithmOverBudget=true`，预算 `algorithmMs=7000`。
- 哪一段：模型命中数量和类型与 GT 一致；layout 未能确认，滑动阶段正确消解。
- 什么情况：GT 1 个右切文字框，现场模型也返回 1 个右切文字框；左滑后页面变化明显，框被判可滑动消解，因此 normal 样例最终为 ok。页面动态内容不同但不影响结构和测试结论。
- 改进方向：准确性通过；后续主要优化耗时，模型推理和滑动总耗时均超过预算。
- 证据：
  - 输出目录：`D:\projects\UX-Agent-rerun-5eafc4b\HarmonyArena-fdu_agent\ux-detect-output\testset_0928\widefold_xml_normal\vipshop\g01\20260929-225218-824`
  - 现场：`...\snapshot.png`
  - 模型原始返回：`...\model_http.json`
  - 模型框：`...\model_result.json`、`...\snapshot_bbox.png`
  - dump：`...\snapshot_window.json`、`...\snapshot_ui-tree.txt`
  - layout：`...\layout_result.json`
  - 滑动：`...\slide_result.json`、`...\slide-ops.jsonl`
  - 滑后图：`...\snapshot_slide_left_0.png`
  - 总结果：`...\snapshot_ux.json`
- 状态：**有效运行，通过。官方校园网模型返回 1 框，与 GT 数量/类型一致；端到端滑动消解后最终页级 ok；需记录超时。**

## 直屏

### phone_xml_normal_tencentnews_g01_s1

- 数据集：`D:\projects\UX-Agent-rerun-5eafc4b\测试集\整理\phone_xml_normal\tencentnews\g01\phone_xml_normal_tencentnews_g01_s1.jpg`，同名 json、xml。GT 为腾讯新闻直屏普通样例，json 标注 3 框：2 个 `截断-文字` 右切、1 个 `截断-图标` 右切。
- 设备 / 屏态：Mate 60 Pro `LNG0123525000430`，直屏单屏；运行前截图为腾讯新闻「要闻」流，右侧露出下一张横向卡片，页面结构与 GT 同类，搜索词和新闻内容有动态差异。
- 官方接口确认：`snapshot_ux.json` 里 `apiConfig.baseURL=http://10.176.44.15:8000/detect`，`apiConfig.model=campus-http-detect`；输出目录包含 `model_http.json`。
- 模型原文：`image_path=/tmp/ux_upload_jw_vv1ma.png`，`total_inference_sec=22.5269`，`parse_status=valid_root_json`，`inference_error=null`。`pred_text` 是 `{"overall":"bad","issues":[{"issue_type":"截断-文字","bbox":[959,516,1000,595],"truncated_edges":["right"]},{"issue_type":"截断-文字","bbox":[965,393,1000,411],"truncated_edges":["right"]}]}`。
- layout / 滑动：模型 2 框；layout 2 个均为 `unknown / unsupported_or_unmatched_issue`；滑动核对将 2 框作为同一 group 左滑，均判为 `scrollable` 并消解。最终页级 **ok**，`issues=0`。
- 算法秒数：`algorithmMs=9159`，约 **9.159s**；总耗时 `elapsedMs=49748`。超过预算：`algorithmOverBudget=true`，预算 `algorithmMs=7000`。其中官方模型 `modelMs=40589`，明显超出模型预算。
- 哪一段：模型阶段与 GT 框数不完全一致；GT 3 框，当前现场模型仅返回 2 个右切文字框，未返回 GT 中的右切图标框。layout 未能确认，滑动阶段将候选框全部消解。
- 什么情况：右侧露出的下一张新闻卡片与 GT 同类，但当前内容动态不同；模型命中的两个右切文字框落在右侧露出的卡片文字上，左滑后被判为可滑动消解。第二框在 group 内 `diffPercent=0`，但同组第一个框 `diffPercent=28.24`，因此 group 作为整体被消解。最终结果符合 normal 样例页级预期，但候选框数为 **2/3**，需要注明少了一个图标候选。
- 改进方向：若后续要求严格对齐 GT 框数，需要关注右侧露出卡片里的小图标/功能图形漏检；同时官方模型推理耗时 22.5s、总耗时 49.7s，需记录超时。
- 证据：
  - 输出目录：`D:\projects\UX-Agent-rerun-5eafc4b\HarmonyArena-fdu_agent\ux-detect-output\testset_0928\phone_xml_normal\tencentnews\g01\20260929-233400-309`
  - 现场：`...\snapshot.png`
  - 模型原始返回：`...\model_http.json`
  - 模型框：`...\model_result.json`、`...\snapshot_bbox.png`
  - dump：`...\snapshot_window.json`、`...\snapshot_ui-tree.txt`
  - layout：`...\layout_result.json`
  - 滑动：`...\slide_result.json`、`...\slide-ops.jsonl`
  - 滑后图：`...\snapshot_slide_left_0.png`
  - 恢复图：`...\snapshot_slide_left_0.png.restore.png`
  - 总结果：`...\snapshot_ux.json`
- 状态：**有效运行，通过。官方校园网模型返回 2 框，与 GT 3 框不完全一致；端到端滑动全部消解，最终页级 ok；需记录超时和 2/3 框差异。**

### widefold_xml_normal_xianyu_g01_s1

- 数据集：`D:\projects\UX-Agent-rerun-5eafc4b\test-set\测试集0928\widefold_xml_normal\xianyu\g01\widefold_xml_normal_xianyu_g01_s1.jpg`，同名 json、xml。GT 为闲鱼外屏普通样例，json 标注 3 框：2 个 `截断-文字` 右切、1 个 `截断-图标` 右切。
- 设备 / 屏态：Pura X `6HQ0125A11000475`，外屏/单屏画幅，坐标空间 `1264x1848`。现场截图为闲鱼推荐页，顶部搜索、频道栏、服务入口、商品流结构与 GT 同类；GT 中有登录提示黑条，当前现场没有，商品和搜索词也有动态差异。
- 官方接口确认：`snapshot_ux.json` 里 `apiConfig.baseURL=http://10.176.44.15:8000/detect`，`apiConfig.model=campus-http-detect`；输出目录包含 `model_http.json`。
- 模型原文：`image_path=/tmp/ux_upload_q97zypt2.png`，`total_inference_sec=9.8587`，`parse_status=valid_root_json`，`inference_error=null`。`pred_text` 是 `{"overall":"bad","issues":[{"issue_type":"截断-文字","bbox":[893,134,932,158],"truncated_edges":["right"]},{"issue_type":"截断-文字","bbox":[974,278,1000,298],"truncated_edges":["right"]},{"issue_type":"截断-图标","bbox":[985,214,1000,259],"truncated_edges":["right"]}]}`。
- layout / 滑动：模型 3 框，与 GT 数量/类型一致；layout 3 个均为 `unknown / unsupported_or_unmatched_issue`。滑动阶段第 1、2 框左滑后分别以 `diffPercent=26.44`、`40.34` 判为 `scrollable` 并消解；第 0 框左滑 `diffPercent=0`，判为 `confirmed` 并留下。最终页级 **bad**，剩余 1 框。
- 算法秒数：`algorithmMs=9866`，约 **9.866s**；总耗时 `elapsedMs=20570`。超过预算：`algorithmOverBudget=true`，预算 `algorithmMs=7000`。
- 哪一段：滑动。模型候选框数量和类型对齐 GT，但顶部频道右侧「手…」框没有通过横滑消解。
- 什么情况：当前现场和 GT 因登录提示/商品/搜索词存在动态差异，但顶部频道右切、服务入口右切属于同类位置。服务入口两个框可以横滑消解；顶部频道右侧「手…」框执行左滑后页面像素差为 0，被流程判成真截断，导致 normal 样例最终 bad。
- 改进方向：顶部横向频道栏的滑动落点或可滑容器识别需要改进，避免只滑到不可动区域导致 `diffPercent=0`；同时可用布局树识别频道栏横向 scroll 容器。
- 证据：
  - 输出目录：`D:\projects\UX-Agent-rerun-5eafc4b\HarmonyArena-fdu_agent\ux-detect-output\testset_0928\widefold_xml_normal\xianyu\g01\20260929-225710-084`
  - 现场：`...\snapshot.png`
  - 模型原始返回：`...\model_http.json`
  - 模型框：`...\model_result.json`、`...\snapshot_bbox.png`
  - 最终框：`...\snapshot_bbox_final.png`
  - dump：`...\snapshot_window.json`、`...\snapshot_ui-tree.txt`
  - layout：`...\layout_result.json`
  - 滑动：`...\slide_result.json`、`...\slide-ops.jsonl`
  - 滑后图：`...\snapshot_slide_left_0.png`、`...\snapshot_slide_left_1.png`
  - 恢复图：`...\snapshot_slide_left_1.png.restore.png`
  - 总结果：`...\snapshot_ux.json`
- 状态：**有效运行，但算法未通过。官方校园网模型返回 3 框，与 GT 数量/类型一致；端到端只消解 2/3，顶部频道右切文字框被确认并保留，最终页级 bad；需记录超时。**

### widefold_xml_normal_xianyu_g01_s2

- 数据集：`D:\projects\UX-Agent-rerun-5eafc4b\test-set\测试集0928\widefold_xml_normal\xianyu\g01\widefold_xml_normal_xianyu_g01_s2.jpg`，同名 json、xml。GT 为闲鱼内屏普通样例，json 标注 1 个 `截断-文字` 右切。
- 设备 / 屏态：Pura X `6HQ0125A11000475`，内屏画幅，坐标空间 `2584x1828`。现场截图为闲鱼内屏三列商品流，顶部搜索、频道栏、服务入口结构与 GT 同类；GT 中有登录提示黑条，当前现场没有，商品和搜索词有动态差异。
- 官方接口确认：`snapshot_ux.json` 里 `apiConfig.baseURL=http://10.176.44.15:8000/detect`，`apiConfig.model=campus-http-detect`；输出目录包含 `model_http.json`。
- 模型原文：`image_path=/tmp/ux_upload_bfmda4s1.png`，`total_inference_sec=5.5544`，`parse_status=valid_root_json`，`inference_error=null`。`pred_text` 是 `{"overall":"bad","issues":[{"issue_type":"截断-文字","bbox":[928,136,962,160],"truncated_edges":["right"]}]}`。
- layout / 滑动：模型 1 框；layout 为 `unknown / unsupported_or_unmatched_issue`；滑动核对左滑，`diffPercent=21.47`，判为 `scrollable` 并消解。最终页级 **ok**，`issues=0`。
- 算法秒数：`algorithmMs=11324`，约 **11.324s**；总耗时 `elapsedMs=19304`。超过预算：`algorithmOverBudget=true`，预算 `algorithmMs=7000`。
- 哪一段：模型命中数量和类型与 GT 一致；layout 未能确认，滑动阶段正确消解。
- 什么情况：GT 1 个顶部频道右切文字框，现场模型也返回 1 个右切文字框；左滑后页面变化明显，框被判可滑动消解，因此 normal 样例最终为 ok。登录提示黑条未复现，但不影响这个顶部频道框的测试结论。
- 改进方向：准确性通过；后续主要优化耗时，尤其是滑动阶段 `slideMs=9124`。
- 证据：
  - 输出目录：`D:\projects\UX-Agent-rerun-5eafc4b\HarmonyArena-fdu_agent\ux-detect-output\testset_0928\widefold_xml_normal\xianyu\g01\20260929-230222-311`
  - 现场：`...\snapshot.png`
  - 模型原始返回：`...\model_http.json`
  - 模型框：`...\model_result.json`、`...\snapshot_bbox.png`
  - dump：`...\snapshot_window.json`、`...\snapshot_ui-tree.txt`
  - layout：`...\layout_result.json`
  - 滑动：`...\slide_result.json`、`...\slide-ops.jsonl`
  - 滑后图：`...\snapshot_slide_left_0.png`
  - 恢复图：`...\snapshot_slide_left_0.png.restore.png`
  - 总结果：`...\snapshot_ux.json`
- 状态：**有效运行，通过。官方校园网模型返回 1 框，与 GT 数量/类型一致；端到端滑动消解后最终页级 ok；需记录超时。**
