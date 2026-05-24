# 部署步骤

## 1. 本地测试

```bash
python scripts/generate.py
# 输出: output/china-holidays.ics
```

## 2. 创建 GitHub 仓库

1. 在 GitHub 新建仓库（建议命名：`china-holidays`）
2. 将本项目推送到 `main` 分支：

```bash
git init
git add .
git commit -m "init: china holidays calendar"
git remote add origin https://github.com/YOUR_NAME/china-holidays.git
git push -u origin main
```

## 3. 启用 GitHub Pages

仓库 → Settings → Pages → Source 选择 **Deploy from a branch** → 分支选 **gh-pages** → 保存

## 4. 触发首次构建

推送代码后 GitHub Actions 会自动运行。也可手动触发：
仓库 → Actions → "Generate & Publish Calendar" → Run workflow

## 5. 获取订阅链接

构建完成后，访问：
```
https://YOUR_NAME.github.io/china-holidays/
```

订阅链接为：
```
webcal://YOUR_NAME.github.io/china-holidays/china-holidays.ics
```

## 6. 每年更新流程

1. 国务院发布调休公告（通常 11-12 月）
2. 更新 `data/YYYY.json`，填入官方数据
3. `git push` → GitHub Actions 自动重新生成并发布
4. 所有订阅用户的 iPhone 在下次刷新时自动同步（最长 24 小时）
