# Snake Game 贪吃蛇

经典贪吃蛇游戏，Flask + Canvas 实现，浏览器直接运行。

## 快速开始

```bash
pip install -r requirements.txt
python app.py
```

访问 http://localhost:5000

## 玩法

- 方向键 / WASD 控制蛇的移动方向
- 空格键暂停/继续
- 吃到红色食物得 10 分，蛇身变长
- 每 50 分速度加快一级
- 撞墙或撞到自己游戏结束

## 端点

| 路由 | 方法 | 功能 |
|---|---|---|
| `/` | GET | 游戏页面 |
| `/health` | GET | 健康检查 |

## 技术栈

- Flask（Web 服务器）
- Canvas + JavaScript（游戏渲染与逻辑）
- 纯前端游戏循环，无需后端状态

## 学习要点

- Flask 路由与 Response
- Canvas 2D 绘图（fillRect / arc）
- 游戏循环（setInterval tick）
- 碰撞检测（边界 + 自身）
- 键盘事件处理
