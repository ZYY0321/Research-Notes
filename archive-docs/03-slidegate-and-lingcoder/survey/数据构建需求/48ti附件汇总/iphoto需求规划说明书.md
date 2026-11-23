# i相册-情侣专属照片记录网站开发规划

### 1.1 用户与情侣关系管理
- **用户注册与登录系统**
  - 账号安全设置（密码修改、两步验证）
  - 用户名校验、密码加密
- **情侣绑定与关系管理**
  - 情侣邀请机制（生成6位数字的临时情侣码）
  - 关系验证与确认流程
  - 情侣关系状态管理（正常、解除关系等）
  - 纪念日设置（恋爱纪念日、生日等）

### 1.2 情侣空间定制
- **个性化空间设置**
  - 情侣空间主题选择（多种预设主题）
  - 自定义背景、封面、空间名称
  - 情侣专属域名/URL设置
  - 隐私权限设置（仅双方可见）

- **个人资料管理**
  - 个人信息编辑
  - 情侣合照设置
  - 个人标签与兴趣爱好

### 1.3 相册管理系统
- **多级相册分类**
  - 时间轴相册（按时间自动排序）
  - 主题相册（如旅行、节日、日常等）
  - 自定义相册创建与管理
  - 相册封面设置与排序
- **相册权限控制**
  - 整体相册权限设置
  - 单相册独立权限设置

### 1.4 照片上传与故事描述
- **照片上传功能**
  - 多图批量上传
  - 拖拽上传支持
  - 照片格式与大小限制
  - 上传进度显示与断点续传

- **照片信息与故事描述**
  - 照片基本信息（拍摄时间、地点、设备）
  - 文字故事描述（富文本编辑器）
  - 标签添加（人物、场景、情绪等）
  - 照片定位与地图标记
  - 天气与心情标记

### 1.5 多样化照片展示模块
1. **时间轴视图**
   - 按时间顺序排列照片
   - 支持年/月/日筛选
   - 时间节点标记重要事件

2. **地图足迹视图**
   - 在地图上标记照片拍摄地点
   - 支持缩放和平移
   - 点击地图标记查看对应照片

3. **3D旋转画廊**
   - 3D立体效果展示照片
   - 支持鼠标/手势旋转控制
   - 可设置自动播放效果

4. **故事书视图**
   - 模拟实体相册翻页效果
   - 支持背景音乐添加
   - 可制作成电子相册分享

5. **瀑布流视图**
   - 不规则网格排列照片
   - 无限滚动加载
   - 支持按标签筛选

6. **拼图墙视图**
   - 多张照片组合成自定义形状
   - 支持手动调整照片位置和大小
   - 可保存为拼图海报

### 1.6 趣味互动功能
- **照片互动**
  - 点赞功能
  - 评论系统（支持文字、表情）
- **回忆提醒**
  - 回忆纪念日提醒（往年今日照片）

### 1.7 管理端功能规划
- **用户管理模块**
  - 用户账号管理（查询、禁用/启用账号）
  - 情侣关系管理（查看关系状态、处理关系异常）
- **内容管理模块**
  - 相册管理（查看、隐藏相册）
  - 照片管理（查看、隐藏照片）
  - 评论管理（查看、删除评论）
- **系统配置模块**
  - 主题管理（新增、编辑、删除主题）
- **数据统计与分析**
  - 内容数据统计（照片上传量、相册创建数）
- **通知管理模块**
  - 纪念日提醒设置与管理

## 2. 技术架构设计

### 2.1 推荐技术栈

#### 前端技术栈
- **核心框架**: Vue.js 2.x + Vue Router + JavaScript
  - 选择理由: Vue2具有简单易学、轻量级、文档完善的特点，适合快速开发

- **状态管理**: Vuex
  - 选择理由: Vue生态系统的官方状态管理库，集中管理应用状态，适合复杂组件间通信

- **UI组件库**: Element UI
  - 选择理由: 基于Vue2的组件库，提供丰富的UI组件，适合快速开发企业级应用

- **HTTP客户端**: Axios
  - 选择理由: 支持Promise API，拦截请求和响应，处理异步请求

- **动画效果**: Vue Transition + Animate.css
  - 选择理由: Vue内置的过渡系统，配合Animate.css提供丰富的动画效果

- **构建工具**: Vue CLI 3+
  - 选择理由: Vue官方构建工具，提供项目脚手架、开发服务器、构建优化等功能

#### 后端技术栈
- **核心框架**: Spring Boot 2.x (基于Java 1.8)
  - 选择理由: Spring Boot提供自动配置、独立运行能力和丰富的starter，适合快速开发企业级应用

- **ORM框架**: MyBatis
  - 选择理由: 简化数据库操作

- **API设计**: RESTful API
  - 选择理由: 符合HTTP设计原则，易于理解和扩展，适合前后端分离架构

- **安全框架**: Spring Security + JWT
  - 选择理由: Spring生态系统的安全框架，配合JWT实现无状态认证，保护API接口安全

- **任务调度**: Spring Scheduler
  - 选择理由: 用于定时任务，如回忆提醒、数据统计等功能

#### 数据库选择
- **主数据库**: MySQL 5.7
  - 选择理由: 稳定可靠的关系型数据库，支持事务和复杂查询，适合存储结构化数据

- **缓存系统**: Redis
  - 选择理由: 高性能内存数据库，用于缓存热点数据、会话管理、排行榜等功能，减轻数据库压力

#### 存储方案
- **对象存储**: 阿里云OSS/AWS S3
  - 选择理由: 高可用、高扩展性的对象存储服务，适合存储大量照片文件，支持CDN加速

- **CDN加速**: 阿里云CDN/Cloudflare
  - 选择理由: 全球节点分发，加速静态资源访问，提升不同地区用户体验

### 2.2 系统架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                        客户端层 (Client Layer)                    │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                Vue.js 2.x 单页应用                        │   │
│  │  ┌──────────┐ ┌────────┐ ┌────────┐ ┌────────────────┐   │   │
│  │  │ Vue Router│ │ Vuex   │ │Element UI│ │ Axios         │   │   │
│  │  └──────────┘ └────────┘ └────────┘ └────────────────┘   │   │
│  └──────────────────────────────────────────────────────────┘   │
└───────────────────────────────┬─────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                        API网关层 (API Gateway)                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐   │
│  │  请求路由     │  │  认证授权     │  │   限流与负载均衡      │   │
│  └──────────────┘  └──────────────┘  └──────────────────────┘   │
└───────────────────────────────┬─────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                        应用服务层 (Application Layer)             │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                 Spring Boot 应用服务                      │   │
│  │  ┌──────────┐ ┌────────┐ ┌────────┐ ┌────────────────┐   │   │
│  │  │Controller │ │Service │ │  Model │ │MyBatis-Plus    │   │   │
│  │  └──────────┘ └────────┘ └────────┘ └────────────────┘   │   │
│  └──────────────────────────────────────────────────────────┘   │
└───────────────────────────────┬─────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                        数据持久层 (Data Layer)                    │
│  ┌──────────────────┐  ┌────────────────┐  ┌────────────────┐   │
│  │    MySQL 5.7     │  │     Redis      │  │   对象存储      │   │
│  │  (关系型数据)    │  │  (缓存数据)    │  │  (照片存储)     │   │
│  └──────────────────┘  └────────────────┘  └────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

## 3. 数据库设计

### 3.1 核心实体关系图

```
┌─────────────┐       ┌───────────────┐       ┌─────────────┐
│    User     │       │  Relationship │       │    User     │
├─────────────┤       ├───────────────┤       ├─────────────┤
│ id          │──┐    │ id            │    ┌──│ id          │
│ username    │  │    │ user1_id      │◄───┘  │ username    │
│             │  └────│ user2_id      │──────┘│             │
│             │       │ status        │       │             │
│ password    │       │ created_at    │       │ password    │
│ avatar      │       │ updated_at    │       │ avatar      │
│ created_at  │       │ anniversary   │       │ created_at  │
│ updated_at  │       │ breakup_at    │       │ updated_at  │
└─────────────┘       └───────────────┘       └─────────────┘
        │                        ▲
        │                        │
        ▼                        │
┌─────────────┐       ┌───────────────┐       ┌─────────────┐
│ UserProfile │       │   SpaceInfo   │       │   Theme     │
├─────────────┤       ├───────────────┤       ├─────────────┤
│ id          │       │ id            │       │ id          │
│ user_id     │       │ relationship_id◄──────┤ name        │
│ real_name   │       │ name          │       │ color_scheme│
│ birthday    │       │ theme_id      │──────►│ background  │
│ gender      │       │ background    │       │ font        │
│ hobbies     │       │ cover_image   │       │ style       │
│ intro       │       │ privacy_level │       │ preview_img │
└─────────────┘       │ domain        │       └─────────────┘
        ▲             │ created_at    │           
        │             │ updated_at    │               
        │             └───────────────┘                
        │                      ▲                       
        │                      │                       
        │             ┌───────────────┐                
        │             │    Album      │                
        │             ├───────────────┤                
        │             │ id            │                
        └─────────────┤ owner_id      │               
                      │ relationship_id                
                      │ cover_image   │                
                      │ description   │                
                      │ category      │                
                      │ privacy       │                
                      │ created_at    │                
                      │ updated_at    │                
                      └───────────────┘                
                              ▲                        
                              │                        
                              │                        
                      ┌───────────────┐                
                      │    Photo      │                
                      ├───────────────┤                
                      │ id            │                
                      │ album_id      │                
                      │ uploader_id   │                
                      │ title         │                
                      │ description   │                
                      │ url           │               
                      │ thumbnail_url │                
                      │ location      │               
                      │ weather       │              
                      │ mood          │                
                      │ taken_at      │              
                      │ created_at    │               
                      │ updated_at    │                
                      └───────────────┘              
                              ▲                       
                              │                      
                              │                       
               ┌──────────────┴───────┐                
               │                      │                
        ┌───────────────┐      ┌───────────────┐        
        │ PhotoComment  │      │ PhotoLike     │        
        ├───────────────┤      ├───────────────┤        
        │ id            │      │ id            │        
        │ photo_id      │      │ photo_id      │        
        │ user_id       │      │ user_id       │        
        │ content       │      │ created_at    │        
        │ created_at    │      └───────────────┘        
        │ updated_at    │                              
        └───────────────┘                               
                                                       
                                           
```

### 3.2 详细数据库表结构设计

#### 用户与情侣关系相关表

**1. users (用户表)**
```sql
CREATE TABLE users (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  username VARCHAR(50) NOT NULL UNIQUE COMMENT '用户名',
  password VARCHAR(100) NOT NULL COMMENT '密码哈希',
  avatar VARCHAR(255) COMMENT '头像URL',
  status TINYINT DEFAULT 1 COMMENT '状态：0-禁用，1-正常',
  last_login_at DATETIME COMMENT '最后登录时间',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户表';
```

**2. user_profiles (用户资料表)**
```sql
CREATE TABLE user_profiles (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  user_id BIGINT NOT NULL UNIQUE COMMENT '用户ID',
  real_name VARCHAR(50) COMMENT '真实姓名',
  birthday DATE COMMENT '生日',
  gender TINYINT COMMENT '性别：0-未知，1-男，2-女',
  hobbies VARCHAR(255) COMMENT '兴趣爱好，逗号分隔',
  intro TEXT COMMENT '个人简介',
  address VARCHAR(255) COMMENT '所在地',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
  INDEX idx_user_id (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户资料表';
```

**3. relationships (情侣关系表)**
```sql
CREATE TABLE relationships (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  user1_id BIGINT NOT NULL COMMENT '用户1ID',
  user2_id BIGINT NOT NULL COMMENT '用户2ID',
  status TINYINT NOT NULL DEFAULT 1 COMMENT '状态：0-待确认，1-正常，2-已解除',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '关系创建时间',
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  anniversary DATE COMMENT '恋爱纪念日',
  breakup_at DATETIME COMMENT '分手时间',
  request_message VARCHAR(255) COMMENT '关系请求消息',
  confirm_message VARCHAR(255) COMMENT '确认消息',
  FOREIGN KEY (user1_id) REFERENCES users(id) ON DELETE CASCADE,
  FOREIGN KEY (user2_id) REFERENCES users(id) ON DELETE CASCADE,
  UNIQUE KEY uk_user_pair (LEAST(user1_id, user2_id), GREATEST(user1_id, user2_id)),
  INDEX idx_user1_status (user1_id, status),
  INDEX idx_user2_status (user2_id, status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='情侣关系表';
```

#### 空间与主题相关表

**4. themes (主题表)**
```sql
CREATE TABLE themes (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  name VARCHAR(100) NOT NULL COMMENT '主题名称',
  description TEXT COMMENT '主题描述',
  color_scheme JSON COMMENT '配色方案',
  background VARCHAR(255) COMMENT '背景图片URL',
  font VARCHAR(50) COMMENT '字体',
  style VARCHAR(50) COMMENT '风格：简约、浪漫、复古等',
  preview_img VARCHAR(255) COMMENT '预览图URL',
  is_default TINYINT DEFAULT 0 COMMENT '是否默认主题：0-否，1-是',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX idx_is_default (is_default)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='主题表';
```

**5. space_info (情侣空间信息表)**
```sql
CREATE TABLE space_info (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  relationship_id BIGINT NOT NULL UNIQUE COMMENT '情侣关系ID',
  name VARCHAR(100) NOT NULL COMMENT '空间名称',
  theme_id BIGINT COMMENT '主题ID',
  background VARCHAR(255) COMMENT '自定义背景图片URL',
  cover_image VARCHAR(255) COMMENT '封面图片URL',
  domain VARCHAR(100) COMMENT '自定义域名',
  view_count INT DEFAULT 0 COMMENT '访问次数',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  FOREIGN KEY (relationship_id) REFERENCES relationships(id) ON DELETE CASCADE,
  FOREIGN KEY (theme_id) REFERENCES themes(id),
  UNIQUE KEY uk_domain (domain),
  INDEX idx_relationship_id (relationship_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='情侣空间信息表';
```

#### 相册与照片相关表

**6. albums (相册表)**
```sql
CREATE TABLE albums (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  name VARCHAR(100) NOT NULL COMMENT '相册名称',
  owner_id BIGINT NOT NULL COMMENT '创建者ID',
  relationship_id BIGINT NOT NULL COMMENT '所属情侣关系ID',
  cover_image VARCHAR(255) COMMENT '封面图片URL',
  description TEXT COMMENT '相册描述',
  category VARCHAR(50) COMMENT '分类：旅行、节日等',
  sort_order INT DEFAULT 0 COMMENT '排序序号',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  FOREIGN KEY (owner_id) REFERENCES users(id) ON DELETE CASCADE,
  FOREIGN KEY (relationship_id) REFERENCES relationships(id) ON DELETE CASCADE,
  INDEX idx_relationship_id (relationship_id),
  INDEX idx_owner_id (owner_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='相册表';
```

**7. photos (照片表)**
```sql
CREATE TABLE photos (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  album_id BIGINT NOT NULL COMMENT '所属相册ID',
  uploader_id BIGINT NOT NULL COMMENT '上传者ID',
  title VARCHAR(255) COMMENT '照片标题',
  description TEXT COMMENT '照片描述',
  url VARCHAR(255) NOT NULL COMMENT '原始照片URL',
  thumbnail_url VARCHAR(255) COMMENT '缩略图URL',
  large_url VARCHAR(255) COMMENT '大图URL',
  width INT COMMENT '宽度',
  height INT COMMENT '高度',
  size INT COMMENT '文件大小(字节)',
  format VARCHAR(20) COMMENT '文件格式',
  location VARCHAR(255) COMMENT '拍摄地点',
  weather VARCHAR(50) COMMENT '天气',
  mood VARCHAR(50) COMMENT '心情',
  taken_at DATETIME COMMENT '拍摄时间',
  sort_order INT DEFAULT 0 COMMENT '排序序号',
  view_count INT DEFAULT 0 COMMENT '查看次数',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  metadata JSON COMMENT '扩展元数据',
  FOREIGN KEY (album_id) REFERENCES albums(id) ON DELETE CASCADE,
  FOREIGN KEY (uploader_id) REFERENCES users(id) ON DELETE CASCADE,
  INDEX idx_album_id (album_id),
  INDEX idx_uploader_id (uploader_id),
  INDEX idx_taken_at (taken_at),
  INDEX idx_location (location)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='照片表';
```

**8. photo_tags (照片标签表)**

```sql
CREATE TABLE photo_tags (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  photo_id BIGINT NOT NULL COMMENT '照片ID',
  tag_name VARCHAR(50) NOT NULL COMMENT '标签名称',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (photo_id) REFERENCES photos(id) ON DELETE CASCADE,
  UNIQUE KEY uk_photo_tag (photo_id, tag_name),
  INDEX idx_tag_name (tag_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='照片标签表';
```

#### 互动相关表

**9. photo_likes (照片点赞表)**

```sql
CREATE TABLE photo_likes (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  photo_id BIGINT NOT NULL COMMENT '照片ID',
  user_id BIGINT NOT NULL COMMENT '点赞用户ID',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (photo_id) REFERENCES photos(id) ON DELETE CASCADE,
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
  UNIQUE KEY uk_photo_user (photo_id, user_id),
  INDEX idx_photo_id (photo_id),
  INDEX idx_user_id (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='照片点赞表';
```

**10. photo_comments (照片评论表)**

```sql
CREATE TABLE photo_comments (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  photo_id BIGINT NOT NULL COMMENT '照片ID',
  user_id BIGINT NOT NULL COMMENT '评论用户ID',
  content TEXT NOT NULL COMMENT '评论内容',
  parent_id BIGINT COMMENT '父评论ID，用于回复功能',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  FOREIGN KEY (photo_id) REFERENCES photos(id) ON DELETE CASCADE,
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
  FOREIGN KEY (parent_id) REFERENCES photo_comments(id) ON DELETE CASCADE,
  INDEX idx_photo_id (photo_id),
  INDEX idx_user_id (user_id),
  INDEX idx_parent_id (parent_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='照片评论表';
```

**11. memories (回忆提醒表)**

```sql
CREATE TABLE memories (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  relationship_id BIGINT NOT NULL COMMENT '情侣关系ID',
  title VARCHAR(255) NOT NULL COMMENT '回忆标题',
  description TEXT COMMENT '回忆描述',
  reminder_date DATE NOT NULL COMMENT '提醒日期',
  reminder_time TIME COMMENT '提醒时间',
  repeat_type VARCHAR(20) DEFAULT 'yearly' COMMENT '重复类型：yearly, monthly, daily, once',
  status TINYINT DEFAULT 1 COMMENT '状态：0-禁用，1-启用',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  FOREIGN KEY (relationship_id) REFERENCES relationships(id) ON DELETE CASCADE,
  INDEX idx_relationship_id (relationship_id),
  INDEX idx_reminder_date (reminder_date),
  INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='回忆提醒表';
```

## 4. UI/UX设计建议

### 4.1 设计风格定位

为"i相册"情侣照片记录网站，建议采用**温馨浪漫、简约精致**的设计风格，整体视觉效果应该传达出甜蜜、温暖和珍贵回忆的感觉。设计应注重情感化表达，同时保持界面简洁易用，让用户能够专注于照片内容和情感体验。

### 4.2 色彩方案

#### 主色调
- **主色**：柔和的粉色系 (#FF85A2)
  - 代表浪漫、甜蜜和爱情，适合情侣主题
  - 用于主要按钮、重点强调元素和品牌标识

- **辅助色**：淡紫色 (#A78BFA)
  - 与主色形成和谐对比，传达温馨梦幻感
  - 用于次要按钮、交互元素和装饰元素

#### 中性色
- **背景色**：浅米色 (#FFF9F5)
  - 温暖柔和的背景，减少视觉疲劳
  - 适合长时间浏览照片

- **文本色**：深灰色 (#333333)
  - 确保良好的可读性
  - 用于主要文本内容

- **次要文本**：中灰色 (#666666)
  - 用于辅助说明文字

- **边框和分割线**：浅灰色 (#EEEEEE)

#### 功能色
- **成功**：淡绿色 (#4ADE80)
- **警告**：淡黄色 (#FACC15)
- **错误**：淡红色 (#F87171)
- **信息**：淡蓝色 (#60A5FA)

### 4.3 页面布局设计

#### 整体布局结构
采用响应式设计，适配移动端和桌面端：

- **移动端**：单栏布局，重要功能放在底部导航栏
- **平板/桌面端**：侧边栏导航 + 主内容区的双栏布局

#### 关键页面布局

**1. 情侣空间主页**
- 顶部展示情侣封面图和空间名称
- 封面图下方显示情侣合照和基本信息
- 中部为动态时间轴，展示最新上传的照片
- 下方为相册入口，以卡片式布局展示
- 右侧边栏（桌面端）显示纪念日倒计时和重要提醒

**2. 相册列表页**
- 顶部为相册筛选和搜索功能
- 主体采用瀑布流或网格布局展示相册封面
- 每个相册卡片显示封面图、名称、照片数量和创建时间
- 支持按时间、名称、自定义排序
- 悬浮操作按钮用于创建新相册

**3. 照片详情页**
- 大型照片展示区，支持左右滑动切换
- 照片下方为故事描述和互动区域
- 右侧（桌面端）或底部（移动端）为照片信息和操作按钮
- 支持全屏查看模式

### 4.4 照片展示模块视觉设计

**1. 时间轴视图**
- 垂直中心线设计，照片沿中心线两侧排列
- 按时间顺序从新到旧排列
- 每个时间节点有月份标签和简约分隔线
- 重要日期有特殊标记和装饰元素
- 滚动时有视差效果，增强深度感

**2. 地图足迹视图**
- 简洁的矢量地图背景
- 照片以大头针或爱心标记在地图上
- 标记点根据照片数量有大小变化
- 支持缩放和平移操作
- 点击标记点弹出照片缩略图预览

**3. 3D旋转画廊**
- 模拟实体相册的3D翻页效果
- 支持鼠标拖拽旋转或自动播放
- 中央照片最大，向两侧逐渐缩小
- 旋转时有轻微的阴影和深度效果
- 可调整旋转速度和方向

**4. 故事书视图**
- 模拟真实相册的翻页效果，有页面卷曲动画
- 左右两页形成一个完整的跨页设计
- 支持添加文字说明和装饰元素
- 可自定义页面背景和边框样式
- 翻页时有纸张翻动音效（可关闭）

**5. 拼图墙视图**
- 多张照片以不规则方式排列组合成自定义形状
- 提供多种预设拼图模板：心形、圆形、方形、自由式等
- 支持手动调整照片位置和大小
- 照片大小根据重要性和尺寸自动调整
- 双击照片放大查看详情

## 5. 核心功能模块详细设计

### 5.1 情侣绑定与验证机制

#### 实现方案

**1. 绑定流程设计**

```
用户A注册/登录 → 进入"寻找情侣"页面 → 选择绑定方式 → 
生成绑定邀请 → 用户B接收邀请 → 用户B确认 → 
系统创建情侣关系 → 完成绑定，进入情侣空间
```

**2. 多种绑定方式**

- **二维码绑定**
  - 用户A生成个性化二维码
  - 用户B扫描二维码接收邀请
  - 二维码有效期设为10分钟，过期自动刷新
  
- **链接绑定**
  - 生成带有用户ID和时间戳的加密链接
  - 支持通过社交媒体、短信等渠道分享
  - 链接有效期设为24小时
  
- **账号搜索绑定**
  - 支持通过手机号、邮箱或用户名搜索
  - 搜索结果展示用户头像和昵称（隐藏部分信息保护隐私）
  - 发送邀请时需附加验证消息

- **情侣码绑定**
  - 生成6位数字的临时情侣码
  - 双方输入相同的情侣码完成绑定
  - 情侣码每分钟刷新一次

**3. 验证与安全机制**

- **双向确认机制**
  - 邀请发送后，需对方明确确认才能完成绑定
  - 确认页面显示双方信息，防止误绑
  
- **防骚扰保护**
  - 被拒绝后，短时间内无法再次向同一用户发送邀请
  - 用户可设置"不接收陌生人邀请"
  
- **关系状态管理**
  - 待确认状态：邀请已发送，等待对方确认
  - 已绑定状态：双方已确认，正常情侣关系
  - 解除中状态：一方申请解除，等待对方确认
  - 已解除状态：情侣关系已解除

### 5.2 照片上传与故事描述系统

#### 实现方案

**1. 照片上传流程**

- **多渠道上传入口**
  - 相册页面的"上传照片"按钮
  - 首页快捷上传按钮
  - 手机端支持直接拍摄上传
  - 支持从第三方相册导入（如微信相册、手机系统相册）

- **批量上传支持**
  - 一次最多支持50张照片批量上传
  - 拖放区域支持文件多选和拖放排序
  - 上传队列管理，支持暂停、继续和取消

- **断点续传机制**
  - 基于HTML5 File API实现分片上传
  - 每个文件分成2MB的块进行上传
  - 上传中断后可从断点继续，无需重新上传整个文件
  - 上传进度实时保存到本地存储

**2. 照片处理与优化**

- **自动处理流程**
  ```
  原图上传 → 服务器接收 → 生成缩略图 → 生成中等尺寸图 → 
  生成原图备份 → 提取EXIF信息 → 存入数据库 → 通知客户端上传完成
  ```

- **图片处理规格**
  - 缩略图：200×200px，用于列表展示
  - 中等图：800×800px，用于预览和普通查看
  - 原图：保留原始尺寸，用于高清查看和下载
  
- **智能优化**
  - 自动旋转：根据EXIF信息调整方向
  - 压缩优化：保持视觉质量的同时减小文件体积
  - 格式转换：自动将HEIC等特殊格式转换为JPEG/PNG

**3. 故事描述系统**

- **富文本编辑器**
  - 支持基本格式化：粗体、斜体、下划线
  - 支持标题层级和项目符号
  - 支持表情符号和特殊字符
  - 简单的排版样式选择

- **多维度故事元素**
  - **时间信息**
    - 自动提取照片EXIF中的拍摄时间
    - 支持手动调整时间和时区
    - 可设置为"今日"、"昨日"等相对时间显示
  
  - **地点标记**
    - 自动获取拍摄地点（如果照片包含GPS信息）
    - 手动搜索选择地点
    - 在地图上精确定位
    - 支持添加地点描述
  
  - **情绪与天气**
    - 情绪选择器：开心、浪漫、平静、惊喜等
    - 天气选择器：晴天、雨天、雪天等
    - 每个选项配有对应的小图标
  
  - **人物标记**
    - 支持标记照片中的人物（情侣双方或其他人）
    - 点击标记可查看相关人物的所有照片
    - 支持添加人物关系和备注

- **标签系统**
  - 预设常用标签分类：场景（旅行、约会、日常）、节日（生日、纪念日）、活动（看电影、吃饭）等
  - 智能标签推荐：基于照片内容和描述自动推荐相关标签
  - 自定义标签支持，自动记录用户常用标签

### 5.2 五种照片浏览/展示模块

#### 1. 时间轴视图

**效果描述**：
垂直滚动的时间轴，照片按时间顺序排列，重要日期有特殊标记，支持按年/月快速筛选。

**实现思路**：
- **数据结构**：
  ```javascript
  {
    "years": [
      {
        "year": 2023,
        "months": [
          {
            "month": 10,
            "days": [
              {
                "day": 15,
                "photos": [/* 照片数组 */]
              }
            ]
          }
        ]
      }
    ]
  }
  ```

- **前端实现**：
  - 使用Vue组件化构建时间轴项
  - 采用虚拟滚动(如vue-virtual-scroller)优化大量照片的渲染性能
  - 时间轴中心线使用SVG绘制，随滚动动态变化
  - 月份分隔使用渐变色块和简约文字标记
  
- **交互效果**：
  - 滚动时照片有淡入效果
  - 点击年份/月份可快速跳转到对应时间点
  - 重要日期（如纪念日）的照片卡片有特殊边框和标记
  - 支持横向滑动查看同一天的多张照片

### 2. 地图足迹视图

**效果描述**：
交互式地图上标记照片拍摄地点，不同地点用不同颜色和大小的标记表示，点击标记可查看该地点的所有照片。

**实现思路**：
- **地图选择**：
  - 使用高德地图API作为基础地图
  - 支持标准地图和卫星地图两种模式切换
  
- **标记设计**：
  - 使用自定义爱心形状标记
  - 标记颜色根据照片数量渐变
  - 标记大小根据该地点照片数量动态调整
  - 有新照片的地点标记有脉冲动画效果
  
- **交互功能**：
  - 地图支持缩放、平移操作
  - 点击标记弹出照片缩略图轮播
  - 支持按时间范围筛选地图上的照片
  - 可切换"全部足迹"和"共同足迹"视图
  
- **技术实现**：
  - 后端提供按地理范围查询照片的API
  - 使用Redis缓存热门地点的照片数据
  - 前端使用地图集群(clustering)优化大量标记的显示性能
  - 照片地理位置信息使用GCJ-02坐标系（高德地图标准）

### 3. 3D旋转画廊

**效果描述**：
照片以3D圆柱方式排列，用户可通过鼠标拖拽或触摸滑动进行旋转浏览，中央位置的照片最大最清晰，向两侧逐渐缩小。

**实现思路**：
- **3D布局**：
  - 使用Three.js实现3D场景
  - 照片排列在虚拟圆柱面上
  - 视角固定在圆柱中心，旋转圆柱实现浏览
  
- **交互控制**：
  - 鼠标拖拽/触摸滑动控制旋转方向和速度
  - 滚轮/双指缩放控制视角远近
  - 点击照片放大查看详情
  - 支持自动旋转模式，可调整旋转速度
  
- **视觉效果**：
  - 中央照片高亮显示，尺寸最大
  - 两侧照片有透视变形效果，增强空间感
  - 照片之间有适当间距，避免重叠
  - 背景使用渐变深色，突出照片内容
  
- **技术实现**：
  - 使用WebGL渲染3D场景
  - 根据设备性能自动调整渲染质量
  - 照片加载采用LOD策略，远处照片使用低分辨率缩略图
  - 支持VR模式，配合VR设备获得沉浸式体验

### 4. 故事书视图

**效果描述**：
模拟实体相册的翻页效果，照片以跨页方式排版，支持添加文字描述和装饰元素，营造翻阅实体相册的温馨体验。

**实现思路**：
- **翻页效果**：
  - 使用CSS 3D变换实现页面卷曲效果
  - 翻页时有阴影和厚度变化，增强真实感
  - 支持左右滑动或点击页码翻页
  
- **排版布局**：
  - 支持多种预设排版模板：单张大图、两张对页、多张小图组合等
  - 文字描述区域可自由调整位置和大小
  - 支持添加日期、地点等元数据
  - 可添加装饰元素：贴纸、边框、线条等
  
- **阅读体验**：
  - 支持自动翻页播放，可设置翻页间隔
  - 翻页时有纸张翻动音效（可关闭）
  - 支持全屏模式，隐藏界面元素
  - 可添加背景音乐，增强阅读氛围
  
- **技术实现**：
  - 使用Turn.js或自行实现翻页效果
  - 页面内容预加载，提升翻页流畅度
  - 支持离线缓存，可在无网络环境下浏览已加载的故事书

### 5. 拼图墙视图

**效果描述**：
多张照片以不规则方式排列组合成自定义形状的拼图墙，用户可手动调整照片位置和大小，也可使用自动排版功能生成多种风格的拼图效果。

**实现思路**：

- **拼图布局**：
  - 提供多种预设拼图模板：心形、圆形、方形、自由式等
  - 支持自定义拼图尺寸和比例
  - 照片大小根据重要性和尺寸自动调整
  
- **交互功能**：
  - 拖拽调整照片位置
  - 双击照片放大查看详情
  - 拖拽边缘调整照片大小
  - 支持旋转照片角度
  
- **自动排版算法**：
  - 基于照片尺寸和横纵比例智能布局
  - 重要照片（如合照、有故事描述的照片）优先分配较大空间
  - 避免同一场景或同一时间的照片相邻排列
  - 自动平衡照片色彩分布，避免色彩过于集中
  
- **技术实现**：
  - 使用CSS Grid和Vue拖拽组件实现拼图功能
  - 拖拽功能使用vuedraggable实现
  - 拼图状态实时保存，支持撤销/重做操作
  - 支持导出高清拼图图片，用于分享或打印
