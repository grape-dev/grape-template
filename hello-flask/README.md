# Mood Tracker 心情追踪器

极简 Flask Web 应用：记录每日心情，查看心情统计趋势。

## 快速开始

```bash
pip install -r requirements.txt
python app.py
```

访问 http://localhost:5000

## 端点说明

| 路由 | 方法 | 功能 |
|---|---|---|
| `/` | GET | 心情追踪页面（emoji 选择 + 备注 + 列表 + 统计图） |
| `/api/moods` | GET | 获取所有心情记录 |
| `/api/moods` | POST | 记录心情（JSON: `{"score": 1-5, "note": "备注"}`） |
| `/api/stats` | GET | 心情统计（总数 / 平均分 / 分布） |
| `/health` | GET | 健康检查 `{"status":"ok"}` |

## 心情等级

| Emoji | 标签 | 分数 |
|---|---|---|
| 😀 | 开心 | 5 |
| 😊 | 愉悦 | 4 |
| 😐 | 平静 | 3 |
| 😟 | 低落 | 2 |
| 😢 | 难过 | 1 |

## Grape 流水线体验（3 步）

本项目使用 `hello-demo` 流水线（5 阶段）：

```
vod(需求分析) → issue(分类分配) → coding(编码实现) → qa(PR审查) → sre(云部署)
```

### 第 1 步：部署体验（自动触发）

模板创建后自动触发。流水线会部署应用到云服务器，完成后在 Issue 评论中查看部署地址。

### 第 2 步：新增导出功能（手动创建 Issue）

在 GitCode 仓库 → Issue → 新建：

- **标题**：`新增 /api/export 端点`
- **描述**：新增 /api/export 端点，返回心情 JSON 数据，支持日期过滤（`?start=2026-09-01&end=2026-09-09`），首页添加导出按钮。

提交后观察流水线自动分析 → 编码 → 审查 → 部署的全过程。

### 第 3 步：补充测试（手动创建 Issue）

在 GitCode 仓库 → Issue → 新建：

- **标题**：`为 /api/export 补充单元测试`
- **描述**：验证空数据返回空列表、有数据返回完整记录、日期过滤功能正确。

提交后体验测试驱动开发流程。

## 运行测试

```bash
python -m pytest test_app.py -v
```

## 部署说明

生产环境使用 gunicorn 启动：

```bash
pip install gunicorn
gunicorn -w 2 -b 0.0.0.0:5000 app:app
```

## 学习要点

- Flask 路由与 `render_template_string`
- RESTful API 设计（GET / POST）
- JSON 请求与响应处理
- 内存数据存储与统计计算
- `unittest` 单元测试
- 健康检查端点设计
