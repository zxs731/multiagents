# 多助手智能对话应用

## 【视频链接】你的私人AI智囊团，400多位专家24小时待命！开源、本地、免费，这才是未来生活工作的终极形态！ https://www.bilibili.com/video/BV1ysCCBTEmc
## 本项目是一个基于 Streamlit 和 LangChain 的多智能助手对话平台，支持自定义助手、会话管理和收藏、对话记录持久化等功能。

## 主要特性
- 多智能助手（可自定义配置、分组、收藏）
- 会话管理：多轮对话历史记录，支持新建/切换/删除
- 收藏助手并置顶显示
- 支持对助手按名称搜索过滤
- 使用 OpenAI/GPT-4 等模型流式响应
- 全界面 Streamlit Web UI
- 对话内容可持久化存储

## 环境要求
- Python 3.10+
- 推荐 macOS 或 Linux 环境（Windows 兼容性良好）

## 安装步骤
1. 克隆本仓库
   ```bash
   git clone <your-repo-url>
   cd <your-repo>
   ```
2. 安装依赖
   ```bash
   pip install -r requirements.txt
   ```
3. 添加配置文件
   - 在根目录创建 `.env` 文件，根据你的 OpenAI 账号及模型配置填入：
     ```env
     openai_base_url=https://api.openai.com/v1
     openai_api_key=sk-xxxxxx
     model=gpt-4.1
     ```
   - 编辑 `config.json`（已内置400多角色）：
     ```json
     {
       "ASSISTANTS": [
         {
           "key": "gpt_default",
           "title": "通用助手",
           "system_prompt": "你是一个专业的中文助手。"
         },
         {
           "key": "dev_gpt",
           "title": "开发助手",
           "system_prompt": "你是专业程序员答疑助手。"
         }
         // 可自定义更多助手
       ]
     }
     ```

## 运行方法
```bash
streamlit run app.py
```

首次运行会自动创建和维护每个助手的对话历史（JSON文件保存在 histories 目录下）。

## 目录结构
- `app.py`          主应用入口
- `config.json`     助手配置文件
- `.env`            OpenAI 密钥及模型配置
- `histories/`      会话历史存储目录
- `requirements.txt`依赖列表

## 常见问题
- KEY/BASE_URL/模型参数错误将导致无法正常对话，请检查`.env`。
- 新助手添加后需刷新页面。

## 联系 & 贡献
- 欢迎提 Issue、PR
- 视频 https://www.bilibili.com/video/BV1ysCCBTEmc

---
