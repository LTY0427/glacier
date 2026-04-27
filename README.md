# 冰川数据查询与预测系统

基于Vue 3 + Flask的冰川数据分析系统，提供数据查询、趋势预测和转型分析功能。

## 技术栈

### 前端
- Vue 3
- Element Plus
- ECharts
- Leaflet
- Pinia
- Vue Router
- Vite

### 后端
- Flask
- SQLite
- scikit-learn
- ReportLab

## 项目结构

```
ruanzhu/
├── src/                    # Vue前端源码
│   ├── components/         # 组件
│   │   ├── Sidebar.vue    # 左侧导航栏
│   │   ├── SettingsBar.vue # 设置栏
│   │   └── ChartComponent.vue # 图表组件
│   ├── views/             # 页面视图
│   │   ├── MapView.vue    # 地图导航
│   │   ├── QueryView.vue  # 数据查询
│   │   ├── PredictView.vue # 趋势预测
│   │   └── ReportView.vue # 导出报告
│   ├── store/             # Pinia状态管理
│   ├── router/            # 路由配置
│   ├── utils/             # 工具函数
│   └── main.js            # 入口文件
├── app.py                 # Flask后端
├── prediction_model.py    # 预测模型
├── build_database.py     # 数据库构建
└── requirements.txt      # Python依赖

```

## 安装与运行

### 1. 安装Python依赖

```bash
pip install -r requirements.txt
```

### 2. 构建数据库

```bash
python build_database.py
```

### 3. 安装前端依赖

```bash
npm install
```

### 4. 开发模式运行

前端（Vite开发服务器，端口2450）：
```bash
npm run dev
```

后端（Flask，端口5000）：
```bash
python app.py
```

### 5. 生产环境构建

构建前端：
```bash
npm run build
```

运行后端（同时服务静态文件）：
```bash
python app.py
```

## API接口

### RESTful API设计

- `GET /api/glacier/{id}/info` - 获取冰川基本信息
- `GET /api/glacier/{id}/history?start_year=&end_year=` - 获取历史指标数据
- `POST /api/glacier/{id}/predict` - 预测未来指标值
- `GET /api/glacier/{id}/transform-index?years=` - 计算转型指数
- `GET /api/glacier/{id}/report` - 生成PDF报告
- `GET /api/glacier/map-data` - 获取所有冰川地图数据

## 功能模块

1. **地图导航** - 可视化显示所有冰川位置，支持点击选择
2. **数据查询** - 查询冰川历史数据，展示指标趋势图
3. **趋势预测** - 多模型预测对比，转型分析
4. **导出报告** - 生成PDF分析报告

## 部署

系统可部署在具备Node.js/Python环境的服务器上，使用Nginx或PM2管理进程。

