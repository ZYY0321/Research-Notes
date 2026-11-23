# Bench215 今晚对齐：Sonnet 分析 × 人工评判

2026-09-09。看台 `comments.json` 92 条批注 + 正式 215 道 Sonnet 卡。主张分类沿用 `bench215-已看55-论文点.md`，后半夜补的批注追加进来，不另起主张。

口径仍是 `bench215-锁表口径-20260908.md`：Sonnet 当分类器；已驳过的以你为准；旧 Gemini/Qwen 分不翻。

## 0. 数字

| 项 | 数 |
|---|---|
| 正式题 | 215 |
| Sonnet 卡 | 215（全覆盖） |
| 你写过批注 | 92 |
| 点过按钮 | 55（保留 33 · 改题 12 · 修判定 10 · 拿掉 0） |
| 只写字没点按钮 | 37 |
| 还没批 | 123 |

按钮数和 9/8 锁表稿「改题 11 · 修判定 11」差 1：现在是改题 12、修判定 10，仍合计 55。

## 1. 你点过按钮的 55

短名用看台 `table_id`。

### 保留（33）

- **v6.case_01** `hybrid_tools_v6.HTV6Case01`
  - 你：这道题还是比较典型的，就是交互是个比较难的事情，模型不确定要不要往下滑，滑多少，于是倾向于就看“第一屏”

- **v6.case_08** `hybrid_tools_v6.HTV6Case08`
  - 你：这个任务质量确实还可以，比较典型。

- **v6.case_09** `hybrid_tools_v6.HTV6Case09`
  - 你：这里分析错了其实，我们系统时间固定的七月多份，他查询这个日期是对的，不过数据可能没有对应上吗？不太确定。

- **v6.case_13** `hybrid_tools_v6.HTV6Case13`
  - 你：bilibili__get_ranking` 在 hybrid 路径下返回空是一个状态不一致问题 ，这个必须查一下，是模型调用工具问题还是本身工具问题。为什么这么多次检查之后还是有这么多问题呢。。。。其实这个能体现出来我们固定模拟环境的一个小优势就是，我们可以固定“排行榜第一”这种可能动态变化的项有助于我们验证。

- **v6.case_14** `hybrid_tools_v6.HTV6Case14`
  - 你：但如果将来想收紧到"内容不含无关冗余"就得加字段。当前宽松判定对于基准测试是可接受的，不构成误判。这个确实是值得注意的一个点，先保留，后续可以考虑收束这里的验证。然后纯gui的反复操作值得拿出来说的。不过这次案例我看了过程，他并没写错，小红书如果只发布文字的话就是那个样子的，而且题面其实也并没有规定怎么发布。这任…

- **v6.case_16** `hybrid_tools_v6.HTV6Case16`
  - 你：比较平庸的题

- **v6.case_22** `hybrid_tools_v6.HTV6Case22`
  - 你：这个还行吧，发现纯gui ，模型新建操作竟然还能出错。不过排序推理倒是对的。

- **v6.case_75** `hybrid_tools_v6.HTV6Case75`
  - 你：这个确实是通过工具绕过了一些gui陷阱。他这个日历，你点了一个具体日期之后点加号，只能输出时间，不能改日期，必须一开始就点到正确的具体日期。。。

- **e0815.broadcast.broadcast_task_04** `hybrid_tools_0815_explore.HTV1ExploreBroadcastBroadcastTask04`
  - 你：模型把进度条目标位置计算为总时长的某个比例并点击，实际落在 31:15 左右（1875 秒），miss 了约 75 秒，被判 fail。这不是理解错误，是拖拽/点击精度问题，在真实手机上也常见。 这个可能是一个值得注意的问题。拖拽精度导致的失败。工具返回值（`queued: true, queue_length:…

- **e0815.broadcast.broadcast_task_08** `hybrid_tools_0815_explore.HTV1ExploreBroadcastBroadcastTask08`
  - 你：或者 API 的队列和 UI 的"待播清单"视图不完全同步 这种问题必须解决。然后我们还得考虑一下怎么处理这个数据。是不是qwen那个这里也是hybrid出错？这种如果能把hybrid掰正，或者证明模型不会用工具会比较好。

- **e0815.ctrip.ctrip_002** `hybrid_tools_0815_explore.HTV1ExploreCtripCtrip002`
  - 你：简单题

- **e0815.ctrip.ctrip_003** `hybrid_tools_0815_explore.HTV1ExploreCtripCtrip003`
  - 你：这是不是说明环境依然有问题。真正的问题在 `flightDirectOnly`：GUI-only 走了相同的筛选路径却读出 null，Hybrid 走了更乱的路却写入成功。这说明该字段的写入触发点在模拟器里不稳定，或者对应的 UI 元素在两条轨迹里实际上是不同的（hybrid 绕弯时点到了某个持久化开关，GUI-…

- **e0815.daysmatter.dm_003** `hybrid_tools_0815_explore.HTV1ExploreDaysmatterDm003`
  - 你：值得在初态或工具返回里明确注入日期上下文。。他自己不确定日期应该去日历里面看。不是自己编一个对吧。模型在界面操控失败后主动切换到工具通道并几乎完成任务，展示了工具作为"backup channel"的实际效用，这个问题，为什么他不会想到一开始就去调用工具呢？

- **e0815.daysmatter.dm_006** `hybrid_tools_0815_explore.HTV1ExploreDaysmatterDm006`
  - 你：Hybrid 模式完全没有调用任何工具**（tools 列表为空），这才是最值得关注的地方。`daysmatter__prepare_event_draft` 等工具本可以直接写入 endDate 字段，跳过整个 UI 日期选择器，但模型全程没有意识到工具可以作为绕过 UI 难点的第二通道。这正是 Hybrid …

- **e0815.dianping.dp_task_01** `hybrid_tools_0815_explore.HTV1ExploreDianpingDpTask01`
  - 你：收藏菜品那段（步骤9-12 / 10-12）两条轨迹都经历了"点图片没反应→点文字没反应→找到'查看全部'→在列表页收藏"的多步摸索，说明界面里推荐菜的收藏入口不在第一个可见元素上，模型靠盲试找到了，正好说明这条路径在 GUI 上是可走但需要探索的。这个点其实是我在任务设计的时候故意设计的，他能够成功其实还不错

- **v6.case_42** `hybrid_tools_v6.HTV6Case42`
  - 你：这道题比较正常且典型，难度中等

- **e0815.dianping.dp_task_08** `hybrid_tools_0815_explore.HTV1ExploreDianpingDpTask08`
  - 你：这是正式集里质量较高的一类题：界面流程有层次（首页→我的→订单→订单详情→申请退款→选原因→提交），有真实的下拉选择和表单提交，任务本身对普通用户有意义。。这个需要记录的。但这道题的结果可能是轨迹污染了。可能修好了环境才跑了这个有工具的题，会有误导。需要记录

- **e0815.didi.didi_001** `hybrid_tools_0815_explore.HTV1ExploreDidiDidi001`
  - 你：这道题还是无法体现混合调用优势。我也不知道咋办了

- **e0815.douban.task_03** `hybrid_tools_0815_explore.HTV1ExploreDoubanTask03`
  - 你：整体来说是一道结构正常、有实际手机操作难度的任务，三条独立效果分开验证也是好做法。模型对"输入没有生效"的反馈处理比较机械这件事我觉得也是这样的

- **e0815.douban.task_01** `hybrid_tools_0815_explore.HTV1ExploreDoubanTask01`
  - 你：影评区"友邻排序"这个细节是有区分度的——模型必须找到正确的排序入口，而不是停在默认热门视图，确实，这是我们希望有的特性。核心差别是 Hybrid 路径对"友邻视图有内容"的假设更坚持，没有被 UI 反馈击退。从示范价值看，这个例子可以说明：模型在 GUI-only 模式下对"当前视图看不到目标内容"这类中间状态…

- **e0815.douban.task_02** `hybrid_tools_0815_explore.HTV1ExploreDoubanTask02`
  - 你：其中 `search_subjects` 理论上可以带条件参数直接拿合格片单，是正宗的 plus 通道。但两条轨迹都没用工具，hybrid 退化成了纯 GUI。这道题的 plus 通道设计是合理的，只是没有被用上。 这个确实值得记录一下呢

- **e0815.fanqiexiaoshuo.T01** `hybrid_tools_0815_explore.HTV1ExploreFanqiexiaoshuoT01`
  - 你：弹窗绕路带来的步数膨胀，不涉及规划或工具使用的对比。这个点也挺重要的，有些hybrid步数更多的例子纯粹是波动了

- **e0815.fanqiexiaoshuo.T02** `hybrid_tools_0815_explore.HTV1ExploreFanqiexiaoshuoT02`
  - 你：这题一般，有迷惑性

- **e0815.fanqiexiaoshuo.T04** `hybrid_tools_0815_explore.HTV1ExploreFanqiexiaoshuoT04`
  - 你：这个也是特地留的导航难点题

- **e0815.fanqiexiaoshuo.T05** `hybrid_tools_0815_explore.HTV1ExploreFanqiexiaoshuoT05`
  - 你：也是导航误导性的难度题。包括需要模型确认是否是连载中的题

- **e0815.fanqiexiaoshuo.T07** `hybrid_tools_0815_explore.HTV1ExploreFanqiexiaoshuoT07`
  - 你：这段探索显示了应对非预期界面跳转的一定韧性。卧槽这个app简直了，路径是迷宫啊，哈哈哈，很好

- **e0815.fanqiexiaoshuo.T08** `hybrid_tools_0815_explore.HTV1ExploreFanqiexiaoshuoT08`
  - 你：这个ui是不是有点问题啊。。。

- **e0815.flomo.flomo_08** `hybrid_tools_0815_explore.HTV1ExploreFlomoFlomo08`
  - 你："已识别错误但无法自我纠正"现象，思考链里的文字几乎一字不差。模型知道自己在循环（"swiping on the note triggered the long press menu again"），却没有跳出策略，比如换成更小的起点偏移、或直接用工具确认 id 后换一种交互方式。

- **e0815.keep.keep_task_04** `hybrid_tools_0815_explore.HTV1ExploreKeepKeepTask04`
  - 你：但 runSession.status=running 本身无法区分"真正恢复跑步"和"点了继续但还没迈步"。在当前模拟环境下这不是实际问题，但如果将来迁移到真机评测，需要确认采样时机。

- **S_finance_bill** `bench200_flow.HTV1FinanceGasKapi`
  - 你：这道题可以看出如果是工具调用失败，可能会导致步数增加回退到gui的。

- **S_shop_01** `bench200_flow.HTV1ShopVivoKapi`
  - 你：Hybrid step 7–9 那段滚屏找国补开关是小弯路，但 step 10 thought 里模型正确推断补贴已含在价格里、无需额外操作，之后直接提交，没有卡死或重复探索。这个"工具返回数据 → 推断 → 跳过多余界面操作"的行为模式如果要举 Hybrid 优势的例子，这里可以作为一个小佐证

- **S_travel_train_cal** `bench200_flow.HTV1TravelTrainCal`
  - 你：作为"跨 App 运行时值传递"类目的典型通过样本

- **S_travel_hotel_kapi** `bench200_flow.HTV1TravelHotelKapi`
  - 你：可以用来展示工具在数值读取和跨 App 状态转移上的稳定性收益

### 改题（12）

- **v6.case_03** `hybrid_tools_v6.HTV6Case03`
  - 你：找 Notes 过程中误入 SMS，这个是谁的问题呢？模型问题还是题面问题。算不算是模型那种陷入循环的老问题呢。不过没有明确说明笔记是哪个app也是题面的问题，这个肯定需要改一下的。

- **e0815.boss.boss_task_02** `hybrid_tools_0815_explore.HTV1ExploreBossBossTask02`
  - 你：去「收藏」页看看职位和公司都存进去了没有。 这个指令，根本没有验证，意义是啥。“一个潜在的设计问题：题面把"收藏职位"和"收藏公司"描述为并列目标，但路径上两者高度耦合——通常从职位详情页点进公司页，再收藏公司，算不上独立的第二条路线。如果想用这道题测"能否分别触达两类收藏"，初态里职位和公司入口是否都可以独立访…

- **e0815.boss.boss_task_05** `hybrid_tools_0815_explore.HTV1ExploreBossBossTask05`
  - 你：不改正式 215 对错：Gemini / Qwen 的 GUI、Hybrid 都挂，终态是招呼 s2 已标不感兴趣、切过「仅沟通」，但蔺晓禾没有任何一条会话 blocked。新判定拆开后，这种终态仍然失败。旧题面把「不感兴趣、加入黑名单」写成同一条会话、还不感兴趣在前。一点确定会话就从列表消失，再拉黑只能搜岗绕回…

- **e0815.boss.boss_task_07** `hybrid_tools_0815_explore.HTV1ExploreBossBossTask07`
  - 你：核心问题是模型缺乏可靠的"滑动幅度→小时偏移量"映射，每次滑过头（08→13）或滑不到（08→08 不动）再往回补，陷入振荡循环。两条轨迹最终都在第 32/41 步前后改用"直接点击数字 10"才成功退出循环。“一个值得留意的地方：验证要求"查看历史面试"（taskAudit.interviewTab == "h…

- **e0815.cainiao.cainiao_002** `hybrid_tools_0815_explore.HTV1ExploreCainiaoCainiao002`
  - 你：可用的 cainiao__list_stations 和 cainiao__search_packages 完全被忽视，与 hybrid 的设计初衷不符。 这个是因为没有设计对应的任务知道吗。以及"保温杯"是否需要手动清空默认值再输入，这个是啥玩意，这道题要不要填保温杯这件事是不是不清楚。。。这道题一般吧反正，照…

- **e0815.cainiao.cainiao_006** `hybrid_tools_0815_explore.HTV1ExploreCainiaoCainiao006`
  - 你：题面描述的行为路径在现实中稍显不自然。这一点是对的，之前其他题说过了。希望可以改题面或者验证。

- **e0815.ctrip.ctrip_001** `hybrid_tools_0815_explore.HTV1ExploreCtripCtrip001`
  - 你：密码需要仔细确认。给一个统一的解法，最好还是要涉及到支付的，这样两个app间可以联动。

- **e0815.dida.dida_008** `hybrid_tools_0815_explore.HTV1ExploreDidaDida008`
  - 你：这个 false 值得确认是不是聚合逻辑把剪贴板那两个非正式字段也计入了。而且我发现他分享给了微信好友？这种错误应该也要算错，因为他做了我们没要求的而且会产生影响的操作，这是一个重要的点，其他题目也都需要检查是不是有这种情况。「买菜」部分由 `dida__search_tasks` + `dida__comple…

- **e0815.jingdong.jd_001** `hybrid_tools_0815_explore.HTV1ExploreJingdongJd001`
  - 你：我想用国家补贴买笔记本电脑，这个题面写错了吧，这不买手机吗。。卧槽这个分期不会ui又是坏的吧。。。这道题我真不知道咋改了说实话，怎么假装它确实错了呢

- **e0815.jingdong.jd_004** `hybrid_tools_0815_explore.HTV1ExploreJingdongJd004`
  - 你：最后一步支付方式切换失败导致整体失败」模式。照理来说不可以这样子。支付问题要统一解决。

- **S_shop_02** `bench200_flow.HTV1ShopThinkbookKapi`
  - 你：这道题貌似有问题啊，看看不改环境的情况下有办法补救吗

- **S_travel_12306_cal** `bench200_flow.HTV1Travel12306Cal`
  - 你：（年份写错，这个问题就很，对工具调用不友好说实话。

### 修判定（10）

- **v6.case_02** `hybrid_tools_v6.HTV6Case02`
  - 你：这个失败不是模型业务能力的问题，而是"工具调用不触发store写入"导致的基础设施缺口。，这个问题还是挺严重的？但是还是需要检查的就是，模型搜索了“全新”，如果商品字段带“全新”就搜不出来的话，这个算什么的问题？模型得到null之后为什么没有重新搜呢？之前经常遇到类似问题，模型搜索匹配经常匹配不上。以及判定时候为…

- **e0815.boss.boss_task_03** `hybrid_tools_0815_explore.HTV1ExploreBossBossTask03`
  - 你：若想让 hybrid 列真正有区分度，需要补一个能读写 session 消息或备注的工具。如果这个"必须走常用语路径"的约束是题面语义的一部分，验证需要额外检查（比如消息来源字段或操作日志），否则这个限定写在题面里但不被核查，属于验证盲区。这一题模型对验证的判断值得参考并修改，

- **e0815.boss.boss_task_14** `hybrid_tools_0815_explore.HTV1ExploreBossBossTask14`
  - 你：这道题啥意思，有问题是吗，semantic_verifier_contract` 这个 check 在 GUI 路上返回 `missing` 是啥意思，这道题查一下，然后看一下怎么把这任务改正一下。

- **e0815.cainiao.cainiao_004** `hybrid_tools_0815_explore.HTV1ExploreCainiaoCainiao004`
  - 你：这里验证需要做的补充有道理的。

- **e0815.dianping.dp_task_07** `hybrid_tools_0815_explore.HTV1ExploreDianpingDpTask07`
  - 你：判定实际只看 `dianping.checkins` 是否新增，两者不矛盾但题面的措辞让模型觉得必须导航到"我的打卡"界面才算完成，多出了冗余步骤压力。该任务没有 plus 路径（候选工具里没有打卡相关 API），GUI-only 是唯一通道，这符合题目定位。。这个也是这批任务的统一毛病，验证需要改，不能初始就p…

- **v6.case_25** `hybrid_tools_v6.HTV6Case25`
  - 你：这两个短语并不出现在题面里，是判定代码硬编码的，属于题面与验证之间的隐性约束。，这个赶紧修改吧。整个流程靠视觉推断凑出了正确结论，但路径非常不稳健。这个可能是我们想看到的对吧。这两条轨迹对比鲜明，适合作为"工具辅助大幅降低导航噪声、提升推理准确性"的例子，。这个要记录一下

- **e0815.jingdong.jd_003** `hybrid_tools_0815_explore.HTV1ExploreJingdongJd003`
  - 你：需要确认 `search_items` 的 filters 参数能写入 taskAudit，以及 GUI 路径下筛选点击也能触发同一字段的更新——否则 GUI 路径的筛选失败可能只是坐标问题，而 Hybrid 路径的失败则是工具参数设计没有逼迫模型传 filters。

- **e0815.jingdong.jd_006** `hybrid_tools_0815_explore.HTV1ExploreJingdongJd006`
  - 你：这里结果有问题的，验证改过。

- **e0815.keep.keep_task_01** `hybrid_tools_0815_explore.HTV1ExploreKeepKeepTask01`
  - 你：题面末尾要求"看看今天推荐练什么"，但 assertions 里完全没有对应的检查项。模型在 GUI-only 里直接 terminate 而不输出推荐内容，仍然判 success。这意味着"今天推荐"这个子任务在评测上是虚设的——它既不影响得分，也没有对应的状态字段可读。如果这个子任务有保留的必要，需要补一个验…

- **e0815.luckin.luckin_002** `hybrid_tools_0815_explore.HTV1ExploreLuckinLuckin002`
  - 你：只有 1 杯橙C、无备注字段、订单结构也不符合预期格式；Hybrid 轨迹里下单通过，`actual` 里有 `items: [{productId: orange-c, quantity: 2}]` 以及 `note` 字段，status 是 unpaid。两次跑出不同的下单结果，说明 Hybrid 里的纯 G…

## 2. 只写了批注、没点按钮的 37

今晚对的时候先补按钮。倾向已经写在字里。

- **S_local_movie_cal** `bench200_flow.HTV1LocalMovieCal`
  - 干净通过

- **S_local_coffee_kapi** `bench200_flow.HTV1LocalCoffeeKapi`
  - 如果用作论文例子，可以说明工具辅助对不同子任务的贡献是不均匀的：读类工具在界面信息可直接读取时增益有限

- **S_work_launch_cal** `bench200_flow.HTV1WorkLaunchCal`
  - 这道题题面可能要改一下吧，不然看陈昊上线时间有啥意义，他说是周五，题面应该改成，放在这天的下午三点即可

- **C25** `bench200_compose.HTV1ComposeDianpingCal`
  - 每次日历都错，因为这个导航确实有迷惑性。

- **G_can_buy** `bench200_compose.HTV1GatherCanBuy`
  - 这两条轨迹的对比是这套 bench 设计意图的直接体现：同一任务，GUI-only 需要逐屏滚动手工搜最大值，Hybrid 一次 API 调用拿到所有账单数据后在模型侧排序，效率差距明显。值得在论文里摊开作为「工具加速信息聚合类任务」的例子

- **G_spend** `bench200_compose.HTV1GatherSpendCompare`
  - 对基准构建的启发：这类「收集→比较→汇总落笔」的三段式任务是跨应用任务里最能体现工具调用价值的模板，值得多几道。 不过这个错误也是重复出现了好几次，其实意义不大了

- **G_weekend** `bench200_compose.HTV1GatherWeekend`
  - 猫眼这段值得记录：Hybrid 里模型找不到日历 App 来回滑了三次屏（step 9-11），在找到后直接调工具跳过了手动填写。工具的 `persisted: false` 返回表明草稿未落盘，模型随后点击右上角保存按钮让它落盘——这条工具+UI 的混合路径在 Hybrid 框架下正好展示了"工具准备 + 界面确认"的典型用法。

- **G_meet_pay** `bench200_compose.HTV1GatherMeetPay`
  - 又是日历这个陷阱。

- **C_nimbus_kapi** `bench200_more.HTV1ComposeNimbusKapi`
  - 流程完整但偏冗余（两次点击同一"0"键坐标，且依赖坐标猜键盘布局），健壮性依赖截图像素精度。但需两次调用才找到有效类目——这说明 prepare_bill_draft 对类目名称的容错性较弱，或"其他"在当前账本里确实不存在；对模型来说算一次合理的自我纠正。这两个点也是比较常见的了

- **G_nimbus_bal** `bench200_more.HTV1GatherNimbusBalance`
  - 比较简单，任务比较不真实其实

- **G_hotpot** `bench200_more.HTV1GatherHotpot`
  - 应该题目改成收藏，打卡这家店，或者买一个这家店的套餐？但是同步的来说，微博必须有这个店，就是两个app的数据得对上

- **G_typhoon** `bench200_more.HTV1GatherTyphoon`
  - 这个判定没啥问题吧，他看图获得天气也可以啊。关键差异在 step 21-23：模型在翻页失败后调出了系统搜索，输入"笔记"，找到了正确的 notes App。这个属于模型波动。整个 hybrid 轨迹展示了一个有代表性的模式：工具在信息提取和最终写入两端都发挥了作用，GUI 负责中间的导航和定位，分工明确。

- **G_shhz** `bench200_more.HTV1GatherShhz`
  - 验证侧可以明确要求 G 字头且票态为"有票"。揭示了纯界面操作时"看到什么就用什么"的局限。工具路径避开了界面滚动不足的问题，结果正确。失败原因明确（列表未完整浏览导致车次选错），而非偶发性崩溃，对 hybrid 工具价值的说明比较干净。

- **G_vivo_bal** `bench200_more.HTV1GatherVivoBalance`
  - 也可以吧，以后看一看这种问题全部都要改成再在系统笔记里写一下然后再写一下验证。之前有很多看一看问题呗。

- **G_hotel_bal** `bench200_more.HTV1GatherHotelBalance`
  - 简单题

- **G_friday_pay** `bench200_more.HTV1GatherFridayPay`
  - 让 Slack 消息写具体日期（如「7月10日」）而非「周五」，让模型自己判断那天是周几并在笔记里两者都写，这个改动可以应用的。最终 actual content 里有重复的「周五前付款」前缀。验证只看「含周五」「含200」，所以仍然通过，但内容并不整洁。步骤 16 的思考里模型自己察觉到了这个问题（「I notice the text was typed into the body, not the title」），但补救动作并不彻底。这个问题很重要需要改，之前有过，但是不知道怎么改。照理你输出的东西标题就应该在标题的地方。正文又重复一遍周五前付款是啥意思？任务改成标题写 周五前付款，剩下的改期情况和金额写正文。然后验证要检查正文不可以有周五前付款。这样这题失败率又提了，这符合预期

- **G_orange_movie** `bench200_more.HTV1GatherOrangeMovie`
  - 还行

- **G_xianyu_bal** `bench200_more.HTV1GatherXianyuBalance`
  - 普通题

- **G_didi_pickup** `bench200_more.HTV1GatherDidiPickup`
  - 太简单了。

- **G_listen_read** `bench200_more.HTV1GatherListenRead`
  - 同样在找 notes App 图标时绕了两次（先点到 contacts、再点到 sms）

- **C_pickup_cal** `bench200_more.HTV1ComposePickupCal`
  - 简单

- **v4.ctrip_02** `hybrid_tools_selfbuilt_v4.HTV1CtripV402ChangchunOrderIdinhand`
  - 这道题绝对验证有问题，按照sonnet说的改一下验证吧，我觉得她们应该做的是对的吧？检查一下？然后题面里面不要有括号里那种表述

- **e0815.cainiao.cainiao_003** `hybrid_tools_0815_explore.HTV1ExploreCainiaoCainiao003`
  - 这道题我怀疑到底能不能复制了

- **e0815.vipshop.vipshop-005** `hybrid_tools_0815_explore.HTV1ExploreVipshopVipshop005`
  - 题面可以改成美妆分类。，没关系。核心瓶颈是「在哪个 tab 能找到唇釉」这个空间定位问题，两条轨迹都靠穷举解决，hybrid 的工具（list_brands / search_items）本可以在这里提速，但模型没有使用。

- **e0815.xiaorichang.task_03** `hybrid_tools_0815_explore.HTV1ExploreXiaorichangTask03`
  - UI-only 轨迹报告 `success: true`，29 步完成，但从轨迹内容来看，模型实际上在步骤 10 点击日期后直接触发了默认打卡（变成棕色、出现+20动画），这道题验证严重缺少，这里应该失败的。其实题面稍微有点误导，不是打卡日志，而是笔记，题面可以改成隐晦一点的，发布一条“xxxx”，插入这个时间戳。这样这两条都会失败了

- **e0815.cainiao.cainiao_005** `hybrid_tools_0815_explore.HTV1ExploreCainiaoCainiao005`
  - 这种"把多个选项聚合进单次创建操作"的任务形态在商业 App 评测里具有代表性：步骤多但逻辑线性，判定字段离散，不同字段可能在不同 UI 层（物品弹窗、服务选项、交件偏好弹窗），。在一个已有值的输入框上 type("5") 变成 25，删退格又删不干净，连续多步在修错而非推进——最终步骤耗尽时订单处于未提交状态。如果这道题提供一个表单填写工具的话结果会好很多其实。但是还是先别改这个，因为基线还没有测。只能改验证。

- **e0815.boss.boss_task_11** `hybrid_tools_0815_explore.HTV1ExploreBossBossTask11`
  - 模型在 step 23 点了分享按钮，step 24 直接 terminate 而没有完成分享确认动作（GUI 轨迹是点了微信选项后进入微信就 terminate，Hybrid 是看到分享菜单就 terminate），系统没有收到完成回调，resultCode 停在 null。这是模型过早宣告任务完成的典型失误。，这个值得记录。社区昵称入口藏在「有了」Tab 的社区头像里，不在「我的」主页的常规编辑入口，，也增加了模型探索路径

- **e0815.xiaorichang.task_05** `hybrid_tools_0815_explore.HTV1ExploreXiaorichangTask05`
  - 它试图用 `long_press` 或 `swipe` 来模拟"长按拖动"，始终没有成效，最后在 GUI-only step 10/Hybrid step 16 改为点击了一个铅笔图标（坐标 `[770,490]` / `[780,490]`），进入"规划每日计划"模式后，通过某个点击（step 13 `[800,350]` / step 19 `[820,350]`）完成了习惯移动。题面要求的是"长按拖动"，但模型实际走的是编辑按钮路径，绕开了题目明确指定的交互手势。，这里没法验证啊，这个要明确提出来

- **e0815.meiyou.task-05** `hybrid_tools_0815_explore.HTV1ExploreMeiyouTask05`
  - 不把 inline hashtag 自动解析进 `topics` 字段，验证就会误判。`circleId: "gynec"` 也未在题面中提示圈子 ID。综合来看，题面与判定之间的对应关系太窄，不是路径无关的终态验证，而是要求模型碰巧复现一个隐藏字符串，这对"成败只看业务终态，不看路径"的原则构成违背。如果要留这道题，正文应该在题面里直接给出，或者验证放宽到"含痛经相关内容且挂在 gynec 圈子且 topics 含 #妇科健康"。。这道题验证明确有问题，必须改，这两题算对应该。除非你想出一个验证能让他们失败。。。

- **e0815.daysmatter.dm_008** `hybrid_tools_0815_explore.HTV1ExploreDaysmatterDm008`
  - 这个任务我很好奇了，到底可不可以做到，？？？

- **e0815.vipshop.vipshop-003** `hybrid_tools_0815_explore.HTV1ExploreVipshopVipshop003`
  - 其实这个是模型不知道成功状态是啥，一直在反复延续完成任务。

- **e0815.tencentvideo.tv003** `hybrid_tools_0815_explore.HTV1ExploreTencentvideoTv003`
  - 这道题我也一下子找不到想看和不想看的入口在哪，得确认一下。

- **v4.kapi_08** `hybrid_tools_selfbuilt_v4.HTV1KapiV408BreakfastSubcategoryAmount`
  - 这道题环境有明确bug，看上去有数据，点开具体早餐订单显示0元，不能怪模型，不知道咋改了。如果要验证就应该验证0元才对。不过他们最终也没有建立笔记，所以这道题保持判错。

- **v4.kapi_09** `hybrid_tools_selfbuilt_v4.HTV1KapiV409LargeExpenseFullscan`
  - 但step 5它导航到了"flomo"而不是"notes"，最终笔记写在了错误的应用里，`notes_note[1]`为null，判定失败。这是一个典型的"工具调用正确但收尾操作错误"案例——数据推理部分hybrid比GUI更高效（3步完成GUI需要10步的扫描），但最后一公里走错了路。

- **v4.broadcast_05** `hybrid_tools_selfbuilt_v4.HTV1BroadcastV405StateAddHighcountLowrating`
  - 这个任务不需要记笔记。这个提示词不需要写啊。题面容易制造非预期的认知负担，这个是预期内的，然后模型读不完整，也是预期内的。然后他有了工具反而会困在搜索里面而不是用gui去看，这个现象也值得拿来看一看型花了大量步骤（27次 `search_shows` 调用）用单字符穷举检索来试图覆盖全部节目，但 `search_shows` 是关键词匹配，不支持空查询枚举

- **v4.broadcast_11** `hybrid_tools_selfbuilt_v4.HTV1BroadcastV411QueryScanWeeklyLowcount`
  - 实际上节目是有的，但是苹果资料库里只会有自己已经订阅的节目。这是一个陷阱。值得拿出来讲。

- **v4.taobao_12** `hybrid_tools_selfbuilt_v4.HTV1TaobaoV412SoldOver10KScanQueryScanMismatch`
  - 我靠这个现象还挺搞笑的：3步直接ABORT，工具`taobao__search_items`一次都没调用。从思考内容看，模型在反复纠结"无法一次列出全部商品"这个约束，陷入了策略困境后放弃。这是一个有意思的反差：GUI模型因为能直接看到历史搜索记录而产生了行动冲动，Hybrid模型则因为工具约束更显式而过早判断任务不可完成。gui是最终结果是**正确方向、严重遗漏**，这个也是反复的问题

## 3. 后补批注按主张归入（接 55 那篇）

下面只收**后半夜 37 条**里有主张的。9/8 下午那 55 已经在 `bench215-已看55-论文点.md`。

### 1. 界面本身难

- **点评日历 ComposeDianpingCal**：每次日历都错，导航有迷惑性。接 Case75 日历陷阱。
- **GatherMeetPay**：又是日历陷阱。
- **NimbusKapi**：两次点同一「0」键、靠像素猜键盘。
- **ListenRead**：找 notes 误入 contacts / sms。接 Case03。
- **Boss11**：社区昵称藏在「有了」Tab 头像，不在「我的」。
- **唯品会 005**：唇釉在哪个 tab，两条都穷举；工具能提速但没调。
- **唯品会 003**：不知道成功态，反复续做。
- **淘宝 412**：GUI 看见历史记录就动手（方向对、严重遗漏）；Hybrid 觉得一次列不全直接 ABORT、工具一次没调。

### 2. 工具有用

- **GatherCanBuy**：GUI 逐屏找最大支出，Hybrid 一次拉账单再排序。你点头：论文可摊开。
- **GatherWeekend**：工具 `persisted: false` 后再点保存，工具准备 + 界面确认。
- **GatherTyphoon**：工具管提取和写入，GUI 管导航；看图读天气你认为判定没问题。
- **GatherShhz**：GUI 看第一屏用了 K 字头；工具避开滚动不足。可要求 G 字头且有票。
- **Kapi409**：推理 hybrid 更省（3 步 vs 10 步），收尾写进 flomo。接 Case03。
- **LocalCoffeeKapi**：读类工具在屏幕已能读时增益有限（不均匀）。

### 3. 工具在场但没用上

- **唯品会 005**：`list_brands` / `search_items` 没调。
- **淘宝 412**：Hybrid 困在「无法一次列出全部」策略里放弃。
- **播客 V405**：有工具反而困在 `search_shows` 单字符穷举，不会改用 GUI 看列表。

### 4. 工具 / 环境洞

- **Kapi408 早餐**：点开订单显示 0 元，环境 bug；你说若验就该验 0，但最终没建笔记，**保持判错**。
- **播客 V411**：资料库只有已订阅，是故意陷阱。
- **菜鸟 003**：你怀疑到底能不能复制。
- **Daysmatter 008**：你好奇到底能不能做到。
- **腾讯视频 003**：想看/不想看入口你也一时找不到，先确认环境。

### 5. 判定和题面对不齐

- **周五付款 GatherFridayPay**：标题/正文重复「周五前付款」。你要：标题写「周五前付款」，正文只写改期和金额，**正文不得再出现标题句**。本机判定已按这个收过一刀；linux-dev 干净树没有这刀。
- **WorkLaunchCal**：看陈昊上线时间没意义，改成「放在这天下午三点」。
- **GatherHotpot**：改成收藏/打卡/买套餐，且微博和店数据要对上。
- **GatherVivoBalance**：这类「看一看」以后都改成再写系统笔记并验笔记。
- **携程 V402**：你认 Sonnet，改判定；题面去掉括号里那种表述。
- **小日常 03**：默认点日期就打卡，验证太松，应失败；题面改成发布一条并插入时间戳。
- **小日常 05**：题面要长按拖动，模型走编辑按钮；手势验不了，要写明。
- **美柚 05**：判定绑了隐藏字符串 / circleId，路径无关原则被破坏；两条应算对，除非另写能让他们失败的验。
- **Cainiao005**：聚合表单有代表性；type 把 5 变成 25。先不改工具（基线未测），只能改验证。
- **BroadcastV405**：不需要记笔记，题面别写这句。

### 6. 多余副作用 / 题面笔误

- **Boss11**：点了分享就 terminate，过早宣告完成。

### 7. 协议

- **GatherSpendCompare**：收集→比较→落笔最能体现工具，但同类错已重复，不必再堆例子。
- **NimbusBalance**：简单、不真实。
- **DidiPickup / HotelBalance / OrangeMovie / XianyuBalance / PickupCal / LocalMovieCal**：你标了干净/简单/还行/普通，不当贡献。

### 8. 先不要写成贡献

- 简单题、重复日历坑、重复找 Notes、重复「第一屏」。
- Kapi408 环境 0 元：记录 limitation，不洗成分。

## 4. 你已经驳过 Sonnet 的

| 题 | Sonnet | 你 |
|---|---|---|
| Case09 | 日期/数据可能错 | 系统时钟固定七月，查询日期是对的 |
| Case14 | 内容冗余要收 | 当前宽松可接受；小红书纯文字本来那样，题面没规定发法 |
| Keep01 等「看看」 | 补字段 | 没落点就**算了**，不硬加 |
| 美柚 05 | （分析判定过窄） | 你同意必须改验，两条应算对 |
| 携程 V402 | 改验 | 你同意按 Sonnet 改 |

## 5. 还没批的 123

Sonnet 卡都在 `artifacts/bench215-official-insight/cards.json`。今晚若只能抽，优先：GUI/Hybrid 对错不一致、Sonnet 写了「验证/基础设施」、以及带「看看/确认/去某页」的题面。

未批 123 道。按看台短名：

| 短名 | GUI | Hybrid |
|---|---|---|
| C01 | 挂 | 挂 |
| C02 | 过 | 过 |
| C04 | 过 | 过 |
| C05 | 挂 | 过 |
| C06 | 过 | 过 |
| C07 | 过 | 过 |
| C08 | 过 | 过 |
| C10 | 挂 | 挂 |
| C13 | 过 | 过 |
| C14 | 过 | 过 |
| C15 | 挂 | 过 |
| C16 | 过 | 过 |
| C17 | 挂 | 过 |
| C_bcz_flomo | 过 | 过 |
| C_boss_cal_day | 过 | 过 |
| C_cake_cal | 过 | 过 |
| C_pdd_buy_kapi | 过 | 过 |
| C_slack_meet | 挂 | 过 |
| C_suning_kapi | 过 | 过 |
| C_vip_kapi | 挂 | 过 |
| C_xianyu_xrc | 过 | 过 |
| C_youku_todo | 过 | 过 |
| S_finance_01 | 过 | 过 |
| Shop_pdd_kapi | 挂 | 挂 |
| Soc_broadcast_xhs | 过 | 过 |
| Soc_keep_dumbbell | 过 | 过 |
| Soc_keep_mat | 挂 | 过 |
| Soc_weibo_cal | 过 | 挂 |
| Work_boss_greet | 过 | 过 |
| Work_drive_dida | 过 | 过 |
| Work_drive_meet | 过 | 挂 |
| Work_drive_slack | 过 | 过 |
| Work_nimbus_slack | 过 | 过 |
| Work_wangsiyu_slack | 过 | 过 |
| alipay_06 | 挂 | 挂 |
| e0815.ctrip.ctrip_006 | 过 | 过 |
| e0815.didi.didi_004 | 过 | 过 |
| e0815.didi.didi_006 | 挂 | 挂 |
| e0815.douban.task_07 | 挂 | 过 |
| e0815.fanqietodo.T06 | 过 | 过 |
| e0815.fanqiexiaoshuo.T06 | 过 | 过 |
| e0815.jingdong.jd_005 | 过 | 过 |
| e0815.luckin.luckin_001 | 挂 | 挂 |
| e0815.luckin.luckin_003 | 过 | 过 |
| e0815.luckin.luckin_004 | 过 | 过 |
| e0815.mail.mail-task-01 | 过 | 挂 |
| e0815.mail.mail-task-03 | 过 | 过 |
| e0815.mail.mail-task-04 | 过 | 过 |
| e0815.maoyan.t01 | 过 | 挂 |
| e0815.maoyan.t02 | 过 | 过 |
| e0815.maoyan.t03 | 过 | 挂 |
| e0815.maoyan.t04 | 挂 | 挂 |
| e0815.maoyan.t05 | 挂 | 挂 |
| e0815.pinduoduo.pdd_001 | 过 | 过 |
| e0815.pinduoduo.pdd_002 | 挂 | 挂 |
| e0815.pinduoduo.pdd_004 | 过 | 过 |
| e0815.slack.slack_task_01 | 过 | 过 |
| e0815.slack.slack_task_03 | 过 | 过 |
| e0815.slack.slack_task_06 | 过 | 过 |
| e0815.suning.task-01 | 挂 | 挂 |
| e0815.suning.task-02 | 过 | 过 |
| e0815.suning.task-06 | 过 | 过 |
| e0815.suning.task-07 | 过 | 过 |
| e0815.tbsg.tbsg_t01 | 挂 | 挂 |
| e0815.tbsg.tbsg_t02 | 挂 | 挂 |
| e0815.tbsg.tbsg_t04 | 挂 | 挂 |
| e0815.tbsg.tbsg_t05 | 挂 | 挂 |
| e0815.tbsg.tbsg_t06 | 挂 | 挂 |
| e0815.tbsg.tbsg_t07 | 挂 | 挂 |
| e0815.tbsg.tbsg_t08 | 过 | 过 |
| e0815.tencentvideo.tv005 | 挂 | 挂 |
| e0815.vipshop.vipshop-001 | 挂 | 挂 |
| e0815.vipshop.vipshop-002 | 挂 | 过 |
| e0815.vipshop.vipshop-004 | 过 | 过 |
| e0815.weibo.wb_task_01 | 过 | 过 |
| e0815.weibo.wb_task_07 | 过 | 过 |
| e0815.weibo.wb_task_08 | 过 | 过 |
| e0815.xianyu.xianyu_001 | 过 | 过 |
| e0815.xianyu.xianyu_002 | 挂 | 过 |
| e0815.xianyu.xianyu_005 | 挂 | 挂 |
| e0815.xianyu.xianyu_006 | 过 | 过 |
| e0815.xianyu.xianyu_008 | 过 | 过 |
| e0815.xianyu.xianyu_009 | 过 | 过 |
| e0815.xianyu.xianyu_013 | 挂 | 挂 |
| e0815.xiaorichang.task_01 | 过 | 过 |
| e0815.youku.yk_task_01 | 挂 | 过 |
| e0815.youku.yk_task_04 | 挂 | 挂 |
| kapi_05 | 过 | 过 |
| railway12306_01 | 挂 | 挂 |
| railway12306_03 | 挂 | 挂 |
| railway12306_06 | 过 | 过 |
| v4.broadcast_03 | 过 | 过 |
| v4.broadcast_04 | 挂 | 过 |
| v4.broadcast_07 | 挂 | 挂 |
| v4.broadcast_10 | 挂 | 挂 |
| v4.ctrip_01 | 过 | 过 |
| v4.ctrip_03 | 过 | 过 |
| v4.ctrip_06 | 过 | 过 |
| v4.jd_01 | 挂 | 过 |
| v4.kapi_01 | 过 | 过 |
| v4.taobao_03 | 挂 | 过 |
| v6.case_27 | 挂 | 挂 |
| v6.case_28 | 挂 | 挂 |
| v6.case_32 | 挂 | 过 |
| v6.case_35 | 挂 | 挂 |
| v6.case_36 | 过 | 过 |
| v6.case_40 | 过 | 过 |
| v6.case_41 | 挂 | 挂 |
| v6.case_51 | 过 | 过 |
| v6.case_52 | 挂 | 挂 |
| v6.case_53 | 挂 | 挂 |
| v6.case_54 | 过 | 过 |
| v6.case_55 | 过 | 过 |
| v6.case_56 | 挂 | 挂 |
| v6.case_57 | 过 | 挂 |
| v6.case_58 | 过 | 过 |
| v6.case_59 | 过 | 过 |
| v6.case_62 | 过 | 过 |
| v6.case_63 | 过 | 过 |
| v6.case_68 | 过 | 过 |
| v6.case_69 | 挂 | 挂 |
| v6.case_73 | 挂 | 过 |
| v6.case_74 | 过 | 过 |
