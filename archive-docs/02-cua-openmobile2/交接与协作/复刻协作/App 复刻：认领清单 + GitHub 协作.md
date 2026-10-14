# App 复刻：认领清单 \+ GitHub 协作

## 一、认领规则

- App 按难度分 5 档：**高=5 / 中高=4 / 中=3 / 中低=2 / 低=1**。

- **每档各认领 1 个，共 5 个，难度合计 15 分**

- **表里的 App 只是参考**。认领后可以换成**同类型**的别的 App（例：把「滴滴」换成「高德打车」「T3」，把「知乎」换成「即刻」），只要难度相当、且不和下面「已有 App」重复即可。

- 认领后在该行「负责人」列写名字，先到先得。

**NEW**

- ****完成后在状态列填写【已完成】或【已PR】

### 已有 App（不要重复做）

- **日常 App（apps/）**：微信、小红书、支付宝、B站、淘宝、卡皮记账、地图、**美团**、12306、腾讯会议、微信读书、Spotify、Reddit、eBay、X、**天气**。

- **系统 App（system/）**：浏览器、计算器、日历、时钟、指南针、通讯录、文件管理、相册、备忘录、设置、短信、答题卡、主题商店。

---

## 二、候选 App（按难度分档）

### 高（5 分）— 多账号 / 支付 / 复杂流程

### 中高（4 分） 

### 中（3 分）

### 中低（2 分）

### 低（1 分）— 单机 / 工具 / 无支付

> 还不够 / 想做别的：可同类替换，或从备用池选——盒马、肯德基、星巴克、QQ音乐、酷狗、红果短剧、起点读书、特来电、微医、国家医保、个税、豆果美食、下厨房、墨迹之外的生活工具 等。
> 
> 

---

## 三、文件怎么组织

拉下仓库后，和复刻有关的就四类东西：

你做一个 App，AI 只会动**两个属于这个 App 的文件夹**：`apps/<App>/`（代码）和 `docs/<app>-replication/`（过程产物）。别人的 App 在别的文件夹，互不相干。

新 App 由平台扫描 manifest **自动识别，不需要改 OS 层或任何公共文件**——这是几个人能并行而不冲突的原因。唯一的公共文件是依赖锁文件：正常复刻用不到新依赖，AI 若提出要装包，先在群里同步一下。

---

## 四、GitHub 基本操作

New 在开始做某个app前，一定在这个文档里刷新确认这个app没有被认领过；然后填好自己的名字

仓库：`https://github.com/ZYY0321/mobilegym-mock`

**一次性准备**

- 各自安装 Git、Node ≥ 22，拉下项目并跑通模拟器：

```Bash
git clone https://github.com/ZYY0321/mobilegym-mock.git
cd mobilegym-mock/trial_apps/mobilegym
npm install && npm run dev      # 打开它给的地址即可看到模拟手机
```

- New 在git clone之后，需要下载mobilegym需要的一些[资源包](https://github.com/Purewhiter/mobilegym#1-install)（确保壁纸、字体渲染、图标、app内资源的美观）；如果github下载有不方便也可以用我下好的https://box\.nju\.edu\.cn/seafhttp/f/a7a9ffb420f444b79714/?op=view，下载解压之后放在`mobilegym-mock/trial_apps/mobilegym/`目录下。最终环境ready的标志是`npm install && npm run dev`之后和[官方demo](https://mobilegym.dev/)基本在外观上一致（我们的版本可能会多一些app）

### **开自己的分支**

```Bash
git checkout -b zhangyingying          # 用你的名字，你 5 个 App 都在这条分支上做
```

### **做完一个 App（在自己分支上提交、推送）**

```Bash
git add trial_apps/mobilegym/apps/Jingdong docs/jingdong-replication
git commit -m "京东复刻：阶段④审核通过"
git push -u origin zhangyingying        # 第一次推带 -u，之后直接 git push
```

New\&Important 

### App都完整能跑了怎么交 → 开 PR，等组长合并（不要自己合 main）

1. 推完分支后，打开 GitHub 仓库页面，会提示 Compare \& pull request，点它；base 选 main，compare 选你的分支（如 zhangyingying）。

2. PR 里写清做完了哪个 App。

3. 由组长审核 \+ Merge。合并后，别人 git pull 就能看到你的成果了。

**两条约定**

- 提交时**只 add 你自己 App 的两个文件夹**，不要 `git add .`。

- 截图不进仓库——`.gitignore` 已忽略所有 `*_images/`，正常提交不会带上。

操作中拿不准，把 `git status` 的输出连同报错发给 AI，它会给出下一步。



New\&Important

### 怎么同步最新规范\(不用重新 clone\):

你已经 clone 过主仓,以后每次开工前,在项目目录下跑一句就拿到最新规范:

git pull。它只更新有变动的文件,你本地正在做的 app 不受影响。**0701：**判断自己是不是最新:打开 docs/app\-replication\-pipeline\-v3\.md,拉到最后看有没有「§10 保真四要素」——有就是最新的。



### 发现新的共性问题\(或觉得规范/流程本身有坑\)怎么提?

不要自己在本地改规范——那样每个人的规范会变得不一样。在飞书群发问题、

维护者会把确认的共性问题收进规范文档,下次所有人 git pull 就自动带上。只影响你自己这个 App 的小问题,直接告诉正在陪你做的 AI 改就行。



