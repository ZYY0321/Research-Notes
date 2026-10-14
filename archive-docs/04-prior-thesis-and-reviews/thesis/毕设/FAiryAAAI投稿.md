Fairy: Interactive Mobile Assistant to Real-world Tasks
Abstract（修正V1）
精细校对（GYN）👇@郭祎凝 
大型多模态模型的研究大大的推动了移动图形用户界面（GUI）智能体领域的发展。然而，现有工作仍难以胜任应用界面多样、用户需求模糊多变的真实世界场景，依赖模型“常识”驱动的“端到端”方法在长尾应用中屡屡失效，缺乏用户交互也导致智能体总是自行其是，无法令用户满意。我们提出了 Fairy——能在执行过程中持续积累 App 知识并自我进化的交互式多智能体手机助手。Fairy 通过三个核心模块保障了跨应用协作、交互式执行和持续学习的能力：Global Task Planner在跨 App 视角下拆解用户任务；App-Level Executor依据长短期记忆将任务进一步细化为子目标与原子操作，通过两个环路（Loop）中的四类核心智能体实现高精度的操作与实时的用户沟通；Self-Learner在任务结束后总结知识，持续扩充 App Map与 App Tricks。我们进一步构建了面向更真实场景的评测基准RealMobile-Eval并制定了一系列评估指标，并利用LMM智能体代替人类参与结果评估。实验显示，在ChatGPT-4o骨干模型上，Fairy 相较最新方法取得了平均XX%的绝对准确率提升，推理时延缩短XX%，并展现优异的长程任务鲁棒性与自我进化能力。代码见xxx。 
1 Introduction
智能手机已经深刻的影响了我们的生活方式，但智能手机从未做到“智能”。大语言模型的进展使得这不再是幻想，基于LMM衍生的GUI智能体，如AutoDroid、AppAgent、MobileAgent等工作已经取得了至关重要的进展——根据人类的指令控制手机应用完成任务。
尽管取得了这些进步，但它们尚未完全克服真实世界中执行用户任务所面临的挑战。首先，用户有着复杂多变的需求，且往往难以一次性提出。用户通常会基于一个大致想法（例如，我希望点一份麦当劳汉堡），再在执行中补全额外需求（例如，麦香鱼套餐，可乐不加冰），一次性的接受用户任务并执行往往会偏离用户真实需求（+MobileAgent E，MOBA）。其次，移动端应用的页面与功能通常会持续更新，而且其长尾效应不可忽视。依赖模型微调以期让模型“记住”应用，从而基于模型“常识”实现更准确规划与操作的做法是有局限的（+基于微调的仨）。最后，糟糕的智能体设计，例如缺乏设计的上下文、未分层的计划、不准确的屏幕感知和混乱的知识库，使得许多Mobile Agent在真实世界的任务中的表现被显著削弱，糟糕的体验使得用户对其丧失兴趣和信心。
为了应对这些挑战，我们提出了Fairy，这是一种能够在执行任务中持续积累App知识的交互式多智能体手机助手。Fairy主要由三个层级构成：在高层，我们将用户任务分解为一系列在单个App中执行的子任务；在中层，我们结合特定App的知识将任务进一步分解为多个子目标；在低层，我们将子目标转换到具体的原子行动和参数。分层决策模拟了人类对任务的细化过程，使智能体可针对性的提取不同层次、不同应用的知识，从而有效提升计划质量。
为实现分层规划，我们设计了全局计划器（Global Planner）负责制定高层跨App协作策略，App级执行器（App-Level Executor）负责制定中、低层单App执行策略并做出动作。其中，App级执行器由两个包含多个智能体与工具的“环路”构成：“动作执行环路”负责“反思行动并重新计划”、“决策原子行动”、“执行动作”与“感知屏幕变化”；在执行时，如果发现当前需求模糊，则进入“用户交互环路”，由其向用户指出模糊之处并引导用户补全额外需求。这使得用户可渐进的澄清需求，而无需担心智能体在模糊空间下的自作主张。
Fairy还包括两类持续积累App知识的学习器（Learners），它们将基于操作过程中积累的短时记忆，从此前的执行或试错中吸取经验与教训（App Tricks），并持续积累App的操作与页面跳转逻辑（App Map）。这些信息将形成针对特定App的长期记忆，在未来由相关的智能体通过RAG等方式检索获得。
为更好的理解Fairy，我们在图1展示了一项真实世界的复杂任务，该任务需要多个应用程序中协作工作，且面临模糊且多变的用户需求。
为了评估Fairy的实际能力，我们专门设计了首个用于评估交互式Mobile智能体的基准——RealMobile-Eval。与此前的基准(+3)相比，RealMobile-Eval的任务更接近于真实场景下的用户行为，且首次基于LMM智能体模拟了用户与手机助手的渐进式交互；我们选取的手机应用也更真实且复杂，它们带来的挑战将显著高于功能专一的特定应用。
我们考虑了多种先进的评估指标，并使用LMM智能体进行结果评估与人工检查的方式以确保得分可靠。实证结果表明，Fairy与之前最先进的方法相比，实现了33.7%的用户需求完成率增幅，而冗余步骤率则下降了58.5%。
总之，本文有如下贡献：
- 我们设计并开源了一个持续进化的交互式的手机智能助手Fairy，它可以通过与用户沟通来持续跟进用户真实意图，并通过在使用中持续学习页面组件知识而不断提升自身能力。
- 我们提出了一种全新的评估基准RealMobile-Eval，包含一系列真实世界任务和评估指标，可以有效评估交互式手机智能体的性能。
- 我们进行了广泛的实证测试，证明了Fairy在各种智能手机应用、真实世界场景中的有效性。据我们所知，Fairy是迄今为止表现最好的移动端GUI智能体之一。
有关Fairy项目的更多信息，包括开源代码仓库与评估基准，请参考我们的附加材料。
[图片]
图注：Fairy执行真实世界任务的案例。Fairy正在执行由用户提出的“Check my today's schedule and order me a McDonald's hamburger after the meeting.”任务：首先由它的Global Planner做出全局计划，并将App级的任务分配给App-Level Executor。根据计划，App-Level Executor将先在Google Calendar获取用户的日程并确定会议结束时间，然后根据这一时间在McDonalds App完成点餐。在点餐时，Re-Planner发现用户只给出了模糊的点餐需求，因此它将Aciton Loop切换为Interaction Loop，User Interactor与用户交互以确定用户希望吃哪种汉堡。在得到用户明确的答复后，Action Decider决策了点击动作，将汉堡加入购物车。在计划、执行过程中，它们使用了长期记忆提供的App Map和App Trick，这帮助了它们避免错误和完成操作。我们在实验选取30个类似的真实世界任务进行了测试，实验证明Fairy在复杂的现实世界任务中表现优于之前的先进方法。
精细校对（GYN）👆@郭祎凝 
2 Motivating Examples（修正V2）
精细校对（GYN）👇@郭祎凝 

最新版👇@郭祎凝 
我们将通过一个网络点餐案例来进一步说明在真实世界中Mobile智能体面临的关键挑战，现有工作的局限性，以及我们的动机。现在，用户希望智能体使用外卖软件“点一份麦当劳汉堡外卖”。智能体将面临以下挑战：
- 模糊用户指令挑战：我们发现许多智能体依赖用户给出非常确切的指令，例如使用麦当劳App，在离我1.6km的那家门店，点一份麦满分可乐套餐，外送到家，请附带餐具，可乐不放冰”。而事实上，用户难以在下达任务前完整的考虑任务中的所有细节，开始时用户往往只有一个高层的想法，需要在与手机的交互中逐步做出决定（例如，决定具体吃什么汉堡）。此外，我们还发现大量工作为了确保正确率采取了鲁莽且直接的措施——在用户需求模糊或面临多个选项时，要求大模型替代人类做出选择。这确实可以帮助提升任务的正确率，但却与解决真正的用户要求相去甚远——随意的购买麦当劳的任意汉堡来敷衍任务会使得用户感到非常沮丧。要应对这一挑战，智能体就必须在执行任务时主动发现用户指令中的模糊性、收集必要信息并与用户及时交互。
- 组件识别与操作挑战：在点餐时，智能体通常需要使用搜索栏查找用户要求的餐品，它需要准确识别出它的位置并执行四个动作（Action）：点击输入框、清空输入框、输入内容和点击搜索按钮。我们发现，许多采取了基于“视觉+提示”策略的智能体在“提示”环节会将“搜索栏”拆解为图标和文字，使得其无法正确识别搜索栏，进而做出直接点击搜索按钮等错误操作；由于缺乏经验，部分智能体无法意识到搜索栏可能已预先输入了广告，往往因未能删除广告而落入陷阱。此外大部分智能体在此步骤上表现迟缓：执行搜索包括的四个动作需要消耗四轮非必要的“规划-执行-感知-反思”的循环，而这些动作根本不需要反思和重新规划。要应对这一挑战，智能体就必须能够增强对App页面中组件的认识，包括组件的位置与功能、操作技巧等方面。
- 复杂路径规划挑战：点餐软件中往往充斥着各类广告，在点餐时，许多智能体的目光常常会被首页推荐的广告吸引，从而走向错误的广告页面。幸运的是，很多具备自我纠错功能的智能体可以意识到错误并及时走入正确的路径；不幸的则是，当下次再遇到这类广告时，它们还是会再次中招。此外，还有部分智能体在某些情况下完全无法意识到它们正行于错误之路，因为这条路径也能完成用户的任务——只不过可能大大威胁用户的钱包（例如在广告的诱导下购买了昂贵的套餐、优惠月卡或者几十张预付费券）。要应对这一挑战，智能体就必须能够增强对App页面跳转逻辑的认知，提前预知操作可能带来的结果并做出正确的计划。
Fariy is all you Need！对于挑战A，Fairy设计了“动作执行”和“用户交互”两个环路，将动作执行中遇到的可选选项（例如当前有哪几家麦当劳门店，正在出售哪些汉堡）提供给用户决策，从而避免了智能体自行其是的错误。对于挑战B，Fairy解析了可访问树，基于此前学习的组件知识和使用技巧可以精确定位并清除预填充广告；同时，在低层，fairy可依据子目标一次性决策多个原子行动，使得案例B的四个动作得以一次性执行。对于挑战C，Fairy可利用此前学习的应用页面跳转逻辑来发现潜在的广告路径，从而提前避开。总的来说，Fairy通过“在用中学”积累了关于App的“知识”和“经验”，这使得其在进行计划时有据可依；通过可访问树对页面结构与组件进行分析和在截屏使用SoM标注提升了操作的准确率，也使得页面知识可以被积累。这些原因和Fairy本身优秀的分层架构设计，使得Fairy在真实世界的任务中取得了更好的表现。
——————————————————————————————————————————————
Food ordering is one of the most common tasks users ask mobile agents to handle, and it highlights the challenge of dealing with \textbf{vague and evolving user instructions}. Typically, a user might issue a brief instruction such as \textit{Get a McDonald’s burger delivered}'' rather than providing a detailed request like \textit{Open the McDonald’s app, select the store 1.6 km away, add a McMuffin and Coke set, and have it delivered to my home and Coke no ice.}” Users usually start with a general idea and refine their choices—such as which burger to order—through ongoing interaction.
Therefore, an effective agent must identify the vague in the initial instruction, gather the necessary information, and ask the user relevant follow-up questions. Unfortunately, many approaches try to achieve accuracy by taking a straightforward action. When facing vague user requests or multiple options are available, the LMM makes decisions on behalf of the user. While this may improve task completion metrics, it fails to meet real user needs. Arbitrarily purchasing any McDonald’s burger just to complete the task could lead to significant user frustration.

One of the most common steps in executing user tasks is \textbf{performing a search}. The agent must accurately locate the search bar and complete four sub-steps: tap the input field to gain focus, clear any prefilled ads (if necessary), type the search query, and hit the search button. Although this may seem straightforward, many approaches struggle for several reasons: (1) In real scenarios, the search bar often comes prefilled with ad text, and the agent fails to recognize that it must delete this text before typing and searching; (2) Many agents use a "vision + prompt" strategy, where the prompt encoder treats the search bar as two separate elements—an icon and a label. As a result, the agent may not notice the ad text, may not recognize the region as typeable, or might even click the search button first and fall into the ad trap. Additionally, multi-agent frameworks often perform sluggishly at this step. The four sub-steps consume four complete ``Plan–Execute–Perceive–Reflect'' loops, but these loops are largely ineffective since the actions seldom generate errors that require reflection or perception.

【1】以下案例可进一步说明在真实世界中Mobile智能体面临的关键挑战，现有工作的局限性，以及我们的动机。我们还将在研究主页展示这些案例的进一步详情。
【2】案例A-用户点餐任务：点餐可能是用户最常需要智能体完成的任务之一，“用户需求多变且表达不清”的特点在这一任务上深有体现。正常来说，用户会给出例如“点一份麦当劳汉堡外卖”这样的指令，而不是“使用麦当劳App，在离我1.6km的那家门店，点一份麦满分可乐套餐，外送到家，请附带餐具，可乐不放冰”。用户难以在下达任务前完整的考虑任务中的所有细节，开始时用户往往只有一个高层的想法，需要在与手机的交互中逐步做出决定（例如，决定具体吃什么汉堡）。这需要智能体在执行任务时主动发现用户指令中的模糊性、收集必要信息并与用户及时交互。然而，我们发现大量工作加为了确保正确率采取了鲁莽且直接的措施——在用户需求模糊或面临多个选项时，要求大模型替代人类做出选择。这确实可以帮助提升任务的正确率，但却与解决真正的用户要求相去甚远——随意的购买麦当劳的任意汉堡来敷衍任务会使得用户感到非常沮丧。
【3】案例B-搜索步骤：在执行用户任务时，最常见的步骤之一就是执行搜索。智能体需要准确识别出搜索栏的位置并执行四个子步骤：点击输入框获取焦点，清空其中的广告（如需要），输入内容，点击搜索按钮进行搜索。这听起来轻而易举，但许多工作加在此遇到了滑铁卢，其原因是多样的：1）在真实任务中，搜索栏中往往已经预先输入了广告，智能体未能意识到需要先删除它们才能输入并搜索；2）许多智能体采取了基于“视觉+提示”的策略，“提示”环节常常忽略“搜索栏”这一整体组件而是将它们分别输出为图标和文字，这导致智能体未能意识存在广告、没有意识到当前区域可以进行输入或认为应当先点击搜索按钮（而这又落入了预先输入广告的陷阱之中）。此外，许多多智能体在此步骤上表现迟缓：搜索步骤包括的四个子步骤需要消耗四轮“规划-执行-感知-反思”的循环，事实上，这些循环被极大的浪费，因为这些步骤根本不会产生需要反思和重新规划的错误，也不会带来需要感知的内容。
[图片]
【4】案例C-广告迷踪：在真实世界中，App中的广告总是令人防不胜防，不胜其烦，智能体也并未幸免于难。美团（Meituan）是一款著名的外卖App，当用户试图要求智能体使用Meituan“点一份麦当劳汉堡”时，许多智能体加的目光常常会被首页推荐的广告吸引，从而走向错误的广告页面。幸运的是，很多具备自我纠错功能的智能体加可以意识到错误并及时走入正确的路径；不幸的则是，当下次再遇到这类广告时，它们还是会再次中招。此外，还有部分智能体在某些情况下完全无法意识到它们正行于错误之路，因为这条路径也能完成用户的任务——只不过可能大大威胁用户的钱包（例如在广告的诱导下购买了昂贵的套餐、优惠月卡或者几十张预付费券）。
[图片]
【5】Fariy is all you Need！对于案例A，Fairy设计了“动作执行”和“用户交互”两个环路，将动作执行中遇到的可选选项（例如当前有哪几家麦当劳门店，正在出售哪些汉堡）提供给用户决策，从而避免了智能体自行其是的错误。对于案例B，Fairy解析了可访问树，基于此前学习的组件知识和使用技巧可以精确定位并清除预填充广告；同时，在低层，fairy可依据子目标一次性决策多个原子行动，使得案例B的四个子步骤得以一次性执行。对于案例C，Fairy可利用此前学习的应用页面跳转逻辑来发现潜在的广告路径，从而提前避开。总的来说，Fairy通过“在用中学”积累了关于App的“知识”和“经验”，这使得其在进行计划时有据可依；通过对页面结构与组件进行文本化描述提升了操作的准确率，也使得页面知识可以被积累。这些原因和Fairy本身优秀的分层架构设计，使得Fairy在真实世界的任务中取得了更好的表现。
精细校对（GYN）👆@郭祎凝 
由于过长已经废弃👇
对于案例A，Fairy设计了“动作执行”和“用户交互”两个环路，有效的缓解了用户需求模糊而智能体自作主张产生的错谬。用户可以在与智能体的交互中获取任务中的可选选项（例如当前有哪几家麦当劳门店，正在出售哪些汉堡），做出决策并告知智能体执行。
对于案例B，Fairy基于可访问树获取页面结构信息，联合在此前任务执行中通过学习而积累的页面组件知识，为智能体提供页面结构与组件的文本化描述。因此，Fairy可以准确的获知搜索框的位置，以及其中填充的广告。此外，基于长期记忆中的App Tricks提供的一般性规则，Fairy也可以理解其应在搜索前清空输入框。同时Fairy的分层结构允许在低层将子步骤转换为多个原子行动，使得案例B的四个子步骤可以一次性执行。
对于案例C，基于长期记忆中App Map提供的指引，Fairy可以准确的发现当前的路径将导向一个广告，从而有效规避落入广告陷阱。总的来说，Fairy通过“在用中学”积累了关于App的“知识”和“经验”，这使得其在进行计划时有据可依；通过对页面结构与组件进行文本化描述提升了操作的准确率，也使得页面知识可以被积累。这些原因使得Fairy在真实世界的任务中取得了更好的表现。
由于过长已经废弃👆
3 Our Approach: Fairy
图X中描述了Fairy的主要组件和核心工作流程：
[图片]
由于空间不足，不能放在论文正文里，废弃👇作为标准名称供参考：
Notation
Description
智能体与工具 Agents & Tools

$$\mathcal{A}_{GRP}$$
全局反思-计划器 Global Re-Planner.
$$\mathcal{A}_{AD}$$
原子动作决策器 Atomic Action Decider.
$$\mathcal{A}_{RP}$$
反思-计划器 Re-Planner.
$$\mathcal{A}_{CE}$$
关键信息提取器 Key Context Extractor.
$$\mathcal{A}_{I}$$
用户交互器 User Interactor.
$$\mathcal{AL}_{AM}$$
App技巧学习器 App Trick Learner.
$$\mathcal{AL}_{AT}$$
App知识图谱学习器 App Map Learner.
$$\mathcal{T}_{AE}$$
原子动作执行器 Atomic Action Executor.
$$\mathcal{T}_{SP}$$
屏幕信息感知器 Screen Perceptor.
$$\mathcal{T}_{UT}$$
用户聊天室 User Talker.
$$\mathcal{T}_{APP}$$
应用信息管理器 App Info Manager
$$\mathcal{T}_{TM}$$

短时记忆 Short Time Memory

$$Ins^j$$
用户说明 User, $${Ins^j}=\{Ins_O^j, Ins_U^j, Ins_L, k_R^j\}$$.
$$Ins_O^j$$
任务原始说明 Task Original Instruction (for task j)
$$Ins_{U}^j$$
用户更新说明 User Updated Instruction (for task j)
$$Ins_{L}$$
用户语言 User Languages
$$k^j_R$$
关键上下文的抽取请求 Key Context Extraction Request (for task j)
$$p^t$$
整体计划 Overall Plan, $$p^t=\{p_T^t, p_{Op}^t, p_{Sg}^t,i_{T}^t,i_{Typ}^t\}$$.
$$p_T^t$$
计划思考 Plan thought
$$p_{Op}^t$$
整体计划 Overall plan
$$p_{Sg}^t$$
子目标 Sub goal
$$i_{Tt}^t$$
t时的用户交互类型思考 User interaction type thought at time t.
$$i_{Typ}^t$$
t时的用户交互类型 User interaction type at time t.
$${a}^t$$
t时的动作 Action at time t, $$a^t=\{a_T^t, a_{As}^t, a_{Exp}^t,i_{J}^t\}$$.
$$a_T^t$$
t时的动作思考 Action thought at time t.
$$a_{As}^t$$
原子动作序列 Atomic actions
$$a_{Exp}^t$$
t时的动作预期 Action expectation at time t.
$${i}_{J}^t$$
t时的用户交互判断 User interaction judgment at time t.
$$s^{t}$$/ $$s^{t'}$$

t时的屏幕信息，其中$$t'$$代表动作执行之后的屏幕 
Screen information at time t, $$s^t=\{s_{Act}^t, s_{Info}^t, s_{Pic}^t\}$$, where $$t'$$stands for the screen after the action has been executed.
$$s^{t}_{Act}$$
t时的App活动名 App activity name at time t.
$$s^{t}_{Info}$$
t时的屏幕感知信息 Screen perception informations at time t.
$$s^{t}_{Pic}$$
t时的屏幕截屏图片 Screenshot picture at time t.
$$r^t$$
t时的反思结果 Reflect result at time t, $$r^t=\{r_{Ar}^t, r_{Ec}^t, r_{Ps}^t\}$$.
$$r^t_{Ar}$$
t时的动作结果 Action result at time t.
$$r^t_{Ec}$$
t的潜在错误原因 Error potential causes at time t.
$$r^t_{Ps}$$
t时任务进度 Progress status at time t.
$$k^t$$
t时关键上下文 Key Contexts at time t.
$$i^n$$

$$i_{T}^{nk}$$
第n轮第k次用户交互的思考 kth Interaction thought at round n.
$$i_{S}^{nk}$$
第n轮第k次用户交互的状态 kth Interaction status at round n.
$$i_{P}^{nk}$$
第n轮第k次用户交互的用户提示词 User prompt for kth interaction at round n.
$$i_{R}^{nk}$$

$$i_{R}^{n}$$
第n轮用户交互的最终用户回应 User responses for interaction at round n.
$$App_{Pkg}$$

$$App_{Desc}$$

$$g$$

$$g^{j}_{Op}$$
全局计划 Global Plan
$$g^{j}_{T}$$

$$g^{j}_{St}$$
子任务 Sub Task，$$g^j_{St}=\{Ins^j_{\hat O},App^j_{Pkg},k^j_R\}$$
$$g^{j}_{Dc}$$
传递的上下文信息 Delivered Key Context
长时记忆 Long Time Memory

$$T^q_{Plan}$$
查询为q时的计划技巧提示
$$T^q_{Exec}$$
查询为q时的执行技巧提示
$$T^q_{Err}$$
查询为q时的执行错误提示
3.2 Global Task Manager
如图X所示，Global Task Manager是将用户指令拆解为App级任务并管理App-Level Executor生命周期的核心。
[图片]
Global Planner（$$\mathcal{A}_{GP}$$）负责把用户的复杂指令拆解为多个单应用任务，分为直接计划和调整两个阶段：
1) 直接计划：$$\mathcal{A}_{GP}$$依据用户指令$$I$$和用户手机中已安装应用元数据$$\{AM^\tau\}^ m_{\tau=0}$$，制定全局计划$$G$$，并确定执行首个子任务。
$$G^1=\mathcal{A}_{GP}(I,\{AM^\tau\}^ m_{\tau=0})$$
$$G$$包括整体计划$$G_{op}$$、将在接下来执行的子任务$$G_{st}$$和执行此任务需要依赖的上下文信息$$G_{c}$$。其中子任务$$G_{st}$$包括未加工任务指令$$I_{T'}$$、上下文抽取请求$$G_{cr}$$和对应任务的App包名$$AM_{p}$$。
2) 调整：$$\mathcal{A}_{GP}$$将a. 检查此前任务的执行结果；b. 根据执行结果更新任务进展，或调整此前的任务规划。$$\mathcal{A}_{GP}$$依据用户指令$$I$$和经过多轮动作循环与用户交互循环的App-Level Executor的轨迹记录$$\mathcal{M}_{T}$$，判断任务结果是否符合预期；然后根据检查结果和此前的全局计划$$G$$，更新整体计划$$G_{op}$$并确定下一个子任务$$G_{st}$$，同时总结需要传递至下一个子任务的上下文信息$$G_{c}$$。
$$G^{j+1}=\mathcal{A}_{GP}(I,\mathcal{M}_{T}^j,G^{j})$$
App Metadata Manager （$$\mathcal{T}_{AM}$$）是一个工具，用于发现、维护并摘要用户设备$$\mathcal{P}$$上已安装应用的元数据，为$$\mathcal{A}_{GP}$$提供可靠的App能力基表，这些信息将随着用户手机应用变动动态更新。
$$\{AM^\tau_{p},AM^\tau_{d}\}^m_{\tau=0}=\mathcal{T}_{AM}(\mathcal{T}_{AE}.ListApp(\mathcal{P}))$$
Task Manager （$$\mathcal{T}_{TM}$$）是一个工具，用于维护由$$\mathcal{A}_{GRP}$$计划的子任务的生命周期，在子任务切换时协助进行上下文传递。
$$\mathcal{T}_{TM}$$在接收当前$$G$$后，将调用$$\mathcal{T}_{AE}.StartApp(\mathcal{P}，AM_{p})$$启动应用。同时，$$\mathcal{T}_{TM}$$利用LLM基于上下文信息$$G_{c}$$对未加工任务指令（Raw Task Instruction）$$I_{T'}$$进行改写。在任务发布后，$$\mathcal{A}_{RP}$$将激活并开始处理任务。
$$I^j_{T} = \mathcal{T}_{TM}(I^j_{T'}, G_{c}^{j})$$
3.3 App-Level Executor 
App-Level Executor是执行由Global Task Manager规划的App级任务的核心，包括Action Loop和Interaction Loop两个核心循环。
3.3.1 Action Loop
Action Loop是执行任务的核心循环，其流程如图X所示。
[图片]
Planner（$$\mathcal{A}_{RP}$$）负责根据$$\mathcal{A}_{GP}$$制定的任务制定具体的、由一系列子目标组成的执行计划。与$$\mathcal{A}_{GP}$$类似，$$\mathcal{A}_{RP}$$也分为直接计划和调整两个阶段：
1) 直接计划：$$\mathcal{A}_{RP}$$依据任务指令$$I_T$$、首个屏幕感知信息$$S^0$$和技巧提示$$T^{I_T}_p$$，制定计划$$P$$，并确定执行首个子目标。
$$P^1=\mathcal{A}_{RP}(I_T,S^{0},T^{I_T}_{p})$$
$$P$$包括整体计划$$P_{Op}$$、将在接下来执行的子任务$$P_{Sg}$$。
2) 调整：$$\mathcal{A}_{RP}$$将a. 检查动作执行的结果；b. 根据执行结果更新任务进展，或调整此前的任务规划。首先，$$\mathcal{A}_{RP}$$依据任务指令$$I_T$$、上轮屏幕感知信息S和本轮执行记录$$\mathcal{M}_{A}$$，检查当前屏幕变化是否符合动作预期并跟踪当前子任务$$P_{Sg}$$的进展，输出反思结果$$R$$。接下来，根据反思结果$$R$$和此前的计划$$P$$、关键上下文信息$$C$$，$$\mathcal{A}_{RP}$$更新整体计划$$P_{Op}$$并确定下一个子任务$$P_{Sg}$$。最后，$$\mathcal{A}_{RP}$$判断目前是否需要与用户交互，输出用户交互请求$$D_R$$。
$$P^{t+1}, D^{t+1}_R,R^{t}=\mathcal{A}_{RP}(I_T,S^{t-1},\mathcal{M}_A^t,C^{t-1},T^{I_T}_{p})$$
$$D_R$$包括用户交互类型$$D_{Ic}$$及思考$$D_{It}$$；$$R$$包括动作结果$$R_{Ar}$$和计划进展$$R_{Pr}$$。其中，$$R_{Ar}$$是以下值的枚举：A：子目标已经完成；B：子目标部分完成；C：动作产生了意外的结果；D：动作未产生任何变化。在动作结果不符合预期（即为C、D）时，还会包括潜在错误原因$$R_{Ec}$$以供纠错使用。
在$$R_{Ar}$$为A时，$$\mathcal{A}_{RP}$$将从$$P_{Op}$$中挑选下一个子目标执行；否则不会调整当前子目标。在当前子目标的$$R_{Ar}$$连续三次为C或D时，$$\mathcal{A}_{RP}$$将考虑调整$$P_{Op}$$并重新挑选子目标，该调整不会变更已经完成的部分。
$$\mathcal{A}_{RP}$$支持“Standalone”模式，在此模式下，反思与计划将在两个Agent中完成。其职责a，b将被分配至Reflector模块（$$\mathcal{A}_{R}$$）与Planner模块（$$\mathcal{A}_{P}$$）。这一模式会降低整体执行速度，可有限提升其稳定性和准确率。
Action Decider（$$\mathcal{A}_{AD}$$）负责根据$$\mathcal{A}_{RP}$$制定的子目标策划具体的原子行动。$$\mathcal{A}_{AD}$$首先依据上次动作的动作结果$$R_{Ar}$$，获取动作决策提示$$T^{P_{Sg}}_{exe}$$或错误恢复提示$$T^{R_{Ec}}_{err}$$，然后基于任务指令$$I_T$$、计划$$P$$、当前屏幕感知信息$$S$$、最近$$n$$次执行记录$$\{ \mathcal{M}_{A}^{\tau} \}_{\tau = t-n}^{t}$$和关键上下文信息$$C$$，规划需要执行的原子动作序列并做出动作决策$$A$$。
$$A^t=\mathcal{A}_{AD}(I_{T},P^t,S^t, \{ \mathcal{M}_{A}^{\tau} \}_{\tau = t-n}^{t},C^t,T^{P_{Sg}}_{exe} / T^{R_{Ec}}_{err}) $$
$$A$$包括原子动作序列$$A_{As}$$和动作预期结果$$A_{Er}$$。$$A_{As}$$由一或多个原子操作构成。如果执行原子操作需要参数，则参数也包含在该序列中。
Action Executor（$$\mathcal{T}_{AE}$$）是一个工具，用于执行由$$\mathcal{A}_{AD}$$产生的原子动作序列$${A}^t_{As}$$。$$\mathcal{T}_{AE}$$可通过UIAutomator，在用户设备$$\mathcal{P}$$上执行以下原子操作：“Tap”, “Swipe”, “LongPress”, “Input”, “ClearInput”, “KeyEvent”, “Wait”, “Finish”, “NeedInteraction”, “ListApps”, “StartApp”。详细列表请参考附加材料。
Screen Perceptor（$$\mathcal{T}_{SP}$$）是一个工具，用于获取并感知当前屏幕信息，支持通过UI Automator获取屏幕截图$$S_{Sp}$$和可访问树XML$$S_{At}$$。$$\mathcal{T}_{SP}$$支持视觉与非视觉两种模式：
（1）在视觉模式下，$$\mathcal{T}_{SP}$$将从$$S_{At}$$中提取“Clickable”与“Scrollable”的组件，依据其bounds属性将其投射在$$S_{Sp}$$上，并为其赋予序号（Mark），该序号与中心坐标的映射关系（Set of Mark, SoM）被存储为$$S_{SoM}$$。在此模式下，$$A_{As}$$在交由$$\mathcal{T}_{AE}$$执行前，将基于$$S_{SoM}$$进行标记到坐标的转换。
（2）在非视觉模式下，$$\mathcal{T}_{SP}$$将基于“可访问树处理算法”（见附加材料）移除无用节点和属性，通过MLLM模型补全图片节点的描述信息，合并并总结“Clickable”组件子节点，最终以类md格式输出为文本化感知信息$$S_{Pt}$$。基于此，我们可支持非视觉模型参与任务处理。
——————补充材料：
我们注意到，即使是最先进的LMM在完成任务时，精确识别屏幕内容并提取相应坐标仍具有挑战。与本领域其他工作类似，Fairy也考虑通过设计先进的Screen Perceptor工具而非微调模型来解决这一问题。
Screen Perceptor通过UI Automator获取屏幕截图和可访问树XML（简称为AT），在获取后，AT将被解析并转换为Dict以便于后续处理。$$\mathcal{T}_{SP}$$将遍历AT以获取其中的Operable节点（即包括可点击或可滚动属性的节点），并将它们记录下来。对于视觉模式而言，这些节点将被依次赋予序号（Mark），同时将编号与对应的中心点坐标（可点击节点）或bounds坐标（可滚动节点）记录至Set of Mark。接下来，一个绘图工具将这些组件的框绘制在截屏上。该截屏将在后续被传递给大模型用于动作决策，一旦决策完成，标记-坐标转换器就可以依据Set of Mark，将基于Mark的决策信息转换为基于坐标的决策信息，从而控制手机执行。其主要流程请参考图X。
对于非视觉模式而言，$$\mathcal{T}_{SP}$$在遍历AT时，除获取Operable节点外，还会（1）清理其中的无意义节点属性，仅保留其中的非阴性值；以及（2）获取其中的图像节点（节点类型为View和ImageView）。接下来，图像节点描述补全器将基于图像节点的坐标提取对应图片，并使用MLLM模型并行补全它们的描述信息。同时，节点总结器将并行总结Operable节点下的所有子节点，将它们的总结描述赋予Operable节点，同时移除所有已被总结的，非Operable的子节点。最后，$$\mathcal{T}_{SP}$$将再次遍历AT，压缩合并所有只有一个子元素的元素，在此之后将AT树输出为类MD结构的文本化屏幕感知信息。该信息包括节点的类型，资源ID，坐标，关键属性和在前序步骤中添加的描述信息。经过上述处理后，文本化屏幕感知信息维持了与AT或屏幕截图中同等的结构信息表达能力，其冗余信息相较于原始XML大大减少，且缺失的信息得到了补全。我们发现，使用这种信息，我们甚至可以使用非视觉大模型进行任务处理，这可能对于未来在手机中部署的小尺寸单一模态的LLM而言至关重要。算法X揭示了其主要流程。
非视觉模式下，由于可访问树本身的特性，有可能使得屏幕中实际上不存在的组件（因被覆盖而不显示也不可用的组件）出现在屏幕感知信息中。为缓解此类问题，$$\mathcal{T}_{SP}$$还将根据坐标信息校验组件间是否存在遮蔽，并对可能存在这种情况的组件基于OCR识别进行二次校验，从而排除已被遮蔽的节点。
在视觉模式模式下，依赖可访问树有可能使得我们遗漏组件。部分组件，例如在选择时间时的滑动选择器，其可滚动属性常常缺失，这会导致在获取Operable节点时将其排除在外，进而未被标记在截屏中。这将导致动作决策器$$\mathcal{A}_{AD}$$无法针对该组件进行动作决策。一个缓解的策略是我们将额外考虑View节点，并使用MLLM模型判断它们的基本功能，一旦发现遗漏就将它们补充Operable节点列表中。此外，该模式下也同样面临组件覆盖问题，但情况相较于非视觉模型更易于处理：即使这些被覆盖的组件被框出，$$\mathcal{A}_{AD}$$也不大可能对其做出动作；此外，在AT树中，最上层的组件的位置要相较于下层更靠后，这意味着它们将在最后被绘制，绘图工具在绘制重叠框时将覆盖前面已经绘制的框，如图X所示，这将破坏位于下层的组件的Mark以使得它不再可以点击。
此外，我们也关注到了如精细视觉感知（Fine-grained Visual Perception, FVP）、OmniParser等纯视觉方案，许多工作考虑引入基于视觉模型的提示模块来补全屏幕识别能力，例如通过文本OCR和图标识别工具提取信息并计算相关坐标。尽管使用这种端到端的方法可以简化系统设计，但令人遗憾的是其准确率和速度均存在缺陷，不完整或错误的信息将严重干扰智能体的决策与执行。我们在开源代码中保留了适用于Fairy的FVP模块，以供对比实验，但该模块将在Fairy的后续版本中被移除。
Key Context Collection（$$\mathcal{A}_{CE}$$）负责从屏幕中提取关键上下文信息，以供计划器和执行器参考。在信息收集类任务中（例如，寻找附近的意大利餐厅并总结评价），$$\mathcal{A}_{CE}$$维护的上下文信息将发挥重要作用。$$\mathcal{A}_{CE}$$将基于任务指令$$I_T$$、上下文抽取请求$$G_{cr}$$、计划$$P$$、当前屏幕感知信息$$S$$和此前的上下文信息$$C^{t-1}$$，提取出新的关键上下文信息$$C^t$$。
$$C^{t}=\mathcal{A}_{CE}(I_{T},G_{cr},P^t,S^{t},C^{t-1})$$
$$\mathcal{A}_{CE}$$在每轮Action Loop结束且结果$$R_{Ar}$$为A或B时才会激活。其行动与其他智能体是并行的。因为当前轮的起始屏幕感知信息将包含上一轮的屏幕信息，所以无需等待$$\mathcal{A}_{CE}$$完成信息收集。这种设计提高了智能体响应速度。
Working Memory （$$\mathcal{M}_{A}$$）当完成第$$t$$轮Action Loop后，$$\mathcal{M}_{A}^t=\{P^t,A^t,S^t,R^t\}$$。附加材料中展示了智能体$$\mathcal{A}_{RP}$$、$$\mathcal{A}_{AD}$$、$$\mathcal{A}_{CE}$$和工具$$\mathcal{T}_{AE}$$、$$\mathcal{T}_{SP}$$之间的记忆调度逻辑。
3.3.2 Interaction Loop
Interaction Loop是负责与用户交互的核心循环，其流程如图X所示。
[图片]
在Action Loop中，在$$\mathcal{A}_{RP}$$判断用户交互类型$$D_{It}$$不为0时，此时当前的Action Loop将被挂起并进入Interaction Loop以与用户进行交互。其中，$$D_{It}$$是以下值的枚举：1: 需用户确认敏感或危险操作；2: 需要用户确认不可逆操作；3: 需用户针对不同选项做出选择；4: 需用户进一步澄清指令；0: 不需要交互
为避免由于$$\mathcal{A}_{RP}$$幻觉而使得Fairy错过用户交互，我们允许$$\mathcal{A}_{AD}$$选择$$NeedInteraction()$$加以纠正。一旦选择发生，$$\mathcal{A}_{RP}$$就能在接下来的循环中反思错误并进入Interaction Loop。
User Interactor（$$\mathcal{A}_{I}$$） 负责根据计划器制定的子目标，持续生成用户提示、接收并判断用户回复是否已满足要求，若要求满足，其还会对用户的对话进行总结。
当$$D_{It}$$非0时，或收到用户回复$$D_{Ur}$$时，$$\mathcal{A}_{I}$$将被激活。$$\mathcal{A}_{I}$$将基于任务指令$$I_T$$、计划$$P$$、用户交互请求$$D_{R}$$、当前屏幕感知信息$$S$$和此前的上下文信息$$C$$，生成当前的用户交互计划$$D$$。若已进行过$$k$$轮交互，$$\mathcal{A}_{I}$$还会读取历史交互记录$$\{ \mathcal{M}_{I}^{\tau} \}_{\tau = 0}^{k}$$中的用户提示$$D_{Up}$$和回复$$D_{Ur}$$。
$$D^{k+1}=\mathcal{A}_{I}({I}_{T},P^{t},D_{R}^{t},S^t,C^{t-1},\{ \mathcal{M}_{I}^{\tau} \}_{\tau = 0}^{k})$$
$$D$$包括交互状态$$D_{Is}$$和用户提示$$D_{Up}$$。其中，$$D_{Is}$$是以下值的枚举：0：需要进一步与用户进行交互；1：用户已做出清晰选择或澄清了模糊的说法。当交互完成时（即$$D_{Is}$$为1），还会包括用户回应总结$$D_{Us}$$以供更新$$I_T$$使用。
User Dialoger（$$\mathcal{T}_{UD}$$） 是一个工具，用于以UI界面与控制台等方式向用户（$$\mathcal{U}$$）显示用户提示$$D_{Up}$$并等待用户输入回复$$D_{Ur}$$。当交互状态$$D_{Is}$$为0时，$$\mathcal{T}_{UD}$$被激活。在评估时，$$\mathcal{T}_{UD}$$也可接入评估系统以进行自动测试。
$$D_{Ur} = \mathcal{T}_{UD}(D_{Up},\mathcal{U})$$
Planner（$$\mathcal{A}_{RP}$$）除在Action Loop中介绍的两个阶段外，$$\mathcal{A}_{RP}$$还负责在用户交互结束后检查结果，并视情况调整或继续执行此前的任务规划：
3) 调整（用户交互）：$$\mathcal{A}_{RP}$$依据用户交互请求$$D_{R}$$和当前屏幕感知信息$$S$$，检查当前用户回复总结$$D_{Us}$$是否已经覆盖了需要从用户处获得的信息。接下来，根据反思结果和任务指令$$I_T$$、计划$$P$$、关键上下文信息$$C$$，$$\mathcal{A}_{RP}$$判断目前是否需要继续与用户交互，输出$$D_R$$，并视情况更新整体计划$$P_{Op}$$与确定下一个子任务$$P_{Sg}$$。
$$P^{t+1}, D_{R}^{t+1}=\mathcal{A}_{RP}(D_{R}^{t},S^{t},D^t_{Us},{I}_{T},P^{t},C^{t-1})$$
当用户交互类型$$D_{It}$$为0时，此时Interaction Loop将被终止，Action Loop解除挂起并进入$$\mathcal{A}_{AD}$$进行原子行动决策。
Working Memory （$$\mathcal{M}_{I}$$）当完成第$$k$$轮Interaction Loop后，$$\mathcal{M}_{I}^k=\{D^k,D^k_{Ur}\}$$。附加材料中展示了智能体$$\mathcal{A}_{RP}$$、$$\mathcal{A}_{I}$$与工具$$\mathcal{T}_{UD}$$之间的记忆调度逻辑。若本轮$$D_{Is}^k$$为0，则针对本次交互请求$$D^t_{R}$$的回应$$D^t_{Us}$$来源于$$D^k_{Us}$$。在Interaction Loop将被终止后，$$k$$重置为0。
3.3.3 Short-term Memory
在App-Level Executor中的各个智能体和工具在执行任务时均需依赖大量的上文，同时产生系列下文在后续流程中使用。App-Level Executor正在执行第$$j$$个子任务，当在第$$t$$轮Action Loop中$$\mathcal{A}_{AD}$$给出“Finish”的决策后，完整记录为$$\mathcal{M}_{\mathcal{O}}^j=\{I_{T}^j,\{\mathcal{M}_A^{\tau},C^{\tau}\}_{\tau=0}^{t},\{\mathcal{M}_{I,\tau}^{(i)}\}_{\tau=0,\ i=0}^{t,\ n_\tau}\}$$；关键轨迹记录为$$\mathcal{M}_{T}^j=\{I_{T}^j,P^t_{Sg},\{A^{\tau},R^{\tau}\}_{\tau=0}^{t},C^t\}$$。我们在附加材料中更完整揭示了Short-term Memory的设计。
3.4 Self-Learner
许多工作致力于通过对模型进行微调的方式以提升其执行表现，然而App的长尾效应和持续的版本迭代削弱了这些努力。一旦这些模型面对一个未知的App或已知App的新版本，它就只能依赖常识进行猜测，而这正是许多智能体犯错的根源。即使它们依赖错误处理机制纠正了这一问题，但仍无法避免在下一次同类任务中继续犯同样错误。因此，在执行过程中持续积累对App的知识是关键且必要的。
我们设计了两个智能体收集、总结、维护此前任务中的知识与经验，并将其存储于Long-term Memory中，以供智能体们在规划与动作决策使用：
App Trick Learner($$\mathcal{AL}_{AT}$$) 在高层次反思整个子任务的执行过程，检查执行中产生的错误步骤与冗余步骤，以及原始计划与最终计划的差异，进而总结在未来避免问题与精准规划的经验$$T$$。在App-Level Executor执行结束后，$$\mathcal{AL}_{AT}$$将对子任务执行轨迹$$\mathcal{M}_{T}$$中的关键信息进行分析，生成针对当前应用$$AM_p$$的规划$$T_{\mathrm{p}}$$ 、执行$$T_{\mathrm{exe}}$$ 与纠错$$T_{\mathrm{err}}$$ 三类技巧（Tricks）。
$$\{\Delta T_{\mathrm{p}},\Delta T_{\mathrm{exe}},\Delta T_{\mathrm{err}}\}^{AM_p^j}= \mathcal{AL}_{AT}({I_{T}^j,P^t_{Sg},\{A^{\tau},S^{\tau},R^{\tau}\}_{\tau=0}^{t}})$$
除由$$\mathcal{AL}_{AT}$$生成提示外，App Tricks $$T$$中还包括由人类专家提供的通用性技巧$$T^\mathrm{Common}$$。在使用时，智能体可基于关键词$$q$$，利用RAG（$$\mathcal{S}$$）从长期记忆中检索（Query）应用$$AM_p$$的相关信息。
$$T^{q,AM_p}_c=\mathcal{S}_c(T_c^{AM_p} \cup T_c^{\mathrm{Common}},q), c\in \{\mathrm{p},\mathrm{exe},\mathrm{err}\}$$
App Map Learner($$\mathcal{AL}_{AM}$$) 跟踪页面的变化以及导致变化发生的动作和触发器（页面组件），进而建立一个反映App页面中组件行为的知识图谱。在App-Level Executor执行结束后，$$\mathcal{AL}_{AM}$$将对每一个动作执行记录$$\mathcal{M}_{A}$$进行分析，生成针对页面组件$$\mathcal{N}$$的描述记录$$M_\mathcal{N}$$。
$$\{M_\mathcal{N}\}^{AM_p^j}= \mathcal{AL}_{AM}({S^{\tau-1},A^{\tau},S^{\tau}})$$
在$$\mathcal{T}_{SP}$$捕获屏幕后，将尝试从$$M$$中匹配对应的页面组件，如果匹配到相关节点，则将知识附加在$$\mathcal{T}_{SP}$$输出的文本化感知信息$$S_{Pt}$$中。我们在附加材料中更完整揭示了$$\mathcal{AL}_{AM}$$的设计。

---
App Map Learner($$\mathcal{AL}_{AM}$$) 的学习过程请参考图X中的绿色区域。在App-Level Executor执行结束后，$$\mathcal{AL}_{AM}$$将从每一个动作执行记录$$\mathcal{M}_{A}$$中提取屏幕感知信息，包括截屏和AT。此时$$\mathcal{AL}_{AM}$$将利用树相似度算法，从该App的页面知识库中尝试匹配该页面，若无法找到相似的页面，则将其标记为新页面；否则，提取该页面与原有页面的差异，记录新增或产生变化的组件节点（如绿区的②所示）。对于新页面，或新增的组件节点，$$\mathcal{AL}_{AM}$$会将其片段和截图同时输入LMM模型，从而建立对相关节点的描述信息（如绿区的③所示）。接下来，基于动作执行记录$$\mathcal{M}_{A}$$中的动作信息，为页面发生的变化与触发该变化的组件建立关联（如绿区的④所示）。最后，上述信息将被存储为一个JSON文件，该文件详细记录了App中已访问过的每个页面、页面中的不同组件结构和其功能摘要，以及页面中触发器的行动后果（即触发后将产生的页面或组件变化描述），这将为动作决策器提供动作的决策依据，避免依赖常识而盲目猜测，进而提升其准确性与稳定性。其算法详见算法X。
App Map Learner($$\mathcal{AL}_{AM}$$) 的提取过程请参考图X中的蓝色区域。当Screen Perceptor获取当前屏幕的AT后，将使用相同的树相似度算法，从该App的页面知识库中尝试匹配该页面（如蓝区的②所示），如果能够找到这样的页面，则直接提取对应组件的描述信息和触发器的行动后果（如蓝区的③所示），并将其附加至屏幕感知信息中（对于视觉模式，该信息将与Mark相关联，并被输出为额外的文本化感知信息$$S_{Pt}$$；对于非视觉模式，则直接附加在输出的$$S_{Pt}$$中对应组件的描述上）。

---
短期记忆模块承担了所有智能体的上下文管理功能。对于Action Loop，首先，Planner将从记忆管理器获取第T轮的起始屏幕、计划、动作和动作执行后的结束屏幕，然后做出第T轮动作的反思结果，并给出第T+1轮的计划。在给出反思结果后，第T轮的记忆就已经完整，此时记忆管理器将新建新一轮的Action Loop记忆，并将第T轮的结束屏幕作为第T+1轮的起始屏幕。接下来，Action Decider将获取第T+1轮的起始屏幕和计划，以及[T, T-n]轮的执行轨迹（仅包括行动与行动结果），然后给出决策出的原子动作。在该动作被Action Executor执行后，Screen Perceptor将被激活并给出第T+1轮的屏幕感知信息。最后，Planner将重复前面的过程，使得循环进入T+2轮。除上述智能体外，在Planner判断第T轮任务正常执行时，Context Extractor将与其他智能体并行，在T+1轮收集第T轮结束屏幕（也是第T+1轮起始屏幕）的关键信息，该关键信息将被存储为第T轮的关键上下文。在执行第T+1轮任务时，使用的为T-1轮关键上下文，这是因为第T轮的上下文信息仍在收集中，而且由于在T+1轮任务中初始屏幕已经包括了第T轮的上下文信息，也无需进行重复的补全。
[图片]
在第T轮时，若Planner决策目前需要进行用户交互，Interaction Loop将被激活，并与用户进行若干轮交互。首先，User Interactor其将从记忆管理器获取第T轮的起始屏幕和计划，以及[K,1]轮用户交互的提示词与用户回应，判断当前是否仍需与用户进行交互。若用户回复仍然没有满足交互需要，则构建第K+1轮的用户提示词并通过User Dialoguer将提示词向用户显示，待用户回应后，将提示词与用户回复一并存储为第K+1轮的用户交互记录，并继续由User Interactor进行下一轮交互规划。一旦用户的回复已经满足要求，User Interactor将总结用户响应，并使用其更新Task Instruction。此时Planner将获取第T轮的起始屏幕、计划和更新后的Task Instruction，对第T轮的交互进行反思，并依据用户补充的需求做出第T+1轮的规划。在给出反思结果后，此时记忆管理器将置空本轮Action Loop记忆中未补全的部分，然后新建新一轮的Action Loop记忆，并将第T轮的起始屏幕直接作为第T+1轮的起始屏幕。如果此时Planner决策此时仍需用户交互，则重复上述过程，否则Action Loop被激活，Action Decider将开始决策原子动作。
[图片]
4 Experiment                               
[图片]
Experiment Setup
4.1.1 评估基准
现有的流行评估基准会将所有用户需求一次性的包含在初始用户指令中，这使得它们难以用于评估交互式的智能体助手。此外，它们还面临任务场景真实性不足，任务难度偏低等问题。为了解决这些局限性，我们提出了一个面向真实场景的、具有挑战性的基准——RealMobile-Eval，它包括30个由领域专家设计的任务，分为简单（8个）、中等（16个）、复杂（6个）三个等级，涵盖“购物订餐”、“旅行规划”、“信息维护”、“个人助手”等场景。有关RealMobile-Eval的动机、与其他基准的比较和完整的任务列表，请参考附录。

---
我们发现，现有的流行评估基准中设计的任务，不太可能被用于评估交互式的智能体助手，因为他们通常将所有用户需求一次性的包含在初始用户指令中。同时，这也削弱了这些任务的真实性，正如我们在Motivating Examples中提出的案例，用户不大可能在一个任务中详尽的描述所有需求：例如在购买汉堡时说明需要使用的App、希望的门店以及汉堡的种类。此外，部分基准本身也缺乏真实世界中的常见任务，例如Android World中的任务主要关注效率类、通信类和多媒体类应用，且要求被选中的应用不需要登录且能在设备本地存储数据。这使得诸如“购物订餐”和“旅行规划”等常见复杂场景未能被有效包含。此外，一些惯用基准，例如用于AppAgent等早期工作评估的相关任务也过于简单，其任务的性能已经趋近饱和。
为解决这些局限性，RealMobile-Eval包括了30个由领域专家设计的任务，其设计规则为：

单APP
多APP
共计
任务难度区分
简单
8

0

8
不跨应用
用户需求总是清晰的
用户需求小于两条
少于5个步骤
中等
12

4
16

不跨/跨2个应用
存在模糊需求（明确/模糊都提供，但指标有区分）
用户需求小于四条
少于15个步骤
困难
4
2

6

跨超过2个应用
存在模糊需求（明确/模糊都提供，但指标有区分）
用户需求四条及以上
15个及以上步骤
4.1.2 评估方法与指标
许多工作使用二元成功率（Binary Success Rat）、基本事实轨迹（Ground Truth Trajectory）的匹配度，并结合人工专家来评估工作的有效性。然而，Agent在完成一个复杂任务时产生了瑕疵并不意味着在该任务上完全失败，同时完成任务的路径可能也不唯一，使用简单指标难以准确评估任务的完成情况。因此，我们为每项任务都编写了一份用户需求清单和关键步骤清单，在任务执行结束后，任务评估智能体将基于其，以及任务执行过程中的屏幕截图、操作日志信息，检查需求和关键步骤的完成情况。为消除幻觉影响，上述检查结果将作为人类专家评估的参考，当发现判断存在误差时将由人类介入改正。
考虑到具有交互能力的智能体将在面临模糊时将寻求人类补充或澄清，我们设计了一个任务驱动智能体，以用户需求清单为依据，代替人类做出回答。该模式仅在交互式智能体面临模糊需求时生效。人类专家将监督该过程，以确保该回答除进一步补充需求外不含其他额外内容。
基于上述方法，我们将计算被评估智能体的用户需求完成率（User Requirement Completion Rate, $$CR_{UR}$$）、关键步骤完成率 （Key Step Completion Rate, $$CR_{KS}$$）以及冗余步骤率（Step Redundancy Rate, SRR）。针对我们的工作，还将额外计算规划准确率（PA）/行动准确率（AA）/反思准确率（RA）。有关指标的详细内容与计算方式，以及完整的评估流程，请参考附录。

---
我们考虑以下评估指标：
- 用户需求完成率（User Requirement Completion Rate）：已完成的用户需求数 占 总用户需求数 的比例。
- 冗余步骤率（Step Redundancy Rate）：已完成任务中的冗余步骤数 占 总步骤数 的比例
- LLM模型调用量（Invocation Cost）：完成任务过程中调用LLM的次数
- 规划错误率/行动错误率/反思错误率（Planning / Action / Reflection Error Rate）： 规划/行动/反思错误的步骤数 占 总步骤数 的比例。
4.1.3 实验环境
我们的实验运行于Xiaomi 14 Ultra设备，Android版本为15；参与评估的骨干模型为Qwen-3、CPT-4o、DeepSeek-v3和DeepSeek-r1；RAG嵌入模型为Multilingual-e5，chat engine模型为qwen-turbo；屏幕视觉提示增强模型为qwen-vl-plus。有关设备的详细信息与模型版本号，请参考附录。
Evaluation on Performance
与最先进技术的比较 Comparison with state-of-the-art.
我们与多种先进的开源移动代理框架进行了比较，包括 AppAgent、Mobile Agent V2、MobA和Mobile Agent E。表1显示了基线工作和Fairy在RealMobile-Eval上，使用相同骨干网络GPT-4o的测试结果。与此前的SOTA工作对比，在所有测试任务上，Fairy的$$CR_{UR}$$较其平均提升33.7%；$$CR_{UR}$$较其平均提升27.2%；$$SSR$$较其平均降低58.47%。这一比较凸显出Fairy三层级的分工协作与积累特定App知识的有效性。
在此实验中，在被测Agent无交互能力时，我们使用包含所有需求用户指令；在被测Agent有交互能力时，我们使用模糊指令（中等与复杂难度时），再由测试驱动Agent根据询问给出进一步需求（未询问则不给出）。尽管不完整的初始指令使得Fairy面临更大的挑战，但Fairy并未因此而损失性能，这表明Fairy能够准确发现指令中的模糊之处并寻求用户澄清，验证了用户交互模块的有效性。
Agent
Multi-Agent

Interactive

Evolution
Simple


Medium


Complex






$$CR_{UR}$$
$$CR_{KS}$$
$$SSR$$
$$CR_{UR}$$
$$CR_{KS}$$
$$SSR$$
$$CR_{UR}$$
$$CR_{KS}$$
$$SSR$$
App-Agent
❌
❌
❌
0%
0%
0%
0%
0%
0%
0%
0%
0%
Mobile-Agent-V2
✔️
❌
❌
0%
0%
0%
0%
0%
0%
0%
0%
0%
Mobile-Agent-E
✔️
❌
✔️
0%
0%
0%
0%
0%
0%
0%
0%
0%
MobA
✔️
❌
❌
0%
0%
0%
0%
0%
0%
0%
0%
0%
Fairy（No Self-learning）
✔️
✔️
❌
0%
0%
0%
0%
0%
0%
0%
0%
0%
Fairy
✔️
✔️
✔️
0%
0%
0%
0%
0%
0%
0%
0%
0%
不同LMM的适配性

URCR
SRR
PA
AA
RA
ChatGPT-4o





DeepSeekV3





DeepSeekR1





Qwen3





表X列出了在RealMobile-Eval上Fairy使用各种骨干 LMM 的表现。我们观察到在所有最新的LMM上Fairy都有较好的表现。此外，在 GPT-4o 和 DeepSeekR1 等更强大的骨干网中，Fairy的优势似乎更加明显。
4.3 RQ2: 自我学习如何促进了多智能体的进化？
为了探究自我学习的作用，我们选取了10个任务以进行消融研究。在移除由自我学习积累的长期记忆后，这些任务的$$CR_{UR}$$下降了XX%，$$CR_{KS}$$下降了XX%，同时$$SSR$$升高了XX%，显示出自我学习在使用中持续积累的App知识对促进Fairy的表现进化具有重要作用。我们将结合具体的案例进行进一步说明。
Case1：任务为在亚马逊购买棒球帽，选择评分4.0以上且价格低于20美元的商品。基于长期记忆带来的经验，Fairy可以注意到搜索结果上方具有排序按钮，通过点击“Spend Less”和“Four Stars & Up”精确地对搜索结果进行排序。在移除长期记忆后，Fairy在搜索后未注意到上述按钮，而是通过多次滑动屏幕来寻找结果，使得冗余步骤数增加。
Case2：任务为查询支付宝账单并记账。基于长期记忆带来的经验，Fairy可以点击“我的”选项卡导航至“我的”页面，然后点击“账单”进入对应页面。在移除长期记忆后，Fairy会错误的点击“理财”选项卡，并在接下来的错误页面中尝试搜索“账单”，最终使得任务失败。
上述案例展示了长期记忆对Fairy的Plan和Action Decision的巨大改进，在积累更多知识后，Fairy减少了对界面猜测的依赖，能够做出更合理的规划并执行。
4.4 RQ3: 交互在多大程度上提升了用户的满意度？
为了探究交互模块的作用，我们将为所有基线工作提供与Fairy一致的模糊需求，以评估其他智能体在面临模糊指令时的性能。表X列出了基线工作和Fairy在RealMobile-Eval的中等与高难任务上，使用相同主干网络GPT-4o的测试结果（由于简单任务均为清晰需求，因此测试不包括它们）。
显然，由于用户指令模糊，不具备交互功能的Agent将自作主张的完成用户需求。这体现在，相较于接受清晰指令，其步骤完成率（$$CR_{KS}$$）并未显著降低，但它们的用户需求完成率（$$CR_{UR}$$）下降明显，在中等任务上平均下降了15.5%，在复杂任务上平均下降了59.6%。
得益于用户交互机制，Fairy能够与用户（实验中为任务驱动智能体）就指令模糊的部分进行沟通，从而较缺乏沟通的智能体基线在用户需求完成率（$$CR_{UR}$$）上平均提升了181.0%。这充分体现了Fairy交互机制的先进性，证明了交互式手机助手能更好的理解并满足用户真实需求。
Agent
Medium


Complex



URCR
SRR
IC
URCR
SRR
IC
App-Agent






Mobile-Agent-V2






Mobile-Agent-E






MobA






Fairy






5 Discussion
Background
Summarizing results
Commenting on results
Limitation
Implication
Future research
6 Related work
GUI Agents
Mobile GUI Agent是一种在智能手机中运行的GUI智能体（Agent），以 LMM 作为其核心推理引擎，感知GUI、规划并执行操作。这一领域的工作始于AutoDroid，紧随其后，AppAgent、Mobile-Agent、MobA、M3A等工作致力于通过改进提示词与上下文工程、设计更先进的工作流架构来实现对智能手机应用的精细控制；CocoAgent、MobileFlow、等工作则通过构建新的数据集并对模型进行微调以提升LLM对页面的理解与操控能力。然而当前的工作仍然面临智能体忽视用户而越俎代庖、规划缺乏层次且依赖模型常识等挑战。Fairy与此前工作的核心区别在于将用户交互融入任务执行流程，设计了三个层次并基于此前执行过程中积累的特定App的经验来逐步规划任务，这使得Fairy可以紧跟用户真正的需求，并且随着用户使用逐步提升其表现。
自我学习与进化
自我进化指的是Agent可以通过经验的积累逐步提高性能。这一过程中的长期记忆的构建是关键，少数一些先进的工作已经开始考虑构建任务轨迹（Task Trajectories）、指导规则（Guidance and Rules）和新工具（New Toolkits），例如Mobile-Agent-E会从过往的任务中提取一些特定的操作序列封装为Shortcut并在执行时重复使用。然而，Mobile智能体进化研究尚不充分，相较于此前的工作，Fairy可以针对每个App建立包含其控制逻辑和使用诀窍的长期记忆，并在使用中不断完善从而持续改善（Continuous Improvement）未来任务效果。
6 Conclusion
我们介绍了Fairy，这是一种交互式的、持续学习并进化的多智能体手机助手，能够与用户保持沟通，引导用户渐进式补充任务细节，并利用积累的App知识完成各种复杂的现实任务的规划和执行。其局限性包括App操作逻辑知识建模不够充分，模型幻觉会带来不稳定性以及响应时间仍然偏长。未来的工作重点是改进App Map的收集、查询、存储策略；对不同角色的智能体骨干模型进行定向的微调，以削减模型幻觉和响应时间；以及加强Agent安全措施。


得益于层次式任务规划机制，行动与交互双循环设计与自我学习模块，Fairy可以与用户保持沟通，遵循用户指令和积累的App知识完成各种复杂的现实任务的规划和执行。其余的局限性包括积累知识的精确程度不足，长程信息收集任务缺陷，模型幻觉造成错误以及响应时间仍然偏长。未来的工作重点是改进App Map的收集、查询、存储策略，实现精细化学习；进一步优化任务规划方法和人机协作模式，更好的适应各类真实世界任务；尝试为不同任务的智能体指定特定的、经过微调的模型，以削减模型幻觉和响应时间；以及加强Agent安全措施。

我们介绍了 Mobile-Agent-E，这是一种新型移动助手，具有分层多代理框架和自我进化模块，可显著增强长期规划、错误恢复和效率，在各种复杂的现实任务中表现出色。尚存的局限性包括错误使用带有无效前提条件的快捷方式和由代理生成的错误快捷方式，详细示例见附录 C。未来的工作重点是开发改进的快捷方式生成、调用和修改策略，加强个性化以更好地适应用户的个性化需求，以及加强安全防范措施以实现更有效的人机协作。
废弃语料库
Introduction
例如，用户希望让手机助手帮助其点一份麦当劳汉堡外卖——这是一个典型的“清晰而模糊”的需求，用户难以在任务发布时一次性指明需要使用的App、希望购买汉堡的门店以及汉堡的种类。随意的购买麦当劳的任意汉堡来敷衍任务会使得用户感到沮丧。
在这些复杂的任务中，App功能与逻辑的“知识”、此前已完成任务“经验”、Agent本身的“常识”，以及三者共同带来的“进化”都不可或缺。
(因过长而不写到正文中👇)
我们发现，人类可以迅速适应并掌握一个即使是刚刚从应用商店下载的App。这是因为人类不仅拥有“常识”，还会在使用手机中会持续积累“知识”和“经验”。相当多的工作忽视了对各个App页面功能逻辑、不同App页面的跳转关系的记忆与总结，而依赖于纯视觉方案又加剧了积累这些知识的难度，这使得其只能依据大模型训练时积累的“常识”来进行规划和执行。已有一些先进的工作已采取措施以缓解这一问题，例如：AppAgent设计了两个阶段——先探索并获取经验然后用于辅助规划；MobileAgentE从过往的执行中总结了加快执行速度的ShortCut和避免犯错的Tips。然而，这些努力带来的见解相对有限：在用户正在使用的手机上进行功能探索可能产生意外操作；总结ShortCut和Tips对理解App功能路径并进行全局任务规划缺乏足够帮助。这种记忆进化的缺陷，使得现有的手机助手在执行类似任务时总会重复同样的错误，严重限制了它们处理现实世界中复杂任务的能力。
We have observed that humans can swiftly adapt to and master an app shortly after downloading it from the app store as they leverage their common sense and continuous accumulation of knowledge and experience while using mobile phones. Many studies overlook the importance of memorizing and summarizing the functional logic of each app page and the interconnectedness between various app pages. Relying solely on visual solutions hampers accumulating such knowledge, leading to planning and execution based purely on the "common sense" built during large model training. Some innovative efforts aim to address this challenge; for instance, AppAgent employs a two-phase strategy—first exploring and acquiring experience, then utilizing that knowledge for planning. MobileAgentE offers summarized Shortcuts to enhance execution speed and Tips to mitigate errors from past attempts. However, these initiatives yield limited insights: exploration on a user’s mobile phone may result in unanticipated actions, and summarizing Shortcuts and Tips often fails to adequately understand the app's functional pathways or facilitate comprehensive task planning. This gap in memory evolution results in current mobile phone assistants repeatedly making the same mistakes during similar tasks, significantly impeding their capacity to handle complex real-world scenarios effectively.
(因过长而被删改👇)
我们注意到，现有的流行评估基准主要是一些简单任务，这些任务的准确率已经趋于饱和；而在一些最新的工作给出的复杂任务评估却不符合现实中用户的使用体验。为了全面评估Fairy的实际能力，我们计划基于这些最新的工作进行改进，引入一个更真实的基准——RealMobile-Eval。与此前的基准相比，RealMobile-Eval基于LMM模拟了用户与手机助手的渐进式交互，其表现更接近于真实场景下的用户；同时，我们选取了更复杂、真实的手机应用，例如“美团”、“知乎”、“X”、“YouTube”、“淘宝”等巨大且通用的应用，它们带来的挑战将显著高于功能专一的特定应用。我们考虑了多种先进的评估指标（参见对应章节），以确保最终得分能够正确反映用户体验。我们将此前的多项工作（5项）在RealMobile-Eval上进行实验，证明了该数据集可以区分这些工作的水平。
% We observed that existing popular evaluation benchmarks primarily address simple tasks, which have reached a saturation point in accuracy; conversely, the assessment of complex functions in some recent studies\cite{rawles2023androidinthewild,xie2024osworld,rawles2025androidworld,zhang2024llamatouch,sun2022metagui} lacks realism regarding user experience. To thoroughly evaluate Fairy's real-world capabilities, we propose introducing a more nuanced benchmark, RealMobile-Eval, based on recent enhancement advancements. Unlike prior benchmarks, RealMobile-Eval simulates the dynamic interactions between users and mobile assistants powered by LLM, producing performance results that more accurately reflect real user scenarios. Additionally, we selected a range of complex and realistic mobile applications, including Meituan, Zhihu, X, YouTube, and Taobao—large, widely used platforms that present significantly greater challenges than specialized apps. To ensure that the final scores accurately represent user experience, we considered a variety of advanced evaluation metrics. We conducted experiments with multiple prior works using RealMobile-Eval, demonstrating its effectiveness in distinguishing the performance levels of these studies.
Motivating Examples
我们发现，现有的手机助手不足以满足真实世界用户的任务需求。现有的手机助手通常只能处理目标明确的任务，例如“请帮我删除所有垃圾短信”。而在真实世界中用户的任务则更为复杂，具体的挑战包括：（1）人机间协作交互挑战：在开始时用户往往只有一个高层的想法，需要在与设备的交互中收集信息并逐步做出决定（例如，用户一开始想点外卖，而具体点什么外卖则需要在交互中决策）；（2）多应用间的协作交互挑战：用户的任务可能涉及在多个应用程序间穿梭，需要每个应用负责完成具体的子任务（例如，用户希望规划行程并订购酒店和机票，这可能涉及论坛、地图、票务等多类应用）；（3）高度复杂的交互环境挑战：移动端的应用有着丰富且多变的页面布局，同时还极有可能充斥着各类与用户任务相关的广告信息，需要确保任务可以快速、准确的执行，避免落入广告陷阱或在复杂的页面中迷失方向。
针对多应用间的协作交互挑战，许多工作（1~3项）隐式的要求用户在指令时明确所需涉及的多个应用，甚至需要包括对这些应用的编排。由于缺乏对用户手机中已存在应用程序的功能感知，一旦用户不再提供包含App名字的具体指令，这些手机助手就不再可以执行这些命令。
针对高度复杂的交互环境挑战，随着视觉大模型的普及，许多工作（2~5项）放弃了此前的基于可访问树的XML描述方式，转变为纯视觉的方式进行。事实上，纯视觉方案在速度和准确率上的表现令人失望，涉及多个CV模型和VLLM的流程拖累了速度，而不确定性进一步干扰了智能体的表现。此外，这种方案也难以辨别显而易见的图片广告。至关重要的是，纯视觉方案在组件提取上仍然存在缺陷，这导致采用了这类方案的工作难以正确积累“应用页面”的知识，而这种知识对规划至关重要。
Our Approach 
(因过长而被删改👇)
$$\mathcal{T}_{AE}$$同时也负责在启动时获取手机应用列表$$App_{Pkg}$$，以及根据$$\mathcal{A}_{GRP}$$产生的全局子任务$$g^{j}_{St}$$中包含的$$App^j_{Pkg}$$启动特定App。
(因过长而被删改👇)
- $$Tap(x, y)$$：在当前屏幕的坐标位置(x,y)处轻点。
- $$Swipe(x1, y1, x2, y2, duration)$$：从坐标位置(x1, y1)滑动到位置(x2, y2)，持续时间为 duration 秒。
- $$LongPress(x, y, duration)$$：在坐标位置(x, y)长按，持续时间为 duration 秒。
- $$Input(text)$$：向当前激活的输入框输入文本 "text"。注意，文本会经过转义处理以保证正确输入。
- $$ClearInput()$$：清空当前输入框中的内容。
- $$KeyEvent(type)$$：发送键盘事件，type 对应 Android 键值，例如 KEYCODE_BACK 或 KEYCODE_HOME。
- $$Wait(duration)$$：等待 duration 秒。
- $$Finish()$$：任务完成标记，不执行任何动作。
- $$NeedInteraction()$$：需要用户交互标记，不执行任何动作。
- $$ListApps()$$：列出当前设备上安装的所有第三方应用包名。
- $$StartApp(app\_package\_name)$$：启动指定包名的应用，包名为 "app_package_name"。
(因过长而被删改👇)
(不写到正文中)我们注意到，即使是最先进的LMM在完成任务时，精确识别屏幕内容并提取相应坐标仍具有挑战。许多工作考虑引入基于视觉模型的提示模块来补全屏幕识别能力，例如通过文本OCR和图标识别工具提取信息并计算相关坐标。尽管使用这种端到端的方法可以简化系统设计，但令人遗憾的是其准确率和速度均存在缺陷，不完整或错误的信息将严重干扰智能体的决策与执行。
Although the latest multimodal large language models (LMM) have made significant advancements, accurately identifying on-screen elements and retrieving their coordinates continues to be a challenge. As a result, many studies incorporate vision-based prompt modules, such as OCR and Icon Recognizers, to address this issue. While end-to-end vision pipelines can simplify the system architecture, they often suffer from latency and accuracy problems. Incomplete or incorrect information can seriously mislead the agent's planning and execution.
由于我们的工作仅针对移动端设备，因此我们考虑通过读取页面可访问树的方式（基于UI Automator）获取具备当前屏幕结构化信息的XML代码。
然而，直接获取的$$s_{info'}^t$$中包含了大量的冗余信息，如果将其直接用于屏幕提示将使得上下文超出限制，或（由于大量无效信息）增加大模型的幻觉。同时，在屏幕中显示的图片或图标也无法从XML获取具体内容。
Related work
GUI Agents
多模态大语言模型(MLLMs)领域的进步促进了人机交互的变革，极大的推动了GUI Agent的相关研究。GUI Agent是一种在GUI环境中运行的智能体，利用 LMM 作为其核心推理引擎，感知GUI并生成、规划和执行操作。它的工作环境包括Web、Desktop和Mobile三种平台，不同的平台在系统和应用层面都有其独特的特点和限制。对于Mobile Agent而言，移动设备的屏幕空间有限，页面布局层次复杂，且依赖触摸交互，但能够获取页面的可访问树(Android’s Accessibility)。针对这些特点，Mobile智能体通常使用可访问树或截屏为LMM提供屏幕感知，还会基于CV或解析可访问树方式为LMM生成画面提示；通过单一或多个智能体协作的方式完成计划，并通过ADB等方式模拟触摸以在手机上执行计划。然而，当前的工作仍然面临视觉感知不准确且速度过慢、多智能体协作缺乏层次、大量智能体串行带来时间消耗、规划过分依赖模型常识、智能体忽视用户而越俎代庖等挑战。Fairy与此前工作的核心区别在于设计了高中低三个层次来协调智能体任务，基于Action Loop和Interaction Loop使得智能体可以紧跟用户真正的需求执行任务。我们还为上述广泛存在的Gap提供了缓解方案。
