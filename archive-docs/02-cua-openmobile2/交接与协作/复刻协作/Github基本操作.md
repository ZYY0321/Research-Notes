四、GitHub 基本操作
New 在开始做某个app前，一定在这个文档里刷新确认这个app没有被认领过；然后填好自己的名字
仓库：https://github.com/ZYY0321/mobilegym-mock （private，只有被邀请的协作者能看到）

⚠️ New 先分清两条 git 操作，别搞混（新手最容易在这卡住）：
- 拉最新代码/规范/别人的成果 = git pull（往下拉，随时可做，不用切分支）
- 交你做好的 app = 推到你自己的分支 + 开 PR（往上交，组长审核合并后别人才看得到）
- 任何人都不要 git push origin main。main 是大家共享、始终要能跑的分支，谁都往上直推很容易搞乱、连累所有人 npm run dev。一律走 PR，由组长统一 merge。

一次性准备
- 组长把仓库设为 private（Settings → General → Change visibility），并在 Settings → Collaborators 把每人加为协作者（否则看不到、也推不上去）。
- 各自安装 Git、Node ≥ 22，拉下项目并跑通模拟器：
git clone https://github.com/ZYY0321/mobilegym-mock.git
cd mobilegym-mock/trial_apps/mobilegym
npm install && npm run dev      # 打开它给的地址即可看到模拟手机
- New 在git clone之后，需要下载mobilegym需要的一些资源包（确保壁纸、字体渲染、图标、app内资源的美观）；如果github下载有不方便也可以用我下好的https://box.nju.edu.cn/seafhttp/f/a7a9ffb420f444b79714/?op=view，下载解压之后放在mobilegym-mock/trial_apps/mobilegym/目录下。最终环境ready的标志是npm install && npm run dev之后和官方demo基本在外观上一致（我们的版本可能会多一些app）

开自己的分支（一人一条，只开一次）
git checkout -b zhangyingying          # 用你的名字，你的几个 App 都在这条分支上做
做完一个 App（在自己分支上提交、推送到你自己的分支）
git add trial_apps/mobilegym/apps/Jingdong docs/jingdong-replication
git commit -m "京东复刻：阶段④审核通过"
git push -u origin zhangyingying        # 推到你自己的分支，第一次带 -u，之后直接 git push

New 一个 App 完整能跑了 → 开 PR，等组长合并（不要自己合 main）
1. 推完分支后，打开 GitHub 仓库页面，会提示 Compare & pull request，点它；base 选 main，compare 选你的分支（如 zhangyingying）。
2. PR 里写清做完了哪个 App、有没有过保真四要素自查（见 docs/collaboration-and-doc-update.md）。
3. 由组长审核 + Merge。合并后，别人 git pull 就能看到你的成果了。

New 想继续做下一个 App，先把别人已合并的成果同步到自己分支再干（建议手头这个 App 先提交/合并完，再来同步，免得没提交的活和别人的改动搅在一起）：
git checkout zhangyingying
git merge main            # 或 git pull origin main，把 main 上的最新成果并到你分支

为什么不自己 git push origin main？因为大家都往 main 直推，只要有人手滑或没先同步，就可能把 main 弄乱、连累所有人跑不起来。统一走 PR、由组长一个人把关 merge，main 才始终干净可跑。（好在各人只动自己 App 的两个文件夹、互不重叠，正常几乎不会冲突。）

两条约定
- 提交时只 add 你自己 App 的两个文件夹，不要 git add .。
- 截图不进仓库——.gitignore 已忽略所有 *_images/，正常提交不会带上。
操作中拿不准，把 git status 的输出连同报错发给 AI，它会给出下一步。整套「开分支→做→推分支→开 PR→切回分支做下一个」的流程，拿不准也可以直接问陪你做的 AI，它会一步步带你。

怎么同步到最新文档(不用重新 clone):
你已经 clone 过主仓,以后每次开工前,在项目目录下跑一句就拿到最新规范:
  git pull。它只更新有变动的文件,你本地正在做的 app 不受影响。0701：判断自己是不是最新:打开 docs/app-replication-pipeline-v3.md,拉到最后看有没有「§10 保真四要素」——有就是最新的。
New git pull 会把 main 上所有更新都拉下来，包括别的同学已经合并的 app（这是正常的，不影响你做自己的 app，只是会多出别人的文件夹）。建议手头自己的 app 先做完、提交/合并了，再来 git pull 同步，免得没提交的活和别人的改动搅在一起。只想看最新文档的话，pull 完直接看 docs/ 即可。
发现新的共性问题(或觉得规范/流程本身有坑)怎么提?
不要自己在本地改规范——那样每个人的规范会变得不一样。在飞书群发问题、
维护者会把确认的共性问题收进规范文档,下次所有人 git pull 就自动带上。只影响你自己这个 App 的小问题,直接告诉正在陪你做的 AI 改就行。