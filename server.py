# -*- coding: utf-8 -*-
"""
FastAPI 后端服务 —— 提供 NL2SQL 的 REST API 接口。
保留原有命令行功能不变，同时提供 Web API 服务。
"""

import os
import sys
import json
import logging
from typing import Optional
from dataclasses import dataclass
from datetime import datetime

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi import Body
from pydantic import BaseModel

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 确保 src 在 path 中
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.unified_pipeline import UnifiedPipeline
from src.schema.metadata import SchemaManager
from src.llm.config_loader import get_llm_config


# ============================================================
# FastAPI 应用初始化
# ============================================================

app = FastAPI(
    title="NL2SQL API",
    description="自然语言转SQL工具 - 支持规则引擎 + LLM",
    version="1.0.0",
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# 数据模型
# ============================================================

class ConvertRequest(BaseModel):
    text: str
    dialect: str = "hive"
    mode: str = "hybrid"
    provider: str = "deepseek"
    model: Optional[str] = None
    temperature: float = 0.1
    use_schema: bool = True  # 是否传入本地 schema 信息
    api_key: Optional[str] = None  # 测试连接时传入的临时 API Key


class ConvertResponse(BaseModel):
    sql: str = ""
    dialect: str = "hive"
    source: str = ""
    confidence: float = 0.0
    elapsed_ms: float = 0.0
    ir: dict = {}
    error: Optional[str] = None


class ApiKeyRequest(BaseModel):
    provider: str
    api_key: str


class ValidateSQLRequest(BaseModel):
    sql: str
    dialect: str = "hive"


# ============================================================
# 全局 Pipeline 实例（延迟初始化）
# ============================================================

_pipeline_cache = {}


def get_pipeline(mode: str, provider: str, model: Optional[str] = None, api_key: Optional[str] = None):
    """获取或创建 Pipeline 实例"""
    if api_key:
        # 使用临时 API Key 时不缓存（测试连接场景）
        return UnifiedPipeline(
            mode=mode,
            llm_provider=provider,
            llm_model=model,
            llm_api_key=api_key,
        )
    cache_key = f"{mode}_{provider}_{model}"
    if cache_key not in _pipeline_cache:
        _pipeline_cache[cache_key] = UnifiedPipeline(
            mode=mode,
            llm_provider=provider,
            llm_model=model,
        )
    return _pipeline_cache[cache_key]


def clear_pipeline_cache():
    """清除流水线缓存（API Key 更新后调用）"""
    _pipeline_cache.clear()


# ============================================================
# API 路由
# ============================================================

@app.get("/")
async def root():
    """根路径 - 返回欢迎信息"""
    return {
        "name": "NL2SQL API",
        "version": "1.0.0",
        "description": "自然语言转SQL工具 - 支持规则引擎 + LLM",
        "endpoints": {
            "convert": "/api/convert",
            "schemas": "/api/schemas",
            "dialects": "/api/dialects",
            "providers": "/api/providers",
            "config": "/api/config",
            "health": "/health",
        },
    }


@app.get("/health")
async def health():
    """健康检查"""
    return {"status": "ok", "timestamp": datetime.now().isoformat()}


@app.post("/api/convert", response_model=ConvertResponse)
async def convert(request: ConvertRequest):
    """
    自然语言转SQL核心接口

    Args:
        request: ConvertRequest {
            text: str,           # 自然语言输入
            dialect: str,         # SQL方言 (hive/doris/starrocks/flink)
            mode: str,           # 运行模式 (rule/llm/hybrid)
            provider: str,       # LLM提供者
            model: Optional[str], # 模型名称
            temperature: float   # LLM温度参数
        }

    Returns:
        ConvertResponse: {
            sql: str,            # 生成的SQL
            dialect: str,         # 方言
            source: str,         # 来源 (rule/llm)
            confidence: float,   # 置信度
            elapsed_ms: float,   # 耗时
            ir: dict,            # 中间表示
            error: Optional[str] # 错误信息
        }
    """
    try:
        logger.info(f"收到转换请求: text={request.text[:50]}..., mode={request.mode}, dialect={request.dialect}")

        pipeline = get_pipeline(request.mode, request.provider, request.model, request.api_key)

        result = pipeline.convert(
            text=request.text,
            dialect=request.dialect,
            temperature=request.temperature,
            use_schema=request.use_schema,
        )

        logger.info(f"转换结果: sql={result.sql[:50] if result.sql else 'empty'}..., source={result.source}")

        return ConvertResponse(
            sql=result.sql,
            dialect=result.dialect,
            source=result.source,
            confidence=result.confidence,
            elapsed_ms=result.elapsed_ms,
            ir=result.ir,
            error=result.error,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/schemas")
async def get_schemas():
    """
    获取数据字典（表和字段信息）

    Returns:
        {
            tables: [
                {
                    name: str,
                    chinese_name: str,
                    description: str,
                    columns: [
                        {
                            name: str,
                            chinese_name: str,
                            type: str,
                            aliases: list,
                            enum_values: list
                        }
                    ]
                }
            ],
            relations: list,
            synonym_map: dict
        }
    """
    try:
        schema = SchemaManager()
        tables = []
        for t in schema.tables:
            tables.append({
                "name": t.name,
                "chinese_name": t.chinese_name,
                "description": t.description,
                "columns": [
                    {
                        "name": c.name,
                        "chinese_name": c.chinese_name,
                        "type": c.type,
                        "aliases": c.aliases,
                        "enum_values": c.enum_values if isinstance(c.enum_values, list) else list(c.enum_values.keys()) if isinstance(c.enum_values, dict) else [],
                    }
                    for c in t.columns
                ]
            })

        return {
            "tables": tables,
            "relations": schema.relations,
            "synonym_map": schema.synonym_map,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/dialects")
async def get_dialects():
    """获取支持的 SQL 方言列表"""
    return {
        "dialects": [
            {"id": "hive", "name": "Hive SQL", "description": "Hadoop 数据仓库 SQL"},
            {"id": "doris", "name": "Doris", "description": "Apache Doris SQL"},
            {"id": "starrocks", "name": "StarRocks", "description": "StarRocks SQL"},
            {"id": "flink", "name": "Flink SQL", "description": "Apache Flink SQL"},
        ]
    }


@app.get("/api/providers")
async def get_providers():
    """获取支持的 LLM 提供者列表（从配置文件动态读取）"""
    config = get_llm_config()
    providers = []
    for name in ["deepseek", "dashscope", "kimi", "minimax", "openai", "claude"]:
        p_config = config.get_provider_config(name)
        if p_config:
            models = [m.get("id") for m in p_config.get("models", [])]
            providers.append({
                "id": name,
                "name": p_config.get("display_name", name),
                "models": models,
            })
    return {"providers": providers}


@app.post("/api/config/api-key")
async def update_api_key(request: ApiKeyRequest):
    """
    更新指定提供者的 API Key

    Args:
        request: {
            provider: str,   # 提供者名称
            api_key: str     # API Key
        }

    Returns:
        {"success": bool, "message": str}
    """
    try:
        import yaml
        from pathlib import Path

        project_root = Path(__file__).parent
        config_path = project_root / "config" / "llm_config.yaml"

        if not config_path.exists():
            raise HTTPException(status_code=404, detail="配置文件不存在")

        with open(config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)

        if "llm" not in config:
            config["llm"] = {}
        if "api_keys" not in config["llm"]:
            config["llm"]["api_keys"] = {}

        config["llm"]["api_keys"][request.provider] = request.api_key

        with open(config_path, "w", encoding="utf-8") as f:
            yaml.dump(config, f, allow_unicode=True, default_flow_style=False)

        from src.llm.config_loader import get_llm_config
        get_llm_config().reload()
        clear_pipeline_cache()  # 清除缓存，下次转换用新 Key

        return {"success": True, "message": f"{request.provider} API Key 已更新"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/config")
async def get_config():
    """获取当前配置信息"""
    config = get_llm_config()
    providers = []
    for name in ["deepseek", "dashscope", "kimi", "minimax", "openai", "claude"]:
        p_config = config.get_provider_config(name)
        if p_config:
            providers.append({
                "id": name,
                "display_name": p_config.get("display_name", name),
                "models": [m.get("id") for m in p_config.get("models", [])],
            })

    api_keys_status = {}
    for name in ["deepseek", "dashscope", "kimi", "minimax", "openai", "claude"]:
        key = config.get_api_key(name)
        api_keys_status[name] = "configured" if key else "not_configured"

    return {
        "default_provider": config._config.get("llm", {}).get("default_provider", "deepseek"),
        "providers": providers,
        "api_keys_status": api_keys_status,
        "dialect_default": config._config.get("dialect", {}).get("default", "hive"),
    }


@app.get("/api/history")
async def get_history():
    """获取历史记录（内存存储，重启后丢失）"""
    return {"history": []}


@app.post("/api/validate-sql")
async def validate_sql(request: ValidateSQLRequest):
    """
    验证 SQL 语法是否正确

    Args:
        request: {
            sql: str,      # SQL 语句
            dialect: str   # 方言 (hive/doris/starrocks/flink)
        }

    Returns:
        {
            valid: bool,
            error: str or None,
            sql: str or None,
            dialect: str
        }
    """
    try:
        from src.dialect.sqlglot_converter import SQLGlotDialectConverter

        validator = SQLGlotDialectConverter()
        valid, error, normalized_sql = validator.validate(request.sql, request.dialect)

        return {
            "valid": valid,
            "error": error,
            "sql": normalized_sql,
            "dialect": request.dialect,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/convert-sql")
async def convert_sql_dialect(request: ValidateSQLRequest):
    """
    转换 SQL 到指定方言

    Args:
        request: {
            sql: str,      # SQL 语句
            dialect: str   # 目标方言 (hive/doris/starrocks/flink)
        }

    Returns:
        {
            success: bool,
            sql: str or None,
            error: str or None,
            from_dialect: str,
            to_dialect: str
        }
    """
    try:
        from src.dialect.sqlglot_converter import SQLGlotDialectConverter

        validator = SQLGlotDialectConverter()
        valid, error, result_sql = validator.convert_dialect(request.sql, request.dialect)

        return {
            "success": valid,
            "sql": result_sql,
            "error": error,
            "from_dialect": "hive",
            "to_dialect": request.dialect,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# 静态文件服务（前端页面）
# ============================================================

frontend_path = os.path.join(os.path.dirname(__file__), "frontend", "dist")


@app.get("/app")
async def serve_frontend():
    """返回前端页面"""
    index_path = os.path.join(frontend_path, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "Frontend not found. Please run: python server.py --build-frontend"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)