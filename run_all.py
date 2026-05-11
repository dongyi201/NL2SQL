# -*- coding: utf-8 -*-
"""
快速启动脚本 - 同时启动后端API服务和前端开发服务器
"""

import subprocess
import time
import os
import sys

backend_dir = os.path.dirname(os.path.abspath(__file__))
frontend_dir = os.path.join(backend_dir, "frontend")

print("\n" + "=" * 50)
print("NL2SQL 快速启动")
print("=" * 50)

print("\n正在启动后端 API 服务 (端口 8000)...")
backend_process = subprocess.Popen(
    [sys.executable, "server.py"],
    cwd=backend_dir,
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL,
    stdin=subprocess.DEVNULL
)

time.sleep(1)

print("正在启动前端服务 (端口 3000)...")
frontend_process = subprocess.Popen(
    "npm run dev",
    cwd=frontend_dir,
    shell=True,
    stdout=None,
    stderr=None,
    stdin=None
)

print("\n" + "=" * 50)
print("服务已启动!")
print("  后端: http://localhost:8000")
print("  前端: http://localhost:3000")
print("\n按 Ctrl+C 停止所有服务")
print("=" * 50)

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("\n正在关闭服务...")
    backend_process.terminate()
    frontend_process.terminate()
    backend_process.wait()
    frontend_process.wait()