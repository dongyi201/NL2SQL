# -*- coding: utf-8 -*-
import requests
import yaml
from pathlib import Path

config_path = Path("config/llm_config.yaml")

before = yaml.safe_load(open(config_path, encoding="utf-8"))
print("保存前 deepseek:", before.get("llm", {}).get("api_keys", {}).get("deepseek", ""))

resp = requests.post("http://localhost:8000/api/config/api-key", json={
    "provider": "deepseek",
    "api_key": "sk-test-save-12345"
})

print("状态码:", resp.status_code)
print("响应:", resp.json())

after = yaml.safe_load(open(config_path, encoding="utf-8"))
print("保存后 deepseek:", after.get("llm", {}).get("api_keys", {}).get("deepseek", ""))
