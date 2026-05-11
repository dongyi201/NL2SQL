# -*- coding: utf-8 -*-
"""
简化的测试脚本 - 逐步测试后端各组件
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 50)
print("1. 测试 FastAPI 导入...")
try:
    from fastapi import FastAPI, HTTPException
    from pydantic import BaseModel
    print("   ✓ FastAPI 导入成功")
except Exception as e:
    print(f"   ✗ FastAPI 导入失败: {e}")
    print("   解决方法: pip install fastapi uvicorn pydantic")
    sys.exit(1)

print("\n" + "=" * 50)
print("2. 测试 SchemaManager 导入...")
try:
    from src.schema.metadata import SchemaManager
    schema = SchemaManager()
    print(f"   ✓ SchemaManager 加载成功，共 {len(schema.tables)} 张表")
except Exception as e:
    print(f"   ✗ SchemaManager 加载失败: {e}")
    sys.exit(1)

print("\n" + "=" * 50)
print("3. 测试 LLMConfig 导入...")
try:
    from src.llm.config_loader import get_llm_config
    config = get_llm_config()
    print("   ✓ LLMConfig 加载成功"
    )
except Exception as e:
    print(f"   ✗ LLMConfig 加载失败: {e}")
    sys.exit(1)

print("\n" + "=" * 50)
print("4. 测试 UnifiedPipeline 导入...")
try:
    from src.unified_pipeline import UnifiedPipeline
    print("   ✓ UnifiedPipeline 导入成功")
except Exception as e:
    print(f"   ✗ UnifiedPipeline 导入失败: {e}")
    sys.exit(1)

print("\n" + "=" * 50)
print("5. 测试 server.py 导入...")
try:
    import server
    print("   ✓ server.py 导入成功")
    print(f"   ✓ API 数量: {len([r for r in dir(server.app.routes) if not r.startswith('_')])}")
except Exception as e:
    print(f"   ✗ server.py 导入失败: {e}")
    sys.exit(1)

print("\n" + "=" * 50)
print("所有组件测试通过！")
print("\n正在启动后端服务...")
print("请访问: http://localhost:8000")
print("按 Ctrl+C 停止")
print("=" * 50)

import uvicorn
uvicorn.run(server.app, host="0.0.0.0", port=8000)