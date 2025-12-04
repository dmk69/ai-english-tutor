# 🎓 智能英语学习对话系统规划文档

## 📋 项目概述

创建一个智能英语学习对话系统，能够根据用户指定的CEFR英语等级进行对话训练，并自动记录和分析用户的语言错误，提供个性化的学习建议。

## 🎯 系统目标

- **个性化学习** - 根据用户英语等级定制对话内容
- **错误分析** - 实时检测和记录语法、词汇等错误
- **数据驱动** - 基于用户数据分析学习进展
- **进度追踪** - 提供详细的学习报告和改进建议

## 🏗️ 系统架构

### 核心模块设计

1. **英语等级控制器 (EnglishLevelController)**
   - 管理CEFR A1-C2等级配置
   - 控制词汇复杂度和句型结构
   - 动态调整AI回复难度

2. **错误检测引擎 (ErrorDetectionEngine)**
   - 语法错误检测
   - 词汇使用分析
   - 拼写和标点检查
   - 表达自然度评估

3. **数据库管理器 (DatabaseManager)**
   - SQLite数据库操作
   - 用户数据存储
   - 错误记录管理
   - 分析结果缓存

4. **统计分析器 (AnalyticsEngine)**
   - 错误趋势分析
   - 学习进度计算
   - 个性化建议生成
   - 报告数据汇总

5. **对话管理器 (ConversationManager)**
   - 对话上下文维护
   - 流式响应处理
   - 用户交互控制

## 📚 CEFR英语等级体系

### 等级定义

| 等级 | 描述 | 词汇量 | 句型复杂度 |
|------|------|--------|------------|
| **A1** | Beginner | 500-800 | 简单句、基本疑问句 |
| **A2** | Elementary | 800-1500 | 复合句、时态变化 |
| **B1** | Intermediate | 1500-3000 | 从句、条件句 |
| **B2** | Upper-Intermediate | 3000-5000 | 被动语态、复杂时态 |
| **C1** | Advanced | 5000-8000 | 倒装句、虚拟语气 |
| **C2** | Proficient | 8000+ | 各类复杂语法结构 |

### 等级控制策略

- **词汇过滤** - 根据等级限制使用的词汇
- **句型模板** - 提供等级对应的句型库
- **语法复杂度** - 控制语法结构的复杂程度
- **话题选择** - 推荐适合等级的对话话题

## 💾 数据库设计

### 表结构设计

#### Users 表 - 用户信息
```sql
CREATE TABLE users (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    username VARCHAR(50) UNIQUE NOT NULL,
    preferred_level VARCHAR(2) DEFAULT 'B1',
    native_language VARCHAR(10),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### Conversations 表 - 对话会话
```sql
CREATE TABLE conversations (
    conversation_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER REFERENCES users(user_id),
    topic VARCHAR(100),
    english_level VARCHAR(2) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    total_messages INTEGER DEFAULT 0,
    duration_minutes INTEGER,
    completion_rate REAL
);
```

#### Messages 表 - 消息记录
```sql
CREATE TABLE messages (
    message_id INTEGER PRIMARY KEY AUTOINCREMENT,
    conversation_id INTEGER REFERENCES conversations(conversation_id),
    role VARCHAR(10) NOT NULL, -- 'user' or 'assistant'
    content TEXT NOT NULL,
    word_count INTEGER,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    response_time_ms INTEGER
);
```

#### Errors 表 - 错误记录
```sql
CREATE TABLE errors (
    error_id INTEGER PRIMARY KEY AUTOINCREMENT,
    message_id INTEGER REFERENCES messages(message_id),
    error_type VARCHAR(20) NOT NULL, -- grammar/vocabulary/spelling/expression/punctuation
    severity VARCHAR(10) DEFAULT 'minor', -- minor/major/critical
    original_text TEXT NOT NULL,
    correction TEXT,
    explanation TEXT,
    start_position INTEGER,
    end_position INTEGER,
    confidence_score REAL DEFAULT 0.0,
    detected_by VARCHAR(20) -- 'ai' or 'rule_based'
);
```

#### Error_Analytics 表 - 错误分析统计
```sql
CREATE TABLE error_analytics (
    analytics_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER REFERENCES users(user_id),
    date DATE NOT NULL,
    total_errors INTEGER DEFAULT 0,
    grammar_errors INTEGER DEFAULT 0,
    vocabulary_errors INTEGER DEFAULT 0,
    spelling_errors INTEGER DEFAULT 0,
    expression_errors INTEGER DEFAULT 0,
    punctuation_errors INTEGER DEFAULT 0,
    unique_error_types INTEGER,
    improvement_score REAL DEFAULT 0.0,
    most_common_error VARCHAR(50)
);
```

#### Vocabulary_Tracking 表 - 词汇追踪
```sql
CREATE TABLE vocabulary_tracking (
    tracking_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER REFERENCES users(user_id),
    word VARCHAR(50) NOT NULL,
    word_level VARCHAR(2),
    usage_count INTEGER DEFAULT 1,
    first_used TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_used TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    mastery_level INTEGER DEFAULT 0 -- 0-5 scale
);
```

## 🔧 技术实现方案

### 1. AI驱动的错误检测架构

#### 核心设计理念
- **AI优先** - 所有错误检测由AI模型完成
- **标准化输出** - AI返回结构化JSON格式的错误分析
- **轻量化本地处理** - 仅需解析JSON和存储数据

#### AI错误检测流程
1. **用户输入** → 发送给DeepSeek
2. **AI分析** → 同时进行对话和错误检测
3. **结构化输出** → 返回JSON格式的错误报告
4. **本地处理** → 解析JSON并存储到数据库

### 2. AI Prompt 工程策略

#### 等级适配提示模板
```python
LEVEL_PROMPTS = {
    'A1': "You are talking to an English beginner. Use simple words (CEFR A1), short sentences, and basic grammar.",
    'A2': "You are talking to an elementary English learner. Use common vocabulary (CEFR A2) and simple compound sentences.",
    'B1': "You are talking to an intermediate English learner. Use moderate vocabulary (CEFR B1) and some complex sentences.",
    'B2': "You are talking to an upper-intermediate learner. Use rich vocabulary (CEFR B2) and varied sentence structures.",
    'C1': "You are talking to an advanced English learner. Use sophisticated vocabulary (CEFR C1) and complex grammar.",
    'C2': "You are talking to a proficient English speaker. Use native-level vocabulary and natural expressions."
}
```

#### AI错误检测JSON格式设计
```python
# 统一的AI输出格式
AI_RESPONSE_FORMAT = {
    "conversation_response": "AI的自然对话回复",
    "error_analysis": {
        "has_errors": True/False,
        "error_count": 3,
        "errors": [
            {
                "error_type": "grammar/vocabulary/spelling/expression/punctuation",
                "severity": "minor/major/critical",
                "original_text": "错误的原文",
                "correction": "纠正后的文本",
                "explanation": "错误解释和学习要点",
                "start_position": 10,
                "end_position": 20,
                "confidence": 0.95
            }
        ],
        "vocabulary_analysis": {
            "new_words": ["advanced", "technique"],
            "word_count": 45,
            "cefr_level_estimate": "B1"
        },
        "overall_score": 85  # 0-100分
    }
}
```

#### 完整的AI提示模板
```python
COMPREHENSIVE_PROMPT = f"""
You are an English tutor for a {level} learner. Your task:

1. **Natural Conversation**: Respond naturally to the user's message, using {level} level English
2. **Error Analysis**: Analyze the user's message for errors and provide structured feedback

**Error Detection Categories:**
- Grammar: tenses, articles, prepositions, subject-verb agreement
- Vocabulary: word choice, collocations, register appropriateness
- Spelling: misspellings, capitalization
- Expression: unnatural phrasing, direct translation issues
- Punctuation: missing/incorrect punctuation

**Response Format Requirements:**
Return JSON with exactly this structure:
{{
    "conversation_response": "your natural English reply",
    "error_analysis": {{
        "has_errors": true/false,
        "error_count": number,
        "errors": [
            {{
                "error_type": "grammar/vocabulary/spelling/expression/punctuation",
                "severity": "minor/major/critical",
                "original_text": "exact user text",
                "correction": "corrected version",
                "explanation": "brief learning explanation",
                "start_position": start_char_index,
                "end_position": end_char_index,
                "confidence": 0.0-1.0
            }}
        ],
        "vocabulary_analysis": {{
            "new_words": ["word1", "word2"],
            "word_count": total_words,
            "cefr_level_estimate": "A1/A2/B1/B2/C1/C2"
        }},
        "overall_score": 0-100
    }}
}}

**Important:** Always respond with valid JSON. Focus on helpful, encouraging feedback.
"""

User message: "{user_message}"
"""
```

### 3. 简化的本地处理逻辑

#### JSON解析和数据存储
```python
import json
import sqlite3
from typing import Dict, List

def process_ai_response(ai_response: str) -> Dict:
    """解析AI返回的JSON响应"""
    try:
        response_data = json.loads(ai_response)
        return {
            'conversation': response_data.get('conversation_response', ''),
            'errors': response_data.get('error_analysis', {}).get('errors', []),
            'vocabulary': response_data.get('error_analysis', {}).get('vocabulary_analysis', {}),
            'score': response_data.get('error_analysis', {}).get('overall_score', 0)
        }
    except json.JSONDecodeError:
        return {'conversation': ai_response, 'errors': [], 'vocabulary': {}, 'score': 0}

def store_error_data(db_manager, message_id: int, errors: List[Dict]):
    """存储AI检测到的错误"""
    for error in errors:
        db_manager.add_error(message_id, {
            'error_type': error.get('error_type'),
            'severity': error.get('severity', 'minor'),
            'original_text': error.get('original_text'),
            'correction': error.get('correction'),
            'explanation': error.get('explanation'),
            'confidence_score': error.get('confidence', 0.0)
        })
```

#### 学习分析算法
```python
def analyze_learning_progress(user_id: int, db_manager) -> Dict:
    """基于AI数据的学习进度分析"""
    # 从数据库获取历史数据
    # 计算错误趋势
    # 分析词汇扩展
    # 生成个性化建议
    pass
```

## 📊 用户功能设计

### 命令行界面功能

```bash
# 基础对话
python english_tutor.py --level B1

# 指定话题
python english_tutor.py --level B2 --topic "technology"

# 查看学习报告
python english_tutor.py --report

# 导出数据
python english_tutor.py --export csv --days 30

# 词汇练习
python english_tutor.py --practice vocabulary --level B1

# 语法练习
python english_tutor.py --practice grammar --focus "tenses"
```

### 实时交互功能

1. **对话模式**
   - 流式英语对话
   - 实时错误提示（可选）
   - 上下文记忆

2. **学习模式**
   - 错误回顾练习
   - 词汇强化训练
   - 语法专项练习

3. **分析模式**
   - 学习报告生成
   - 进度可视化
   - 个性化建议

## 🎨 特色功能

### 1. 智能纠错系统
- **非侵入式** - 错误标记不影响对话流畅性
- **上下文感知** - 基于对话内容提供纠错建议
- **多选项纠错** - 提供多个可能的纠正方案
- **学习导向** - 每个纠错都包含学习要点

### 2. 个性化学习引擎
- **错误模式识别** - 识别用户的系统性错误
- **适应性调整** - 根据表现动态调整难度
- **专项训练** - 针对薄弱环节提供练习
- **学习路径规划** - 制定个性化提升计划

### 3. 游戏化学习元素
- **学习积分** - 正确使用获得积分
- **成就系统** - 解锁各种学习成就
- **连续打卡** - 激励持续学习
- **排行榜** - 与其他学习者比较

## 📅 实施计划

### Phase 1: 基础框架 (Week 1)
- [x] 项目规划文档
- [ ] 基础数据库结构
- [ ] 扩展现有流式对话程序
- [ ] 添加英语等级参数支持
- [ ] 基础错误检测集成

### Phase 2: 核心功能 (Week 2)
- [ ] 完善数据库操作模块
- [ ] 实现错误记录系统
- [ ] 开发统计分析功能
- [ ] 创建基础用户界面

### Phase 3: 高级分析 (Week 3)
- [ ] 完善错误检测算法
- [ ] 实现学习报告生成
- [ ] 添加个性化建议系统
- [ ] 优化AI Prompt策略

### Phase 4: 用户体验 (Week 4)
- [ ] 改进命令行界面
- [ ] 添加数据导出功能
- [ ] 实现游戏化元素
- [ ] 性能优化和测试

## 🔧 技术依赖

### 简化的Python库依赖
- `openai` - AI对话接口
- `sqlite3` - 数据库操作（内置）
- `json` - JSON数据处理（内置）
- `argparse` - 命令行参数（内置）
- `datetime` - 时间处理（内置）
- `os` - 系统操作（内置）
- `typing` - 类型提示（内置）

### 可选增强库
- `rich` - 美化终端输出（可选）
- `pandas` - 数据导出分析（可选）

### 外部服务
- **DeepSeek API** - AI对话和错误检测服务
- **无其他依赖** - 所有语言分析由AI完成

### 架构优势
- **轻量化** - 核心功能仅需3个依赖包
- **高性能** - 本地处理最小化，AI处理最优化
- **可扩展** - JSON格式标准化，易于添加新功能
- **维护简单** - 无复杂的本地语言处理逻辑

## 📈 成功指标

### 用户体验指标
- 对话流畅性评分 > 4.5/5
- 错误检测准确率 > 85%
- 学习效率提升 > 30%

### 技术性能指标
- 响应时间 < 2秒
- 错误分析准确率 > 90%
- 系统稳定性 > 99%

---

*文档版本: v1.0*
*最后更新: 2025-12-04*