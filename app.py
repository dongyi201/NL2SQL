# -*- coding: utf-8 -*-
"""
NL2SQL 主入口 —— 命令行 + 示例运行。

支持三种模式：
  --mode rule   : 纯规则引擎（快速，零成本）
  --mode llm    : 纯 LLM（灵活，通用）
  --mode hybrid : 混合模式（默认，规则优先，复杂场景走 LLM）

用法：
  # 混合模式（默认）
  python app.py "最近7天华北地区每天的销售额"
  python app.py "最近7天华北地区每天的销售额" --dialect doris

  # 强制使用 LLM
  python app.py "张三的订单总额" --mode llm

  # 强制使用规则引擎
  python app.py "最近7天销售额" --mode rule

  # 同时输出所有方言
  python app.py "最近7天每天销售额" --all

  # Demo 演示
  python app.py --demo

配置 LLM：
  - 方式1: 设置环境变量（推荐）
    export OPENAI_API_KEY=sk-...
    export DASHSCOPE_API_KEY=sk-...    (阿里云通义千问)
    export ANTHROPIC_API_KEY=sk-...    (Claude)
    export MOONSHOT_API_KEY=sk-...    (Kimi)
    export MINIMAX_API_KEY=sk-...     (MiniMax)
    export DEEPSEEK_API_KEY=sk-...    (DeepSeek)

  - 方式2: 命令行参数
    python app.py "..." --provider deepseek --model deepseek-chat
"""

import sys
import os
import argparse
import json
from src.unified_pipeline import UnifiedPipeline


def _get_arg_parser():
    parser = argparse.ArgumentParser(
        description="NL2SQL 自然语言转SQL工具（支持规则引擎 + LLM）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "text",
        nargs="?",
        help="要转换的自然语言文本",
    )
    parser.add_argument(
        "--dialect", "-d",
        default="hive",
        choices=["hive", "doris", "starrocks", "flink"],
        help="目标 SQL 方言 (默认: hive)",
    )
    parser.add_argument(
        "--mode", "-m",
        default="hybrid",
        choices=["rule", "llm", "hybrid"],
        help=(
            "运行模式 (默认: hybrid):\n"
            "  rule   - 纯规则引擎，速度快，零成本\n"
            "  llm    - 纯大模型，最灵活，通用\n"
            "  hybrid - 规则优先，不够时走 LLM（推荐）"
        ),
    )
    parser.add_argument(
        "--provider", "-p",
        default="dashscope",
        choices=["openai", "claude", "kimi", "dashscope", "minimax", "deepseek"],
        help="LLM 提供者 (默认: dashscope)",
    )
    parser.add_argument(
        "--model", "-M",
        default=None,
        help="LLM 模型名称 (默认: provider 默认模型)",
    )
    parser.add_argument(
        "--api-key",
        default=None,
        help="LLM API Key（优先从环境变量读取）",
    )
    parser.add_argument(
        "--all", "-a",
        action="store_true",
        help="同时输出所有方言",
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        help="运行内置示例",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="显示详细信息（IR 中间表示）",
    )
    parser.add_argument(
        "--no-schema",
        action="store_true",
        help="LLM模式不使用本地schema（自由模式，完全由大模型推断）",
    )
    return parser


def print_result(result, verbose: bool = False):
    print("=" * 60)
    print(f"[INPUT] {result.raw_text}")
    print(f"[DIALECT] {result.dialect}")
    print(f"[MODE] {result.source}")
    print(f"[CONFIDENCE] {result.confidence * 100:.0f}%")
    print(f"[ELAPSED] {result.elapsed_ms:.2f}ms")
    if result.error:
        print(f"[ERROR] {result.error}")
    if verbose and result.ir:
        print(f"\n[IR]:")
        print(json.dumps(result.ir, ensure_ascii=False, indent=2))
    print(f"\n[GENERATED SQL]:\n{result.sql}")
    print("=" * 60)


def run_demo(pipeline):
    test_cases = [
        "最近7天华北地区每天的销售额",
        "最近一个月按地区统计的用户数",
        "订单金额超过10000的订单",
        "最近7天每天去重用户数",
        "前10名消费额最高的用户",
    ]

    print("\n" + "+" + "=" * 58 + "+")
    print("|" + "  NL2SQL Demo - 自然语言 -> SQL 演示".center(56) + "|")
    print("+" + "=" * 58 + "+" + "\n")

    for text in test_cases:
        result = pipeline.convert(text, dialect="hive")
        print_result(result)
        print()

    print("\n" + "-" * 60)
    print("  Cross-Dialect Comparison")
    print("-" * 60)
    text = "最近7天华北地区每天的销售额"
    results = pipeline.convert_all_dialects(text)
    for dialect_name, r in results.items():
        print(f"\n--- {dialect_name.upper()} ---")
        print(r.sql)


def main():
    parser = _get_arg_parser()
    args = parser.parse_args()

    if args.text is None and not args.demo:
        parser.print_help()
        return

    # 确定模型
    model_map = {
        "openai": "gpt-4o-mini",
        "claude": "claude-3-5-sonnet-20241022",
        "kimi": "moonshot-v1-8k",
        "dashscope": "qwen-turbo",
        "minimax": "abab6.5s-chat",
        "deepseek": "deepseek-v4-flash",
    }
    model = args.model or model_map.get(args.provider, "qwen-turbo")

    # 初始化 Pipeline
    try:
        pipeline = UnifiedPipeline(
            mode=args.mode,
            llm_provider=args.provider,
            llm_model=model,
            llm_api_key=args.api_key,
        )
    except Exception as e:
        print(f"[ERROR] 初始化失败: {e}")
        print("提示: 请确认已安装所需依赖: pip install openai anthropic")
        return

    if args.demo or args.text is None:
        run_demo(pipeline)
        return

    if args.all:
        results = pipeline.convert_all_dialects(args.text)
        print(f"\n=== All Dialects for: {args.text} ===\n")
        for name, r in results.items():
            print(f"--- {name.upper()} ({r.source}, {r.confidence*100:.0f}%) ---")
            print(r.sql)
            print()
    else:
        use_schema = not args.no_schema
        result = pipeline.convert(args.text, dialect=args.dialect, use_schema=use_schema)
        print_result(result, verbose=args.verbose)


if __name__ == "__main__":
    main()