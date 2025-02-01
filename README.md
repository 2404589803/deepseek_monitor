# DeepSeek 监测工具

这是一个用于监测 DeepSeek API 和网页版状态的自动化工具。

## 功能特性

- 监测 DeepSeek API 的可用性和响应时间
- 监测 DeepSeek 网页版的可访问性
- 自动记录监测结果
- 支持异常通知

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

1. 启动监测：
```bash
python src/main.py
```

## 项目结构

```
deepseek_monitor/
├── src/           # 源代码目录
├── tests/         # 测试文件目录
├── config/        # 配置文件目录
└── requirements.txt
``` 