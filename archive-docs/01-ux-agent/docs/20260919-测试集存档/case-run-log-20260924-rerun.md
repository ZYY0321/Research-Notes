# 2026-09-24 重新测试 run-log

### WF-滴滴-G01-S2
- 设备：阔折 Pura X `6HQ0125A11000475`，内屏 `2584×1828`。未用 hidumper。
- GT：测试集/整理/widefold_xml_normal/didi/g01/widefold_xml_normal_didi_g01_s2.jpg
- 现场图：HarmonyArena-fdu_agent/ux-detect-output/20260924-191720-480/snapshot.png
- 页级：ok
- 人眼：滴滴首页/出行服务页，与 GT 同类；文件夹 widefold_xml_normal 判定为非截断样本，模型未报截断，符合预期。
- 算法秒数：5.806s
- 证据：HarmonyArena-fdu_agent/ux-detect-output/20260924-191720-480/snapshot_ux.json；HarmonyArena-fdu_agent/ux-detect-output/20260924-191720-480/snapshot_window.json
- 状态：**模型未出框，页级 ok。**

### WF-抖音-G01-S2
- 设备：阔折 Pura X `6HQ0125A11000475`，内屏 `2584×1828`。未用 hidumper。
- GT：测试集/整理/widefold_xml_normal/douyin/g01/widefold_xml_normal_douyin_g01_s2.jpg
- 现场图：HarmonyArena-fdu_agent/ux-detect-output/20260924-192056-353/snapshot.png
- 页级：ok
- 人眼：抖音消息页，与 GT 同类；文件夹 widefold_xml_normal 判定为非截断样本，现场页面未见文字/组件/图标截断。
- 算法秒数：5.913s
- 模型/layout/slide：模型阶段成功返回 overall=ok、issues=[]，未识别出截断候选框；layout 空输入成功；slide 因无候选框跳过，符合非截断样本预期。
- 证据：HarmonyArena-fdu_agent/ux-detect-output/20260924-192056-353/snapshot_ux.json；HarmonyArena-fdu_agent/ux-detect-output/20260924-192056-353/snapshot_window.json
- 状态：**模型未出框，页级 ok。**

### WF-淘宝-G01-S2
- 设备：阔折 Pura X `6HQ0125A11000475`，内屏 `2584×1828`。未用 hidumper。
- GT：测试集/整理/widefold_xml_normal/taobao/g01/widefold_xml_normal_taobao_g01_s2.jpg
- 现场图：HarmonyArena-fdu_agent/ux-detect-output/20260924-192243-894/snapshot.png
- 页级：ok
- 人眼：淘宝“我的淘宝”页，与 GT 同类；文件夹 widefold_xml_normal 判定为非截断样本，现场页面优惠券横栏、订单区和底部导航未见文字/组件/图标截断。
- 算法秒数：5.852s
- 模型/layout/slide：模型阶段成功返回 overall=ok、issues=[]，未识别出截断候选框；layout 空输入成功；slide 因无候选框跳过，符合非截断样本预期。
- 证据：HarmonyArena-fdu_agent/ux-detect-output/20260924-192243-894/snapshot_ux.json；HarmonyArena-fdu_agent/ux-detect-output/20260924-192243-894/snapshot_window.json
- 状态：**模型未出框，页级 ok。**

### WF-唯品会-G01-S2
- 设备：阔折 Pura X `6HQ0125A11000475`，内屏 `2584×1828`。未用 hidumper。
- GT：测试集/整理/widefold_xml_normal/vipshop/g01/widefold_xml_normal_vipshop_g01_s2.jpg
- 现场图：HarmonyArena-fdu_agent/ux-detect-output/20260924-192430-232/snapshot.png
- 页级：ok
- 人眼：Pura X 内屏大屏，唯品会左侧首页/频道栏、右侧搜索建议页，与 GT 属于同类分屏状态；但现场搜索词、频道项和商品流与 GT 不完全一致，因此频道栏边缘出现模型候选框可以作为现场差异记录，不直接判为 GT 对齐问题。
- 算法秒数：16.477s
- 超时/预算：totalMs=16477，modelMs=7388，slideMs=6655，algorithmMs=9089，algorithmOverBudget=true；页级虽然 ok，但超过 10s 总预算和 7s algorithm 预算，性能需单独关注。
- 模型/layout/slide：模型阶段识别到 1 个候选框，位于左侧顶部频道栏最右侧，raw 为 overall=bad、截断-文字、right；layout 未能直接坐实或消解，结果为 unknown/unsupported_or_unmatched_issue；slide 对该组执行 left 滑动，判定 scrollable，diffPercent=23.06，将候选框移除，最终页级 ok。该结果符合“可横向滑动消解，不算缺陷”的预期。
- 证据：HarmonyArena-fdu_agent/ux-detect-output/20260924-192430-232/snapshot_ux.json；HarmonyArena-fdu_agent/ux-detect-output/20260924-192430-232/snapshot_bbox.png；HarmonyArena-fdu_agent/ux-detect-output/20260924-192430-232/snapshot_slide_left_0.png；HarmonyArena-fdu_agent/ux-detect-output/20260924-192430-232/snapshot_slide_left_0.png.restore.png；HarmonyArena-fdu_agent/ux-detect-output/20260924-192430-232/slide-ops.jsonl；HarmonyArena-fdu_agent/ux-detect-output/20260924-192430-232/snapshot_window.json
- 状态：**一框消掉，页级 ok；页面有回滑恢复证据。**

### WF-闲鱼-G01-S2
- 设备：阔折 Pura X `6HQ0125A11000475`，内屏 `2584×1828`。未用 hidumper。
- GT：测试集/整理/widefold_xml_normal/xianyu/g01/widefold_xml_normal_xianyu_g01_s2.jpg
- 现场图：HarmonyArena-fdu_agent/ux-detect-output/20260924-192657-137/snapshot.png
- 页级：ok
- 人眼：Pura X 内屏大屏，闲鱼首页推荐流，与 GT 同类；现场搜索词和商品流与 GT 不完全一致，但顶部搜索框、频道栏、商品卡片流和底部导航结构一致。模型候选框位于顶部横向频道栏最右侧“包表”附近，属于可横向滚动频道末端边界。
- 算法秒数：17.467s
- 超时/预算：totalMs=17467，modelMs=8235，slideMs=6761，algorithmMs=9232，algorithmOverBudget=true；页级虽然 ok，但超过 10s 总预算和 7s algorithm 预算，性能需单独关注。
- 模型/layout/slide：模型阶段识别到 1 个候选框，raw 为 overall=bad、截断-文字、right；layout 未能直接坐实或消解，结果为 unknown/unsupported_or_unmatched_issue；slide 对该组执行 left 滑动，判定 scrollable，diffPercent=20.32，将候选框移除，最终页级 ok。该结果符合“横向频道可滑动消解，不算缺陷”的预期。
- 证据：HarmonyArena-fdu_agent/ux-detect-output/20260924-192657-137/snapshot_ux.json；HarmonyArena-fdu_agent/ux-detect-output/20260924-192657-137/snapshot_bbox.png；HarmonyArena-fdu_agent/ux-detect-output/20260924-192657-137/snapshot_slide_left_0.png；HarmonyArena-fdu_agent/ux-detect-output/20260924-192657-137/snapshot_slide_left_0.png.restore.png；HarmonyArena-fdu_agent/ux-detect-output/20260924-192657-137/slide-ops.jsonl；HarmonyArena-fdu_agent/ux-detect-output/20260924-192657-137/snapshot_window.json
- 状态：**一框消掉，页级 ok；页面有回滑恢复证据。**

### WF-滴滴-G01-S1
- 设备：阔折 Pura X `6HQ0125A11000475`，外屏 `1264×1848`。按用户要求用 `hidumper -s 4607 -a -p` 切到外屏。
- GT：测试集/整理/widefold_xml_normal/didi/g01/widefold_xml_normal_didi_g01_s1.jpg
- 现场图：HarmonyArena-fdu_agent/ux-detect-output/20260924-194715-839/snapshot.png
- 页级：ok
- 人眼：外屏滴滴“日常出行”服务列表页，与 GT 同类；文件夹 widefold_xml_normal 判定为非截断样本，现场未见文字/组件/图标截断。
- 算法秒数：4.627s
- 模型/layout/slide：模型阶段成功返回 overall=ok、issues=[]，未识别出截断候选框；layout 空输入成功；slide 因无候选框跳过，符合非截断样本预期。
- 证据：HarmonyArena-fdu_agent/ux-detect-output/20260924-194715-839/snapshot_ux.json；HarmonyArena-fdu_agent/ux-detect-output/20260924-194715-839/snapshot_window.json
- 状态：**模型未出框，页级 ok。**

### WF-抖音-G01-S1
- 设备：阔折 Pura X `6HQ0125A11000475`，外屏 `1264×1848`。按用户要求用 `hidumper -s 4607 -a -p` 切到外屏。
- GT：测试集/整理/widefold_xml_normal/douyin/g01/widefold_xml_normal_douyin_g01_s1.jpg
- 现场图：HarmonyArena-fdu_agent/ux-detect-output/20260924-194821-346/snapshot.png
- 页级：ok
- 人眼：外屏抖音消息页，与 GT 同类；文件夹 widefold_xml_normal 判定为非截断样本，现场未见文字/组件/图标截断。
- 算法秒数：4.418s
- 模型/layout/slide：模型阶段成功返回 overall=ok、issues=[]，未识别出截断候选框；layout 空输入成功；slide 因无候选框跳过，符合非截断样本预期。
- 证据：HarmonyArena-fdu_agent/ux-detect-output/20260924-194821-346/snapshot_ux.json；HarmonyArena-fdu_agent/ux-detect-output/20260924-194821-346/snapshot_window.json
- 状态：**模型未出框，页级 ok。**

### WF-淘宝-G01-S1
- 设备：阔折 Pura X `6HQ0125A11000475`，外屏 `1264×1848`。按用户要求用 `hidumper -s 4607 -a -p` 切到外屏。
- GT：测试集/整理/widefold_xml_normal/taobao/g01/widefold_xml_normal_taobao_g01_s1.jpg
- 现场图：HarmonyArena-fdu_agent/ux-detect-output/20260924-195610-843/snapshot.png
- 页级：ok
- 人眼：外屏淘宝“我的淘宝”页，与 GT 很接近；顶部权益/资产区被上缘切到，下面有“我的订单”“快递/收藏/关注店铺/足迹”，领券中心右侧也露出半张券。文件夹 widefold_xml_normal 判定为非截断样本，现场这些候选属于可滚动/可滑动内容边界。
- 算法秒数：39.186s
- 超时/预算：totalMs=39186，modelMs=26158，slideMs=10850，algorithmMs=13028，algorithmOverBudget=true；页级虽然 ok，但模型与滑动耗时都明显超预算，性能需单独关注。
- 模型/layout/slide：模型阶段识别到 9 个候选框，raw 为 overall=bad；其中 7 个位于顶部权益/资产区上缘，方向 top，2 个位于领券中心右侧券边缘，方向 right。layout 对 9 框均未能直接坐实或消解，结果都是 unknown/unsupported_or_unmatched_issue。slide 分两组验证：顶部 7 框执行 down 滑动，均判定 scrollable，diffPercent 10.22%–46.92%；券栏 2 框执行 left 滑动，均判定 scrollable，diffPercent 19.65%/21.91%。9 框全部移除，最终页级 ok。
- 证据：HarmonyArena-fdu_agent/ux-detect-output/20260924-195610-843/snapshot_ux.json；HarmonyArena-fdu_agent/ux-detect-output/20260924-195610-843/snapshot_bbox.png；HarmonyArena-fdu_agent/ux-detect-output/20260924-195610-843/snapshot_slide_down_0.png；HarmonyArena-fdu_agent/ux-detect-output/20260924-195610-843/snapshot_slide_down_0.png.restore.png；HarmonyArena-fdu_agent/ux-detect-output/20260924-195610-843/snapshot_slide_left_1.png；HarmonyArena-fdu_agent/ux-detect-output/20260924-195610-843/snapshot_slide_left_1.png.restore.png；HarmonyArena-fdu_agent/ux-detect-output/20260924-195610-843/slide-ops.jsonl；HarmonyArena-fdu_agent/ux-detect-output/20260924-195610-843/snapshot_window.json
- 状态：**9 框全部消掉，页级 ok；有两组滑动和回滑恢复证据，但严重超预算。**

### WF-唯品会-G01-S1
- 设备：阔折 Pura X `6HQ0125A11000475`，外屏 `1264×1848`。按用户要求用 `hidumper -s 4607 -a -p` 切到外屏。
- GT：测试集/整理/widefold_xml_normal/vipshop/g01/widefold_xml_normal_vipshop_g01_s1.jpg
- 现场图：HarmonyArena-fdu_agent/ux-detect-output/20260924-195919-397/snapshot.png
- 页级：ok
- 人眼：外屏唯品会搜索页，与 GT 同类；现场搜索词是“纸巾小包”，GT 搜索词略有差异，但页面结构都是搜索框、最近搜索和猜你想搜标签。文件夹 widefold_xml_normal 判定为非截断样本，现场未见文字/组件/图标截断。
- 算法秒数：4.373s
- 模型/layout/slide：模型阶段成功返回 overall=ok、issues=[]，未识别出截断候选框；layout 空输入成功；slide 因无候选框跳过，符合非截断样本预期。
- 证据：HarmonyArena-fdu_agent/ux-detect-output/20260924-195919-397/snapshot_ux.json；HarmonyArena-fdu_agent/ux-detect-output/20260924-195919-397/snapshot_window.json
- 状态：**模型未出框，页级 ok。**

### WF-闲鱼-G01-S1
- 设备：阔折 Pura X `6HQ0125A11000475`，外屏 `1264×1848`。按用户要求用 `hidumper -s 4607 -a -p` 切到外屏。
- GT：测试集/整理/widefold_xml_normal/xianyu/g01/widefold_xml_normal_xianyu_g01_s1.jpg
- 现场图：HarmonyArena-fdu_agent/ux-detect-output/20260924-200058-978/snapshot.png
- 页级：bad
- 人眼：外屏闲鱼推荐流，与 GT 同类；现场搜索词为“手机支架”，商品流与 GT 不完全一致，但顶部搜索框、横向频道栏、服务入口、商品卡片和底部导航结构一致。文件夹 widefold_xml_normal 判定为非截断样本；现场顶部横向频道栏最右侧“手”字贴近右边界并被模型保留为右切文字候选，右侧服务入口的图标/文字候选则属于可横向滑动区域。
- 算法秒数：23.145s
- 超时/预算：totalMs=23145，modelMs=12921，slideMs=8118，algorithmMs=10224，algorithmOverBudget=true；页级 bad 且超过 10s 总预算和 7s algorithm 预算，功能与性能都需关注。
- 模型/layout/slide：模型阶段识别到 3 个候选框，raw 为 overall=bad：1 个顶部频道栏右侧文字框 `[893,134,931,158]`，2 个服务入口右侧图标/文字框 `[979,216,1000,258]`、`[974,280,1000,298]`。layout 对 3 框均未能直接坐实或消解，结果都是 unknown/unsupported_or_unmatched_issue。slide 分两组执行 left 滑动：顶部频道栏文字框 diffPercent=0，判定 confirmed，被保留；服务入口图标/文字同组 diffPercent=27.98/12.25，判定 scrollable，被移除。最终仍剩 1 个截断-文字右切框，页级 bad。
- 证据：HarmonyArena-fdu_agent/ux-detect-output/20260924-200058-978/snapshot_ux.json；HarmonyArena-fdu_agent/ux-detect-output/20260924-200058-978/snapshot_bbox.png；HarmonyArena-fdu_agent/ux-detect-output/20260924-200058-978/snapshot_bbox_final.png；HarmonyArena-fdu_agent/ux-detect-output/20260924-200058-978/snapshot_slide_left_0.png；HarmonyArena-fdu_agent/ux-detect-output/20260924-200058-978/snapshot_slide_left_1.png；HarmonyArena-fdu_agent/ux-detect-output/20260924-200058-978/snapshot_slide_left_1.png.restore.png；HarmonyArena-fdu_agent/ux-detect-output/20260924-200058-978/slide-ops.jsonl；HarmonyArena-fdu_agent/ux-detect-output/20260924-200058-978/snapshot_window.json
- 状态：**2 框消掉，1 个顶部频道栏右切文字框保留，页级 bad；同时超预算。**

### TF-京东-G01-S3
- 设备：三折叠 Mate XTs `29L0124226000058`（`GRL-AL10`），三屏 `3184×2232`。跑前用 `hidumper -s 4607 -a -g` 切换并用截图尺寸确认。
- GT：测试集/整理/trifold_xml_normal/jd/g01/trifold_xml_normal_jd_g01_s3.jpg
- 现场图：HarmonyArena-fdu_agent/ux-detect-output/20260924-201535-030/snapshot.png
- 页级：ok
- 人眼：三屏京东首页，与 GT 同类；搜索词、推荐流商品和右上角广告不同，但顶部一级 tab、搜索框、横向频道栏、服务入口、商品卡片区和底部导航结构一致。文件夹 trifold_xml_normal 判定为非截断样本，现场未见需要保留的文字截断。
- 算法秒数：19.693s
- 超时/预算：totalMs=19693，modelMs=8921，slideMs=7930，algorithmMs=10772，algorithmOverBudget=true；页级虽然 ok，但超过 10s 总预算和 7s algorithm 预算，性能需单独关注。
- 模型/layout/slide：模型阶段识别到 1 个候选框，raw 为 overall=bad、截断-文字、right，坐标 `[957,193,961,214]`，位于顶部横向频道栏右侧极窄边界附近。layout 未能直接坐实或消解，结果为 unknown/unsupported_or_unmatched_issue。slide 对该框执行 left 滑动，判定 scrollable，diffPercent=20.07，将候选框移除，最终页级 ok。该结果符合“可横向滑动消解，不算缺陷”的预期。
- 证据：HarmonyArena-fdu_agent/ux-detect-output/20260924-201535-030/snapshot_ux.json；HarmonyArena-fdu_agent/ux-detect-output/20260924-201535-030/snapshot_bbox.png；HarmonyArena-fdu_agent/ux-detect-output/20260924-201535-030/snapshot_slide_left_0.png；HarmonyArena-fdu_agent/ux-detect-output/20260924-201535-030/snapshot_slide_left_0.png.restore.png；HarmonyArena-fdu_agent/ux-detect-output/20260924-201535-030/slide-ops.jsonl；HarmonyArena-fdu_agent/ux-detect-output/20260924-201535-030/snapshot_window.json
- 状态：**一框消掉，页级 ok；但总耗时和 algorithm 耗时超预算。**

### TF-QQ音乐-G01-S3
- 设备：三折叠 Mate XTs `29L0124226000058`（`GRL-AL10`），三屏 `3184×2232`。跑前用截图尺寸确认。
- GT：测试集/整理/trifold_xml_normal/qqmusic/g01/trifold_xml_normal_qqmusic_g01_s3.jpg
- 现场图：HarmonyArena-fdu_agent/ux-detect-output/20260924-201846-565/snapshot.png
- 页级：ok
- 人眼：三屏 QQ音乐首页推荐页，与 GT 同类；顶部 tab、搜索框、推荐卡片、歌曲推荐列表和底部浮动播放/导航栏结构一致。现场推荐内容与 GT 不同，属于动态推荐流差异，不影响结构对齐。文件夹 trifold_xml_normal 判定为非截断样本，现场未见文字/组件/图标截断。
- 算法秒数：9.084s
- 超时/预算：totalMs=9084，modelMs=6493，slideMs=1，algorithmMs=2591，algorithmOverBudget=false；总耗时和 algorithm 未超预算，但 modelMs 超过 3s 模型预算，性能可记录关注。
- 模型/layout/slide：模型阶段成功返回 overall=ok、issues=[]，未识别出截断候选框；layout 空输入成功；slide 因无候选框跳过，符合非截断样本预期。
- 证据：HarmonyArena-fdu_agent/ux-detect-output/20260924-201846-565/snapshot_ux.json；HarmonyArena-fdu_agent/ux-detect-output/20260924-201846-565/snapshot_window.json
- 状态：**模型未出框，页级 ok。**

### TF-今日头条-G01-S3
- 设备：三折叠 Mate XTs `29L0124226000058`（`GRL-AL10`），三屏 `3184×2232`。跑前用截图尺寸确认。
- GT：测试集/整理/trifold_xml_normal/toutiao/g01/trifold_xml_normal_toutiao_g01_s3.jpg
- 现场图：HarmonyArena-fdu_agent/ux-detect-output/20260924-202413-768/snapshot.png
- 页级：ok
- 人眼：三屏今日头条首页推荐页，与 GT 同类；顶部头条入口、搜索框、频道栏、左右两栏新闻流和底部导航结构一致。现场新闻内容与 GT 不同，属于动态内容差异，不影响结构对齐。文件夹 trifold_xml_normal 判定为非截断样本，现场未见文字/组件/图标截断。
- 算法秒数：8.099s
- 超时/预算：totalMs=8099，modelMs=5867，slideMs=1，algorithmMs=2232，algorithmOverBudget=false；总耗时和 algorithm 未超预算，但 modelMs 超过 3s 模型预算，性能可记录关注。
- 模型/layout/slide：模型阶段成功返回 overall=ok、issues=[]，未识别出截断候选框；layout 空输入成功；slide 因无候选框跳过，符合非截断样本预期。
- 证据：HarmonyArena-fdu_agent/ux-detect-output/20260924-202413-768/snapshot_ux.json；HarmonyArena-fdu_agent/ux-detect-output/20260924-202413-768/snapshot_window.json
- 状态：**模型未出框，页级 ok。**

### TF-企业微信-G01-S3
- 设备：三折叠 Mate XTs `29L0124226000058`（`GRL-AL10`），三屏 `3184×2232`。跑前用截图尺寸确认。
- GT：测试集/整理/trifold_xml_normal/wecom/g01/trifold_xml_normal_wecom_g01_s3.jpg
- 现场图：HarmonyArena-fdu_agent/ux-detect-output/20260924-203039-893/snapshot.png
- 页级：ok
- 人眼：三屏企业微信工作台页，与 GT 同类；顶部标题、左侧竖向导航、AI 开放能力升级横幅、效率工具和教学互动区域结构一致。现场消息角标与 GT 略有差异，属于账号状态差异，不影响结构对齐。文件夹 trifold_xml_normal 判定为非截断样本，现场未见文字/组件/图标截断。
- 算法秒数：7.644s
- 超时/预算：totalMs=7644，modelMs=5633，slideMs=1，algorithmMs=2011，algorithmOverBudget=false；总耗时和 algorithm 未超预算，但 modelMs 超过 3s 模型预算，性能可记录关注。
- 模型/layout/slide：模型阶段成功返回 overall=ok、issues=[]，未识别出截断候选框；layout 空输入成功；slide 因无候选框跳过，符合非截断样本预期。
- 证据：HarmonyArena-fdu_agent/ux-detect-output/20260924-203039-893/snapshot_ux.json；HarmonyArena-fdu_agent/ux-detect-output/20260924-203039-893/snapshot_window.json
- 状态：**模型未出框，页级 ok。**

### TF-企业微信-G01-S2
- 设备：三折叠 Mate XTs `29L0124226000058`（`GRL-AL10`），二屏 `2048×2232`。按用户要求切到二屏后优先测试当前已调好的企业微信页面，跑前用截图尺寸确认。
- GT：测试集/整理/trifold_xml_normal/wecom/g01/trifold_xml_normal_wecom_g01_s2.jpg
- 现场图：HarmonyArena-fdu_agent/ux-detect-output/20260924-203241-166/snapshot.png
- 页级：ok
- 人眼：二屏企业微信工作台页，与 GT 同类；顶部标题、AI 开放能力升级横幅、效率工具、教学互动和底部导航结构一致。现场消息角标与账号状态有关，不影响结构对齐。文件夹 trifold_xml_normal 判定为非截断样本，现场未见文字/组件/图标截断。
- 算法秒数：5.814s
- 超时/预算：totalMs=5814，modelMs=3831，slideMs=1，algorithmMs=1983，algorithmOverBudget=false；总耗时和 algorithm 未超预算，但 modelMs 略超过 3s 模型预算，性能可记录关注。
- 模型/layout/slide：模型阶段成功返回 overall=ok、issues=[]，未识别出截断候选框；layout 空输入成功；slide 因无候选框跳过，符合非截断样本预期。
- 证据：HarmonyArena-fdu_agent/ux-detect-output/20260924-203241-166/snapshot_ux.json；HarmonyArena-fdu_agent/ux-detect-output/20260924-203241-166/snapshot_window.json
- 状态：**模型未出框，页级 ok。**

### TF-京东-G01-S2
- 设备：三折叠 Mate XTs `29L0124226000058`（`GRL-AL10`），二屏 `2048×2232`。跑前用截图尺寸确认。
- GT：测试集/整理/trifold_xml_normal/jd/g01/trifold_xml_normal_jd_g01_s2.jpg
- 现场图：HarmonyArena-fdu_agent/ux-detect-output/20260924-203433-509/snapshot.png
- 页级：ok
- 人眼：二屏京东首页，与 GT 同类；搜索词、推荐流商品和右上角广告不同，但顶部一级 tab、搜索框、横向频道栏、服务入口、商品卡片区和底部导航结构一致。文件夹 trifold_xml_normal 判定为非截断样本，现场候选位于服务入口横向列表右侧边缘，属于可横向滑动区域。
- 算法秒数：19.601s
- 超时/预算：totalMs=19601，modelMs=9505，slideMs=7418，algorithmMs=10096，algorithmOverBudget=true；页级虽然 ok，但超过 10s 总预算和 7s algorithm 预算，性能需单独关注。
- 模型/layout/slide：模型阶段识别到 2 个候选框，raw 为 overall=bad：右侧服务入口边缘图标框 `[978,210,1000,258]` 和文字框 `[965,260,1000,277]`，方向均为 right。layout 对 2 框均未能直接坐实或消解，结果都是 unknown/unsupported_or_unmatched_issue。slide 对该组执行 left 滑动，判定 scrollable，diffPercent=17.58/13.62，将 2 个候选框全部移除，最终页级 ok。该结果符合“可横向滑动消解，不算缺陷”的预期。
- 证据：HarmonyArena-fdu_agent/ux-detect-output/20260924-203433-509/snapshot_ux.json；HarmonyArena-fdu_agent/ux-detect-output/20260924-203433-509/snapshot_bbox.png；HarmonyArena-fdu_agent/ux-detect-output/20260924-203433-509/snapshot_slide_left_0.png；HarmonyArena-fdu_agent/ux-detect-output/20260924-203433-509/snapshot_slide_left_0.png.restore.png；HarmonyArena-fdu_agent/ux-detect-output/20260924-203433-509/slide-ops.jsonl；HarmonyArena-fdu_agent/ux-detect-output/20260924-203433-509/snapshot_window.json
- 状态：**2 框全部消掉，页级 ok；但总耗时和 algorithm 耗时超预算。**

### TF-QQ音乐-G01-S2
- 设备：三折叠 Mate XTs `29L0124226000058`（`GRL-AL10`），二屏 `2048×2232`。跑前用截图尺寸确认。
- GT：测试集/整理/trifold_xml_normal/qqmusic/g01/trifold_xml_normal_qqmusic_g01_s2.jpg
- 现场图：HarmonyArena-fdu_agent/ux-detect-output/20260924-203742-766/snapshot.png
- 页级：ok
- 人眼：二屏 QQ音乐首页推荐页，与 GT 同类；顶部搜索框、横向 tab、推荐卡片、歌曲推荐列表和底部浮动播放/导航栏结构一致。现场推荐内容与 GT 不同，属于动态推荐流差异，不影响结构对齐。文件夹 trifold_xml_normal 判定为非截断样本，现场未见文字/组件/图标截断。
- 算法秒数：7.771s
- 超时/预算：totalMs=7771，modelMs=5008，slideMs=1，algorithmMs=2763，algorithmOverBudget=false；总耗时和 algorithm 未超预算，但 modelMs 超过 3s 模型预算，性能可记录关注。
- 模型/layout/slide：模型阶段成功返回 overall=ok、issues=[]，未识别出截断候选框；layout 空输入成功；slide 因无候选框跳过，符合非截断样本预期。
- 证据：HarmonyArena-fdu_agent/ux-detect-output/20260924-203742-766/snapshot_ux.json；HarmonyArena-fdu_agent/ux-detect-output/20260924-203742-766/snapshot_window.json
- 状态：**模型未出框，页级 ok。**

### TF-今日头条-G01-S2
- 设备：三折叠 Mate XTs `29L0124226000058`（`GRL-AL10`），二屏 `2048×2232`。跑前用截图尺寸确认。
- GT：测试集/整理/trifold_xml_normal/toutiao/g01/trifold_xml_normal_toutiao_g01_s2.jpg
- 现场图：HarmonyArena-fdu_agent/ux-detect-output/20260924-204121-510/snapshot.png
- 页级：ok
- 人眼：二屏今日头条首页推荐页，与 GT 同类；顶部头条入口、搜索框、频道栏、左右两栏新闻流和底部导航结构一致。现场新闻内容与 GT 不同，属于动态内容差异，不影响结构对齐。GT JSON 为 `正常图=true` 且 `shapes=[]`，文件夹 trifold_xml_normal 判定为非截断样本；模型未出框与 GT 一致，不属于漏检。
- 算法秒数：6.779s
- 超时/预算：totalMs=6779，modelMs=4408，slideMs=1，algorithmMs=2371，algorithmOverBudget=false；总耗时和 algorithm 未超预算，但 modelMs 超过 3s 模型预算，性能可记录关注。
- 模型/layout/slide：模型阶段成功返回 overall=ok、issues=[]，未识别出截断候选框；layout 空输入成功；slide 因无候选框跳过，符合非截断样本预期。
- 证据：HarmonyArena-fdu_agent/ux-detect-output/20260924-204121-510/snapshot_ux.json；HarmonyArena-fdu_agent/ux-detect-output/20260924-204121-510/snapshot_window.json
- 状态：**模型未出框，页级 ok。**

### TF-今日头条-G01-S1
- 设备：三折叠 Mate XTs `29L0124226000058`（`GRL-AL10`），单屏 `1008×2232`。按用户要求用 `hidumper -s 4607 -a -p` 切到单屏，跑前用截图尺寸确认。
- GT：测试集/整理/trifold_xml_normal/toutiao/g01/trifold_xml_normal_toutiao_g01_s1.jpg
- 现场图：HarmonyArena-fdu_agent/ux-detect-output/20260924-205147-459/snapshot.png
- 页级：ok
- 人眼：单屏今日头条首页推荐页，与 GT 同类；顶部头条入口、搜索框、频道栏、新闻列表和底部导航结构一致。现场新闻内容与 GT 不同，属于动态内容差异，不影响结构对齐。GT JSON 为 `正常图=true` 且 `shapes=[]`，文件夹 trifold_xml_normal 判定为非截断样本；模型未出框与 GT 一致。
- 算法秒数：4.568s
- 超时/预算：totalMs=4568，modelMs=2714，slideMs=0，algorithmMs=1854，algorithmOverBudget=false；总耗时、model 和 algorithm 均未超预算。
- 模型/layout/slide：模型阶段成功返回 overall=ok、issues=[]，未识别出截断候选框；layout 空输入成功；slide 因无候选框跳过，符合非截断样本预期。
- 证据：HarmonyArena-fdu_agent/ux-detect-output/20260924-205147-459/snapshot_ux.json；HarmonyArena-fdu_agent/ux-detect-output/20260924-205147-459/snapshot_window.json
- 状态：**模型未出框，页级 ok；与 GT 空标注一致。**

### TF-京东-G01-S1
- 设备：三折叠 Mate XTs `29L0124226000058`（`GRL-AL10`），单屏 `1008×2232`。跑前用截图尺寸确认。
- GT：测试集/整理/trifold_xml_normal/jd/g01/trifold_xml_normal_jd_g01_s1.jpg；GT JSON 有 1 个右切图标框，坐标约 `[954,461,1008,555]`，`正常图=false`。
- 现场图：HarmonyArena-fdu_agent/ux-detect-output/20260924-205706-287/snapshot.png
- 页级：ok
- 人眼：单屏京东首页，与 GT 同类；搜索词、推荐流商品和右上角广告不同，但顶部一级 tab、搜索框、横向频道栏、服务入口、商品卡片区和底部导航结构一致。现场右侧服务入口有半露出的图标/文字，和 GT 右切图标预期同类，属于横向可滑动区域。
- 算法秒数：36.302s
- 超时/预算：totalMs=36302，modelMs=13270，slideMs=20568，algorithmMs=23032，algorithmOverBudget=true；页级虽然 ok，但总耗时、模型耗时、滑动耗时和 algorithm 耗时均严重超预算，性能需重点关注。
- 模型/layout/slide：模型阶段识别到 4 个候选框，raw 为 overall=bad：顶部频道栏右侧文字框 `[869,158,905,176]`，服务入口右侧文字框 `[929,243,1000,258]`，服务入口右侧图标框 `[944,201,1000,241]`，以及商品流底部组件框 `[509,889,977,901]`。其中服务入口右侧图标框与 GT 右切图标预期匹配，模型有命中；layout 对 4 框均未能直接坐实或消解，结果都是 unknown/unsupported_or_unmatched_issue。slide 分三组验证：顶部频道栏执行 left 滑动，diffPercent=36.59；服务入口图标/文字同组执行 left 滑动，diffPercent=21.58/16.41；商品流底部组件执行 up 滑动，diffPercent=18.68。4 个候选框全部判定 scrollable 并移除，最终页级 ok。
- 证据：HarmonyArena-fdu_agent/ux-detect-output/20260924-205706-287/snapshot_ux.json；HarmonyArena-fdu_agent/ux-detect-output/20260924-205706-287/snapshot_bbox.png；HarmonyArena-fdu_agent/ux-detect-output/20260924-205706-287/snapshot_slide_left_0.png；HarmonyArena-fdu_agent/ux-detect-output/20260924-205706-287/snapshot_slide_left_0.png.restore.png；HarmonyArena-fdu_agent/ux-detect-output/20260924-205706-287/snapshot_slide_left_1.png；HarmonyArena-fdu_agent/ux-detect-output/20260924-205706-287/snapshot_slide_left_1.png.restore.png；HarmonyArena-fdu_agent/ux-detect-output/20260924-205706-287/snapshot_slide_up_2.png；HarmonyArena-fdu_agent/ux-detect-output/20260924-205706-287/snapshot_slide_up_2.png.restore.png；HarmonyArena-fdu_agent/ux-detect-output/20260924-205706-287/slide-ops.jsonl；HarmonyArena-fdu_agent/ux-detect-output/20260924-205706-287/snapshot_window.json
- 状态：**GT 右切图标已命中；4 框全部消掉，页级 ok；但严重超预算。**

### TF-QQ音乐-G01-S1
- 设备：三折叠 Mate XTs `29L0124226000058`（`GRL-AL10`），单屏 `1008×2232`。跑前用截图尺寸确认。
- GT：测试集/整理/trifold_xml_normal/qqmusic/g01/trifold_xml_normal_qqmusic_g01_s1.jpg；GT JSON 为 `正常图=true` 且 `shapes=[]`。
- 现场图：HarmonyArena-fdu_agent/ux-detect-output/20260924-210248-467/snapshot.png
- 页级：ok
- 人眼：单屏 QQ音乐首页推荐页，与 GT 同类；顶部搜索框、横向 tab、推荐卡片、歌曲推荐列表和底部浮动播放/导航栏结构一致。现场推荐内容与 GT 不同，属于动态推荐流差异，不影响结构对齐。GT 为空标注正常图，现场未见文字/组件/图标截断。
- 算法秒数：5.094s
- 超时/预算：totalMs=5094，modelMs=3125，slideMs=0，algorithmMs=1969，algorithmOverBudget=false；总耗时和 algorithm 未超预算，modelMs 略超过 3s 模型预算，性能可记录关注。
- 模型/layout/slide：模型阶段成功返回 overall=ok、issues=[]，未识别出截断候选框；layout 空输入成功；slide 因无候选框跳过，符合非截断样本预期。
- 证据：HarmonyArena-fdu_agent/ux-detect-output/20260924-210248-467/snapshot_ux.json；HarmonyArena-fdu_agent/ux-detect-output/20260924-210248-467/snapshot_window.json
- 状态：**模型未出框，页级 ok；与 GT 空标注一致。**

### TF-企业微信-G01-S1
- 设备：三折叠 Mate XTs `29L0124226000058`（`GRL-AL10`），单屏 `1008×2232`。跑前用截图尺寸确认。
- GT：测试集/整理/trifold_xml_normal/wecom/g01/trifold_xml_normal_wecom_g01_s1.jpg；GT JSON 为 `正常图=true` 且 `shapes=[]`。
- 现场图：HarmonyArena-fdu_agent/ux-detect-output/20260924-210721-420/snapshot.png
- 页级：ok
- 人眼：单屏企业微信工作台页，与 GT 同类；顶部标题、AI 开放能力升级横幅、效率工具、教学互动、学校管理和底部导航结构一致。现场消息角标与账号状态有关，不影响结构对齐。GT 为空标注正常图，现场未见文字/组件/图标截断。
- 算法秒数：4.501s
- 超时/预算：totalMs=4501，modelMs=2503，slideMs=1，algorithmMs=1998，algorithmOverBudget=false；总耗时、model 和 algorithm 均未超预算。
- 模型/layout/slide：模型阶段成功返回 overall=ok、issues=[]，未识别出截断候选框；layout 空输入成功；slide 因无候选框跳过，符合非截断样本预期。
- 证据：HarmonyArena-fdu_agent/ux-detect-output/20260924-210721-420/snapshot_ux.json；HarmonyArena-fdu_agent/ux-detect-output/20260924-210721-420/snapshot_window.json
- 状态：**模型未出框，页级 ok；与 GT 空标注一致。**

### PHONE-携程-G01-S1
- 设备：Mate60 Pro `LNG0123525000430`（`ALN-AL00`），直屏单屏 `1260×2720`。本轮开始前发现仓库开启 sparse checkout，`phone_xml_normal` 仅在 Git 索引中未展开；已用 `git sparse-checkout add 测试集/整理/phone_xml_normal` 展开该 XML 测试集。
- GT：测试集/整理/phone_xml_normal/ctrip/g01/phone_xml_normal_ctrip_g01_s1.jpg；GT JSON 为 `正常图=true` 且 `shapes=[]`。
- 现场图：HarmonyArena-fdu_agent/ux-detect-output/20260924-212055-994/snapshot.png
- 页级：ok
- 人眼：直屏携程首页，与 GT 同类；顶部携程旅行标题、会员入口、核心产品宫格、搜索框、城市快捷入口、功能卡片、双列推荐流和底部导航结构一致。现场推荐内容与 GT 存在动态差异，但页面结构对齐，未见文字/组件/图标截断。
- 算法秒数：6.159s
- 超时/预算：totalMs=6159，modelMs=3722，slideMs=1，algorithmMs=2437，algorithmOverBudget=false；总耗时和 algorithm 未超预算，但 modelMs 超过 3s 模型预算，性能可记录关注。
- 模型/layout/slide：模型阶段成功返回 overall=ok、issues=[]，未识别出截断候选框；layout 空输入成功；slide 因无候选框跳过，符合 GT 空标注正常图预期，不属于漏检。
- 证据：HarmonyArena-fdu_agent/ux-detect-output/20260924-212055-994/snapshot_ux.json；HarmonyArena-fdu_agent/ux-detect-output/20260924-212055-994/snapshot_window.json
- 状态：**模型未出框，页级 ok；与 GT 空标注一致。**

### PHONE-钉钉-G01-S1
- 设备：Mate60 Pro `LNG0123525000430`（`ALN-AL00`），直屏单屏 `1260×2720`。
- GT：测试集/整理/phone_xml_normal/dingding/g01/phone_xml_normal_dingding_g01_s1.jpg；GT JSON 为 `正常图=true` 且 `shapes=[]`。
- 现场图：HarmonyArena-fdu_agent/ux-detect-output/20260924-212257-572/snapshot.png
- 页级：ok
- 人眼：直屏钉钉消息页，与 GT 同类；顶部头像/名称、搜索入口、消息/置顶/未读分段、消息列表和底部导航结构一致。现场账号名称和消息内容与 GT 存在个人账号差异，但页面结构对齐；列表中的省略号为正常文本省略展示，未见文字/组件/图标异常截断。
- 算法秒数：5.337s
- 超时/预算：totalMs=5337，modelMs=3264，slideMs=1，algorithmMs=2073，algorithmOverBudget=false；总耗时和 algorithm 未超预算，但 modelMs 略超过 3s 模型预算，性能可记录关注。
- 模型/layout/slide：模型阶段成功返回 overall=ok、issues=[]，未识别出截断候选框；layout 空输入成功；slide 因无候选框跳过，符合 GT 空标注正常图预期，不属于漏检。
- 证据：HarmonyArena-fdu_agent/ux-detect-output/20260924-212257-572/snapshot_ux.json；HarmonyArena-fdu_agent/ux-detect-output/20260924-212257-572/snapshot_window.json
- 状态：**模型未出框，页级 ok；与 GT 空标注一致。**

### PHONE-爱奇艺-G01-S1
- 设备：Mate60 Pro `LNG0123525000430`（`ALN-AL00`），直屏单屏 `1260×2720`。
- GT：测试集/整理/phone_xml_normal/iqiyi/g01/phone_xml_normal_iqiyi_g01_s1.jpg；GT JSON 为 `正常图=true` 且 `shapes=[]`。
- 现场图：HarmonyArena-fdu_agent/ux-detect-output/20260924-212806-654/snapshot.png
- 页级：ok
- 人眼：直屏爱奇艺首页，与 GT 同类；顶部 iQIYI 标识、搜索框、频道/推荐内容区、双列视频卡片和底部导航结构一致。现场影视推荐内容与 GT 不同，属于动态内容差异，不影响结构对齐；未见文字/组件/图标异常截断。
- 算法秒数：7.780s
- 超时/预算：totalMs=7780，modelMs=4964，slideMs=1，algorithmMs=2816，algorithmOverBudget=false；总耗时和 algorithm 未超预算，但 modelMs 明显超过 3s 模型预算，性能需记录关注。
- 模型/layout/slide：模型阶段成功返回 overall=ok、issues=[]，未识别出截断候选框；layout 空输入成功；slide 因无候选框跳过，符合 GT 空标注正常图预期，不属于漏检。
- 证据：HarmonyArena-fdu_agent/ux-detect-output/20260924-212806-654/snapshot_ux.json；HarmonyArena-fdu_agent/ux-detect-output/20260924-212806-654/snapshot_window.json
- 状态：**模型未出框，页级 ok；与 GT 空标注一致，但模型耗时超预算。**

### PHONE-QQ-G01-S1
- 设备：Mate60 Pro `LNG0123525000430`（`ALN-AL00`），直屏单屏 `1260×2720`。
- GT：测试集/整理/phone_xml_normal/qq/g01/phone_xml_normal_qq_g01_s1.jpg；GT JSON 为 `正常图=true` 且 `shapes=[]`。
- 现场图：HarmonyArena-fdu_agent/ux-detect-output/20260924-213111-696/snapshot.png
- 页级：ok
- 人眼：直屏 QQ 消息页，与 GT 同类；顶部头像/在线状态、搜索框、会话列表和底部消息/频道/联系人/动态导航结构一致。现场账号、会话数量和会话内容与 GT 有账号差异，但结构对齐；会话名和摘要中的省略号属于列表正常省略展示，未见文字/组件/图标异常截断。
- 算法秒数：5.338s
- 超时/预算：totalMs=5338，modelMs=3105，slideMs=1，algorithmMs=2233，algorithmOverBudget=false；总耗时和 algorithm 未超预算，modelMs 略超过 3s 模型预算，性能可记录关注。
- 模型/layout/slide：模型阶段成功返回 overall=ok、issues=[]，未识别出截断候选框；layout 空输入成功；slide 因无候选框跳过，符合 GT 空标注正常图预期，不属于漏检。
- 证据：HarmonyArena-fdu_agent/ux-detect-output/20260924-213111-696/snapshot_ux.json；HarmonyArena-fdu_agent/ux-detect-output/20260924-213111-696/snapshot_window.json
- 状态：**模型未出框，页级 ok；与 GT 空标注一致。**

### PHONE-腾讯新闻-G01-S1
- 设备：Mate60 Pro `LNG0123525000430`（`ALN-AL00`），直屏单屏 `1260×2720`。
- GT：测试集/整理/phone_xml_normal/tencentnews/g01/phone_xml_normal_tencentnews_g01_s1.jpg；GT JSON 为 `正常图=false`，含 3 个右切标注：2 个文字框约 `[1205,1409,1260,1469]`、`[1206,1579,1260,1619]`，以及 1 个图标框约 `[1208,1066,1260,1129]`。
- 现场图：HarmonyArena-fdu_agent/ux-detect-output/20260924-213345-664/snapshot.png
- 页级：ok
- 人眼：直屏腾讯新闻要闻页，与 GT 同类；顶部搜索栏、频道栏、要闻列表、横向热点卡片、新闻流和底部导航结构一致。现场新闻内容与 GT 动态不同，但横向热点卡片右侧同样存在露出区域。按当前“主要识别文字截断”的测试口径，模型命中并验证了文字候选；GT 另有 1 个右切图标框，模型未单独输出图标候选，需在读数时注意该差异。
- 算法秒数：17.095s
- 超时/预算：totalMs=17095，modelMs=8373，slideMs=6214，algorithmMs=8722，algorithmOverBudget=true；总耗时、模型耗时和 algorithm 耗时均超预算，性能需重点关注。
- 模型/layout/slide：模型阶段识别到 2 个右切文字候选框，raw 为 overall=bad：`[958,540,1000,592]`、`[965,418,1000,435]`。layout 对 2 框均未能直接坐实或消解，结果为 unknown/unsupported_or_unmatched_issue。slide 将 2 框分为同一组执行 left 滑动，页面发生横向移动并成功恢复；候选 0 diffPercent=20.48，候选 1 bbox 内 diffPercent=0 但 group/page probe 判定 pageMoved/probeMoved，因此同组均判定 scrollable 并移除，最终页级 ok。
- 证据：HarmonyArena-fdu_agent/ux-detect-output/20260924-213345-664/snapshot_ux.json；HarmonyArena-fdu_agent/ux-detect-output/20260924-213345-664/snapshot_bbox.png；HarmonyArena-fdu_agent/ux-detect-output/20260924-213345-664/snapshot_slide_left_0.png；HarmonyArena-fdu_agent/ux-detect-output/20260924-213345-664/snapshot_slide_left_0.png.restore.png；HarmonyArena-fdu_agent/ux-detect-output/20260924-213345-664/slide-ops.jsonl；HarmonyArena-fdu_agent/ux-detect-output/20260924-213345-664/snapshot_window.json
- 状态：**文字候选命中后被横向滑动流程消解，页级 ok；GT 图标框未单独输出；整体严重超预算。**
