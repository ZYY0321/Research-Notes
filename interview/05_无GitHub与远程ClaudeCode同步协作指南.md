# 无 GitHub 环境克隆修改仓库 & 远程 Claude Code 实时可视化同步指南

> 专门解决你提出的两大高频工程痛点：
> 1. **痛点 A**：别人的电脑 / 内网服务器**连不上 GitHub（或没有你的 GitHub 账号配置）**，怎么克隆这个仓库、在上面正常 `git commit` 修改并同步回你的电脑和 GitHub？
> 2. **痛点 B**：你在自己电脑上只通过纯命令行 SSH 连着远端服务器的 **Claude Code 终端**，看不到远端本地文件夹和排版渲染，怎么实时看到它改了哪些文件、长什么样，并一键同步回本地？

---

## 一、场景 A：远端机器连不上 GitHub（或无 GitHub 账号）怎么克隆与双向修改同步？

按网络条件给你 **3 套零翻车方案（优先推荐方案 1 和方案 2，纯靠你已有的 SSH 连接即可搞定，远端根本不需要配 GitHub！）**：

### 方案 1（最干净原生态！零第三方平台）：利用你本地电脑做 SSH 反向隧道 / Git Bundle 镜像

#### 做法 1A：SSH 反向代理一键直连（如果远端只是被墙连不上 GitHub，而你自己的 Mac 能连）
你在本地电脑 SSH 登录远端机器时，顺手带一个 `-R` 反向端口转发（假设你本地代理端口是 `7890`）：
```bash
# 在你自己的电脑终端执行：把本地 7890 映射给远端的 17890
ssh -R 17890:127.0.0.1:7890 user@remote-host

# 进到远端终端后，仅对当前 git 命令开启代理（配精细尺度的 PAT Token，用完即撤）
export https_proxy=http://127.0.0.1:17890 http_proxy=http://127.0.0.1:17890
git clone https://github.com/ZYY0321/Research-Notes.git
```
> **安全细节（在别人电脑上必看）**：千万不要把你自己的主私钥拷到别人电脑上！在 GitHub `Settings -> Developer settings -> Personal access tokens -> Fine-grained tokens` 建一个**只授权 `Research-Notes` 单一仓库、7 天自动过期**的临时 Token，克隆完离开时随时在网页端一键 Revoke 吊销。

#### 做法 1B：完全断外网也能用 Git！—— 把你本地电脑当成远端的 Git Remote（或用 `git bundle` 单文件传输）
如果远端机器**彻底禁止任何外网/代理**，Git 原生支持把整个仓库（含完整分支与历史）打成**单个离线文件 `.bundle`**：

```bash
# Step 1：【在你自己电脑】把最新仓库打成一个单文件包传给远端
cd ~/Desktop/research-lab/my-research
git bundle create /tmp/Research-Notes.bundle --all
scp /tmp/Research-Notes.bundle user@remote-host:/tmp/

# Step 2：【在远端无 GitHub 电脑】直接从单文件包完整 git clone 出来！
ssh user@remote-host
git clone /tmp/Research-Notes.bundle ~/Research-Notes
cd ~/Research-Notes
git checkout -b cc-work main   # 正常建分支让 Claude Code 随便改、随便 git commit！

# Step 3：【把远端的修改无损拉回你本地电脑，再推回 GitHub】
# 方法一（直接从你电脑拉远端目录，连打包都不用！Git 原生支持 ssh:// 协议直拉远端文件夹）：
cd ~/Desktop/research-lab/my-research
git fetch ssh://user@remote-host/home/user/Research-Notes cc-work:cc-work
git merge cc-work && git push origin main

# 方法二（如果只能单向拷文件）：在远端打增量包拉回来
# 远端执行：git bundle create /tmp/cc-updates.bundle main..cc-work
# 本地执行：scp user@remote-host:/tmp/cc-updates.bundle /tmp/ && git pull /tmp/cc-updates.bundle cc-work
```
> **为什么 `git fetch ssh://user@remote-host/path/to/repo` 是神器？**  
> 因为只要你本地能 SSH 连上那台机器，**那台机器本身就已经是你的一个合法 Git 远程仓库了**！它在上面完全离线 `git add / commit`，你在自己电脑敲一行 `git pull ssh://user@remote-host/.../Research-Notes main`，它的所有提交记录、diff 就原封不动进到你本地仓库了，随后你在自己电脑 `git push` 上 GitHub 即可，远端全程零密钥残留！

---

### 方案 2（国内服务器免代理多机共享）：配置国内镜像双远端（GitCode / Gitee）
你之前已经在用 GitCode（`gitcode.com` 国内直连满速不封禁）。只需在 `Research-Notes` 建一个私有镜像仓：
```bash
# 在你本地电脑添加双 push 地址（以后一次 git push 自动同时推 GitHub + GitCode！）
git remote set-url --add --push origin git@github.com:ZYY0321/Research-Notes.git
git remote set-url --add --push origin git@gitcode.com:<你的账号>/Research-Notes.git
```
任何没有 GitHub 网络的国内机器直接从 `https://gitcode.com/...` 克隆推送，你本地 `git pull` 后自动同步回 GitHub。

---

## 二、场景 B：远程连接 Claude Code（纯终端看不到本地文件），怎么实时看到并审阅它的修改？

当你 SSH 到远端跑 `claude` 时，最大的痛苦是“它在哗哗改好几个 `.md` / `.py` 文件，但终端滚屏太快看不清全貌”。下面按体验从轻到重给你 **4 个实战利器**：

### 利器 1：直接用 Cursor / VS Code `Remote-SSH` 打开同一目录（最直观，零配置）
即使你在独立终端（如 iTerm2 + tmux）跑远程 `claude`，也可以用本地 Cursor `Remote-SSH` 连上同一台机器打开 `/path/to/Research-Notes`：
- 左边文件树实时刷新；
- 点开左侧 **Source Control（Git 图标）**，Claude Code 每改完一个文件，你点一下就能看到红绿并排 Diff 和 Markdown Preview（`Cmd+Shift+V`）！

### 利器 2：连不上 Remote-SSH（如跳板机/受限容器）时 —— 端口转发 + 远端轻量实时网页预览器
如果那台机器装不了 VS Code Server（只有纯 SSH 命令行），只需在 SSH 登录时加 `-L 8899:127.0.0.1:8899`，在远端仓库根目录跑一行命令即可在**你本地浏览器 `http://localhost:8899`** 实时看完整目录树、渲染后的 Markdown 和 Git Diff：
```bash
# 1. 本地登录时映射端口：
ssh -L 8899:127.0.0.1:8899 user@remote-host

# 2. 在远端仓库里一键起 Markdown 实时渲染服务（任选其一）：
npx -y docsify-cli serve . --port 8899
# 或者用 Python 自带 HTTP 服务秒看全部文件：
python3 -m http.server 8899 --bind 127.0.0.1
```

### 利器 3：后台 2 秒级自动增量同步回你本地文件夹（`rsync` 循环 / `mutagen`）
如果你习惯直接用本地 Typora / Obsidian / 本地编辑器看文件，在你自己电脑开一个小终端挂着单向实时镜像，远端 Claude Code 一保存，2 秒内自动出现在你本地桌面文件夹：
```bash
# 在你自己电脑执行（每 3 秒把远端改动增量拉到本地预览目录，极省流量）：
while true; do
  rsync -az --delete --exclude='.git' user@remote-host:~/Research-Notes/ ~/Desktop/remote-cc-mirror/
  sleep 3
done
```

### 利器 4：Claude Code 终端内部自带的必会快捷键与分屏法
在远端 `tmux` 里左右分两屏（`tmux new -s cc` 后按 `Ctrl+b %`）：
- **左屏跑 `claude`**：随时输入 `/diff` 查看本轮会话未提交的全部代码差异，或按 `!git status` / `!git diff --stat` 直接在对话框内执行 shell 检查；
- **右屏挂实时状态看板**：跑 `watch -n 2 "git status -s && echo '---' && git diff --stat"`，它动了哪个文件、加了多少行删了多少行，右半屏实时跳动一目了然！
