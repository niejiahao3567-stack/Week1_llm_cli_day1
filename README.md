# LLM CLI 调用工具

基于 Python 的交互式大模型命令行聊天工具，支持连续对话、历史持久化和终端美化。

## 功能

- 支持 OpenAI-compatible API（DeepSeek / 通义千问 / OpenAI 等）
- 连续多轮对话，模型记住上下文
- 对话历史自动保存到 JSON 文件
- Rich 终端美化（Markdown 渲染）
- 内置命令：/help /history /clear /model

## 快速开始

### 1. 克隆项目

```bash
git clone <your-repo-url>
cd week1_llm_cli
2. 创建虚拟环境
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate
3. 安装依赖
pip install httpx python-dotenv rich
4. 配置 API Key
cp .env.example .env
# 编辑 .env，填入你的 API Key
5. 运行
python main.py
项目结构
week1_llm_cli/
├── app/
│   ├── __init__.py
│   ├── config.py          # .env 配置读取
│   ├── history.py         # JSON 历史持久化
│   ├── llm_client.py      # 同步 LLM 客户端
│   ├── async_llm_client.py # 异步 LLM 客户端
│   ├── api_client.py      # HTTP 客户端（同步+异步）
│   ├── timer.py           # 异步计时装饰器
│   └── cli.py             # CLI 交互核心
├── data/                  # 对话历史存储
├── .env.example           # 配置模板
├── .gitignore
├── requirements.txt
├── README.md
└── main.py                # 入口
命令
命令	说明
/help	显示帮助
/history	查看最近对话
/clear	清空上下文
/model	显示当前模型
/exit	退出

**运行方式：**

```bash
# 确认 .env 已配置
cat .env

# 安装 Rich（如果没有）
pip install rich

# 启动
python -m app.main5