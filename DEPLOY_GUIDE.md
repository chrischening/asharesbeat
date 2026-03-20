# A股利好监控 - 部署指南

## 方案概览

**GitHub Pages（免费托管）+ GitHub Actions（自动数据刷新）**

- 零成本，无需服务器
- 盘中每15分钟自动刷新数据
- 支持绑定自定义域名 www.Asharesbeat.com
- 可选配置 Telegram Bot 推送

---

## 第一步：创建 GitHub 仓库

1. 登录 https://github.com ，点击右上角 **+** → **New repository**
2. 仓库名填 `asharesbeat`（或你喜欢的名字）
3. 选择 **Public**（GitHub Pages 免费版需要公开仓库）
4. 点击 **Create repository**

## 第二步：上传代码

将本部署包内所有文件上传到仓库：

```
asharesbeat/
├── .github/workflows/refresh.yml   ← GitHub Actions 自动刷新
├── monitor.py                       ← Python 后端
├── template.html                    ← 前端模板
└── docs/index.html                  ← 生成的面板（首次已包含）
```

**上传方法（命令行）：**
```bash
cd asharesbeat
git init
git add .
git commit -m "init: A股利好监控系统"
git branch -M main
git remote add origin https://github.com/你的用户名/asharesbeat.git
git push -u origin main
```

**或者用 GitHub 网页上传：** 进入仓库页面 → Add file → Upload files

## 第三步：开启 GitHub Pages

1. 进入仓库 → **Settings** → 左侧 **Pages**
2. Source 选择 **Deploy from a branch**
3. Branch 选择 `main`，文件夹选择 `/docs`
4. 点击 **Save**
5. 等待 1-2 分钟，页面会显示访问链接：`https://你的用户名.github.io/asharesbeat/`

## 第四步：启用 GitHub Actions 自动刷新

1. 进入仓库 → **Settings** → 左侧 **Actions** → **General**
2. 滚动到底部 **Workflow permissions**，选择 **Read and write permissions**
3. 点击 **Save**
4. 进入 **Actions** 标签页，如果看到 workflow 被禁用，点击 **I understand my workflows, go ahead and enable them**
5. 可以手动触发一次：Actions → Refresh Dashboard → Run workflow

**刷新计划（北京时间，工作日）：**
- 08:20 盘前刷新
- 09:15 - 14:45 每15分钟刷新
- 15:30 盘后刷新
- 21:00 晚间刷新

## 第五步：购买域名并绑定

### 购买域名

推荐域名注册商（国际域名无需备案）：
- **Namecheap**: https://www.namecheap.com → 搜索 `asharesbeat.com`
- **Cloudflare Registrar**: https://www.cloudflare.com/products/registrar/ （价格最低）
- **GoDaddy**: https://www.godaddy.com

`.com` 域名通常 $8-12/年。

### 配置 DNS 解析

购买域名后，在域名注册商的 DNS 管理面板添加以下记录：

```
类型    名称    值
CNAME   www     你的用户名.github.io
A       @       185.199.108.153
A       @       185.199.109.153
A       @       185.199.110.153
A       @       185.199.111.153
```

### 在 GitHub 绑定域名

1. 进入仓库 → **Settings** → **Pages**
2. **Custom domain** 填入 `www.asharesbeat.com`
3. 勾选 **Enforce HTTPS**
4. 等待 DNS 生效（通常 10-30 分钟）

### 创建 CNAME 文件

在 `docs/` 目录下创建一个 `CNAME` 文件（无扩展名），内容为：
```
www.asharesbeat.com
```

---

## 可选：配置 Telegram 推送

1. 进入仓库 → **Settings** → **Secrets and variables** → **Actions**
2. 添加以下 Secrets：
   - `TG_TOKEN`: 你的 Telegram Bot Token
   - `TG_CHAT_ID`: 你的 Chat ID
   - `TG_CHANNEL`: 频道名（如 `@your_channel`，可选）

配置后，每次 GitHub Actions 刷新数据时会同时推送 Telegram 汇总。

---

## 常见问题

**Q: GitHub Actions 免费额度够用吗？**
A: 免费账户每月 2000 分钟。本项目每次运行约 2-3 分钟，工作日每天约 30 次 ≈ 每月 1500-2000 分钟。如果超出，可以减少刷新频率（编辑 refresh.yml 中的 cron 表达式）。

**Q: 可以用私有仓库吗？**
A: 可以，但 GitHub Pages 的私有仓库需要 GitHub Pro（$4/月）。免费方案需要公开仓库。

**Q: 数据有延迟吗？**
A: GitHub Actions cron 可能有 5-15 分钟延迟（GitHub 不保证精确执行时间），加上数据抓取约 1-2 分钟，总延迟约 5-20 分钟。

**Q: 想要更实时的方案？**
A: 租一台云服务器（阿里云/腾讯云 轻量 ¥40-60/月），运行 `python monitor.py --daemon` 即可实现精确 15 分钟刷新，并支持 Telegram Bot 实时交互。
