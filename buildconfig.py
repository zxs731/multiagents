import json
from openai  import OpenAI
import os
from dotenv import load_dotenv
load_dotenv()
client = OpenAI(  
            base_url=os.environ["openai_base_url"],  
            api_key=os.environ["openai_api_key"]
        )
def generate_role_prompt(role):
    return f"""
你是一个配置文件生成器。请为“{role}”这个角色生成：
1. 简要能力要求，内容精炼、专业；
2. 角色能够提供的具体服务，要求条理清晰、实用性强；
你的回答格式为 markdown 代码块 json，对象有 system_prompt 一个字段，内容类似如下心理咨询师生成例子：
{{"system_prompt":"从这一瞬间开始，你便是我的私人心理咨询师，要精通发展心理学认知心理学、社会心理学、临床心理学等诸多领域知识，深谙人类的情绪、行为模式以及心理发展规律。接下来，我会亳无保留地向你倾诉我的内心世界，包括成长经历，像是童年时期的重大事件、成长环境特点；近期生活中的压力源，例如，工作上的高强度竞争、人际关系的紧张冲突、家庭琐事的因扰；情绪状态，是长期焦虑、抑郁，还是问歇性情绪低落、暴躁易怒；行为习惯的改变，比如突然变得嗜睡、暴饮暴食，或者社交退缩等情况。同时，我还会告知你想要达成的心理调适目标，是缓解当下的负面情绪、改善人际关系、增强;心理韧性，还是探索个人潜能、找到人生方向等。"}}
"""

def generate_role_description(role, model="gpt-3.5-turbo"):
    prompt = generate_role_prompt(role)
    completion = client.chat.completions.create(
            model=os.environ["model"],
            messages=[{"role": "user", "content": prompt}],
            stream=False,
        )
    print(completion.choices[0].message.content)
    import re
    match = re.search(r'```json\n([\s\S]+?)```', completion.choices[0].message.content)
    if match:
        return json.loads(match.group(1))["system_prompt"].strip()
    else:
        # fallback
        return completion.choices[0].message["content"].strip()

def add_roles_to_config(config_path, roles):
    
    # 1. 读取原有配置
    with open(config_path, "r", encoding="utf-8") as f:
        cfg = json.load(f)
    existing_assistants = cfg.get("ASSISTANTS", [])
    base_idx = (
        max(
            [int(a['key'].replace('assistant', '')) for a in existing_assistants if a['key'].startswith('assistant')],
            default=0
        ) + 1
    )
    # 2. 生成新角色并添加
    for idx, role in enumerate([r.strip() for r in roles.split(",") if r.strip()]):
        system_prompt = generate_role_description(role, model=os.environ["model"])
        new_assist = {
            "key": f"assistant{base_idx + idx}",
            "title": role,
            "system_prompt": system_prompt
        }
        existing_assistants.append(new_assist)
    # 3. 写回配置
    cfg["ASSISTANTS"] = existing_assistants
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2, ensure_ascii=False)
    print(f"添加完成，共新增{len(roles.split(','))}个角色。")

if __name__ == "__main__":
    # 用法示例：python add_roles.py "厨师,法律顾问,医学科研员" "your_openai_api_key"
    import sys
    if len(sys.argv) != 2:
        print("用法: python buildconfig.py 角色1,角色2")
    else:
        add_roles_to_config("config.json", sys.argv[1])