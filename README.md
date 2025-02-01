# DeepSeek 监测工具

这是一个用于监测 DeepSeek API 和网页版状态的自动化工具。

## 功能特性

- 监测 DeepSeek API 的可用性和响应时间
- 监测 DeepSeek 网页版的可访问性
- 自动记录监测结果
- 支持多种推送通知方式（Server酱、Telegram）
- 每10分钟自动检测一次

## 配置说明

在 GitHub 仓库的 Settings -> Secrets and variables -> Actions 中设置以下 secrets：

### DeepSeek API 配置
- `DEEPSEEK_API_KEY`：DeepSeek API 密钥

### Server酱配置（国内推送）
- `ENABLE_SERVERCHAN`：是否启用 Server酱 推送（true/false）
- `SERVERCHAN_KEY`：Server酱的 SendKey（从 https://sct.ftqq.com/ 获取）

### Telegram 配置（国外推送）
- `ENABLE_TELEGRAM`：是否启用 Telegram 推送（true/false）
- `TELEGRAM_BOT_TOKEN`：Telegram Bot Token（从 @BotFather 获取）
- `TELEGRAM_CHAT_ID`：接收消息的用户 ID 或群组 ID（从 @userinfobot 获取）

### 邮件通知配置（可选）
- `ENABLE_EMAIL`：是否启用邮件通知（true/false）
- `SMTP_SERVER`：SMTP 服务器地址
- `SMTP_PORT`：SMTP 服务器端口
- `SMTP_USERNAME`：邮箱账号
- `SMTP_PASSWORD`：邮箱密码或应用专用密码
- `ALERT_RECIPIENTS`：接收通知的邮箱地址列表（逗号分隔）

## 安装

1. 克隆仓库：
```bash
git clone [repository-url]
cd deepseek_monitor
```

2. 安装依赖：
```bash
pip install -r requirements.txt
```

## 配置

1. 在 `config` 目录下创建 `.env` 文件
2. 配置必要的环境变量：
   - DEEPSEEK_API_KEY（如果需要）
   - 其他配置项

## 使用方法

1. Fork 本仓库
2. 在 GitHub 设置中配置所需的 secrets
3. 启用 GitHub Actions
4. 程序会自动每10分钟运行一次监控检查

## 项目结构

```
deepseek_monitor/
├── src/           # 源代码目录
├── tests/         # 测试文件目录
├── config/        # 配置文件目录
└── requirements.txt
```

## 推送说明

- 国内用户建议使用 Server酱 推送（推送到微信）
- 国外用户建议使用 Telegram Bot 推送
- 可以同时启用多种推送方式 