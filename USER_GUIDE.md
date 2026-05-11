# NL2SQL 自然语言转 SQL 系统

## 项目简介

NL2SQL 是一个将自然语言转换为 SQL 语句的智能系统，支持 Hive、Doris、StarRocks、Flink 等多种 SQL 方言。系统采用混合架构，结合规则引擎和大语言模型（LLM），为数据仓库场景提供高效的 SQL 生成能力。

## 功能特性

### 1. 自然语言转 SQL
- 支持 Hive SQL、Doris SQL、StarRocks SQL、Flink SQL 四种方言
- 三种运行模式：混合模式（规则+LLM）、纯规则引擎、纯大模型
- 自动语法验证，确保生成的 SQL 符合目标方言规范
- 置信度评估，展示结果可信程度

### 2. 数据字典管理
- 完整的表结构元数据展示（127+ 张数据表）
- 字段信息：字段名、类型、中文名、别名、枚举值
- 表关联关系可视化（254+ 条关联关系）
- 同义词映射，支持语义理解
- 分页浏览和关键词搜索

### 3. LLM 配置
- 支持多种 LLM 提供者：DeepSeek、通义千问、Kimi、MiniMax、Claude
- 可配置的模型选择
- 温度参数调节（控制输出随机性）
- API Key 安全管理

### 4. 转换历史
- 自动记录每次转换
- 查看历史 SQL 语句
- 复制和重新执行

## 快速开始

### 环境要求

- Python 3.8+
- Node.js 16+
- npm 或 yarn

### 安装依赖

```bash
# 安装 Python 依赖
pip install pyyaml openai dashscope anthropic

# 安装前端依赖
cd frontend
npm install
```

### 启动服务

```bash
# 方式一：一键启动前后端（推荐）
python run_all.py

# 方式二：分别启动
# 终端1 - 启动后端
python server.py

# 终端2 - 启动前端
cd frontend
npm run dev
```

### 访问地址

- 前端页面：http://localhost:3000
- 后端 API：http://localhost:8000
- API 文档：http://localhost:8000/docs

## 使用指南

### 1. SQL 转换页面

#### 基本操作

1. 在左侧输入框输入自然语言查询
   ```
   示例：统计每个省份的订单金额
   ```

2. 选择目标 SQL 方言
   - Hive（默认）
   - Doris
   - StarRocks
   - Flink

3. 选择运行模式
   - **混合模式**：规则引擎优先，复杂查询自动切换 LLM
   - **规则引擎**：纯规则匹配，响应快但能力有限
   - **大模型**：使用 LLM 生成，能力强大但需要 API Key

4. 点击"转换"按钮查看结果

#### Schema 控制

- **参考模式**：LLM 会参考本地数据字典，更精准但受限于已知表结构
- **自由模式**：LLM 自由发挥，可能生成不在数据字典中的表

#### SQL 验证

- 生成的 SQL 会自动进行语法验证
- 验证结果会显示在输出区域
- 可点击"验证"按钮手动检查

### 2. 数据字典页面

#### 表列表浏览

1. 切换到"数据表"标签
2. 支持分页浏览（每页 10/20/50 张表）
3. 支持关键词搜索（搜索表名或字段）
4. 点击表名展开查看字段详情

#### 表详情

- 表名和中文名
- 表描述
- 字段列表：字段名、类型、中文名、别名、枚举值

#### 表关联关系

1. 切换到"表关联关系"标签
2. 查看表与表之间的数据流向
3. 源表 → 目标表 的依赖关系

#### 同义词映射

1. 切换到"同义词映射"标签
2. 查看系统支持的同义词
3. 关键词 → 标准字段/表名 的映射关系

### 3. 配置页面

#### LLM 配置

1. 选择 LLM 提供者
2. 输入 API Key
3. 点击"测试连接"验证 Key 是否有效
4. 点击"保存到配置文件"持久化配置

#### 可配置的参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| 提供者 | LLM 服务提供商 | DeepSeek |
| 模型 | 具体模型版本 | deepseek-v4-flash |
| 温度 | 输出随机性（0-1） | 0.1 |
| 最大重试 | API 调用失败重试次数 | 3 |

### 4. 历史记录页面

- 自动保存每次转换记录
- 显示转换时间、输入、输出
- 支持复制 SQL 语句
- 支持删除单条或清空全部

## 配置文件说明

### LLM 配置 (config/llm_config.yaml)

```yaml
providers:
  deepseek:
    api_key: your-api-key
    models:
      - name: deepseek-v4-flash
        display_name: DeepSeek V4 Flash
      - name: deepseek-v4-pro
        display_name: DeepSeek V4 Pro
  # ... 其他提供者

settings:
  temperature: 0.1
  max_retries: 3
  timeout: 120
```

### 数据字典 (config/schema.yaml)

```yaml
datasource: doris_warehouse
tables:
  - name: ads.ads_activity_stats
    chinese_name: 活动统计
    description: 活动统计报表
    columns:
      - name: dt
        type: VARCHAR(255)
        chinese_name: 统计日期
        aliases: [日期, dt]
relations:
  - from_table: dws.dws_trade_activity_order_nd
    to_table: ads.ads_activity_stats
    relation_type: data_source
synonym_map:
  活动: column.ads.ads_activity_stats.activity_id
```

## 系统架构

```
┌─────────────────────────────────────────────────────────┐
│                     前端 (Vue 3)                        │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌────────┐  │
│  │ 转换页面  │  │数据字典   │  │ 配置页面  │  │ 历史   │  │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └───┬────┘  │
└───────┼─────────────┼─────────────┼─────────────┼───────┘
        │             │             │             │
        └─────────────┴──────┬──────┴─────────────┘
                             │
                    ┌────────▼────────┐
                    │   FastAPI 后端   │
                    └────────┬────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
┌───────▼───────┐   ┌────────▼───────┐   ┌──────▼──────┐
│  规则引擎      │   │  LLM 生成器     │   │ SQL 验证器  │
│ (schema.yaml)  │   │ (多提供者)      │   │ (sqlglot)   │
└───────────────┘   └────────────────┘   └─────────────┘
```

## API 接口

### 1. SQL 转换

```
POST /api/convert
```

**请求体：**
```json
{
  "text": "统计每个省份的订单金额",
  "dialect": "hive",
  "mode": "hybrid",
  "provider": "deepseek",
  "model": "deepseek-v4-flash",
  "temperature": 0.1,
  "use_schema": true
}
```

**响应：**
```json
{
  "sql": "SELECT province, SUM(amount) FROM orders GROUP BY province",
  "source": "llm",
  "confidence": 0.95,
  "error": null,
  "sql_valid": true
}
```

### 2. 获取数据字典

```
GET /api/schemas
```

### 3. 获取方言列表

```
GET /api/dialects
```

### 4. 获取 LLM 提供者列表

```
GET /api/providers
```

### 5. 验证 SQL

```
POST /api/validate-sql
```

**请求体：**
```json
{
  "sql": "SELECT * FROM table_name",
  "dialect": "hive"
}
```

### 6. 保存 API Key

```
POST /api/config/api-key
```

**请求体：**
```json
{
  "provider": "deepseek",
  "api_key": "sk-xxxxx"
}
```

## 维护指南

### 更新数据字典

如果 `warehouse/doris/dml` 或 `warehouse/doris/logical` 中的 SQL 文件有更新，可以重新解析：

```bash
# 解析建表语句
python scripts/parse_doris_sql.py

# 解析表关联关系
python scripts/parse_logical_sql.py

# 重新生成同义词
python scripts/generate_synonyms.py
```

### 添加新的 LLM 提供者

1. 在 `src/llm/providers/` 目录添加新的提供者实现
2. 在 `config/llm_config.yaml` 添加提供者配置
3. 在 `server.py` 添加对应的路由处理

## 常见问题

### Q: 规则引擎模式下报"未找到匹配的表"
A: 这是正常的。规则引擎依赖本地数据字典（schema.yaml），如果表名或字段在字典中不存在，会提示未找到。请确认查询内容是否在已知表结构范围内，或切换到混合模式/大模型模式。

### Q: LLM 模式报"API Key 未设置"
A: 需要在配置页面设置对应提供者的 API Key，或直接在 `config/llm_config.yaml` 文件中填写。

### Q: 生成的 SQL 语法不正确
A: 系统使用 sqlglot 进行语法验证，如果验证失败会显示错误信息。请检查生成的 SQL 是否符合目标方言的语法规范。

### Q: 前端页面加载慢或卡顿
A: 数据字典页面默认折叠所有表，请使用分页功能和搜索功能减少一次性加载的数据量。

## 技术栈

- **后端**：Python、FastAPI、sqlglot
- **前端**：Vue 3、Element Plus、Vite
- **LLM**：OpenAI、Anthropic、DashScope 等多提供者支持
- **数据**：YAML 格式的元数据管理

## 许可证

MIT License
