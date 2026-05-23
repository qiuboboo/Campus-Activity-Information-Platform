# 主页设计：三栏式布局

## 概述

- 布局：深绿色顶栏（网站标题 + 搜索框），主体三栏：左侧导航、中间主内容、右侧辅助栏
- 页面高度：`100vh`，整体不滚动，中间和右侧独立滚动
- 文件：`frontend/src/views/home/HomeView.vue`（~250 行，逻辑在 composable + 4 个子组件）

## 文件结构

```
src/
  composables/useHomePage.ts       ← 所有状态/逻辑（数据获取、轮播、日历计算、导航）
  views/home/HomeView.vue          ← 主页面，仅组装组件 + 热门轮播 + 活动分类列表
  components/
    NavHeader.vue                  ← 顶部导航栏（品牌 + 搜索框 + 登录/退出按钮）
    SearchBar.vue                  ← 搜索框组件
    NavSidebar.vue                 ← 左侧导航 + 分类快捷入口
    HomeCalendarCard.vue           ← 右侧日历 + 日程卡片
    FooterBar.vue                  ← 页脚（品牌 + 版权）
```

## 布局

### 顶部导航栏（`NavHeader.vue`）
- `height: 60px`，绿色背景 `#0d5e3c`，sticky
- 左侧："逸仙活动云"
- 中间：`SearchBar` 组件
- 右侧：未登录显示"登录"按钮，已登录显示用户名 + "退出登录"按钮
- 所有按钮为绿色渐变 `.nav-cta` 样式
- 未开放入口（搜索提交、我的活动、创建活动）弹出"内容未实现！"

### 左侧导航（`NavSidebar.vue`）
- 栏目：全部活动、热门推荐、按类别、我的活动、创建活动
- 点击"我的活动"/"创建活动" → 未登录跳登录页，已登录提示"内容未实现！"
- 其余通过 `scrollIntoView` 滚动
- 分隔线下：分类快捷入口（前 6 种类型）
- ≤768px 隐藏

### 中间主内容（`HomeView.vue` 模板）

**上方：热门活动轮播**
- 自动 4 秒轮播，带指示点
- 显示：类型标签、标题、摘要、主办方、时间、地点
 - 数据：`listActivities({ status: 'published', per_page: 6 })`
- 点击卡片提示"内容未实现！"

**下方：分类活动列表**
- `el-radio-group` 标签："最近" + 8 种活动类型
- 按 `created_at` 降序排列
 - 选中类型时从 `recentActivities` 中按 `activity_type` 过滤
- 无数据时显示 `el-empty`

### 右侧辅助栏（`HomeCalendarCard.vue`）
- 上：日历（当月视图，今日/选中日高亮，上/下月切换）
- 下：日程列表（通过 `GET /api/calendar/events` 获取，按用户返回不同日程）
- ≤1024px 隐藏

### 页脚（`FooterBar.vue`）
- `height: 60px`，黑色背景
- 品牌名 + 英文副标题
- 版权信息
 - 类别切换：点击标签后局部刷新下方活动列表（`fetchCategoryActivities`）
- 日历：选择日期联动展示该日日程
- 响应式：
  - ≤1024px：右侧辅助栏隐藏
  - ≤768px：左侧导航隐藏，三栏变单列，搜索框隐藏

---

## 可访问性与性能
- 无障碍：所有交互控件添加合适 `aria-` 标签，卡片与按钮可键盘导航
- 性能：骨架屏，纵向滚动仅发生在需要滚动的区域内

---

## API 与数据交互
| 用途 | 接口 |
|------|------|
| 搜索 | GET `/api/activities?query=...&category=...&date=...&page=...` |
| 热门活动 | GET `/api/activities?status=published&per_page=6` |
| 最近/分类活动 | GET `/api/activities?per_page=6`（前端过滤+排序） |
| 日历/日程 | GET `/api/calendar?user_id=...&month=YYYY-MM` |
| 详情/报名 | GET `/api/activities/:id`、POST `/api/activities/:id/register` |

---

## Mock 数据说明（`frontend/mock-server.js`）
 - 每条 ACTIVITIES 记录需包含 `activity_type` 字段，值为后端支持的 8 种类型之一
- 示例：
  ```js
  { id: 1, title: '校园科技文化节开幕式', activity_type: '其他', ... }
  { id: 2, title: 'AI 创新应用讲座',      activity_type: '讲座', ... }
  { id: 3, title: '校园志愿服务文化论坛',  activity_type: '论坛', ... }
  { id: 4, title: '春季篮球联赛决赛',       activity_type: '体育', ... }
  { id: 5, title: '校园歌手大赛海选',       activity_type: '晚会', ... }
  { id: 6, title: '考研经验分享会',         activity_type: '讲座', ... }
  ```

---

## CSS 布局要点
- `.home-page`：`height: 100vh; overflow: hidden;` 固定视口
- `.home-body`：`padding: 24px 32px 0 0;`（左 0，右 32px，侧栏贴左）
- `.home-main`：`flex: 1; display: flex; flex-direction: column; overflow: hidden;`
- `.hot-section`：`flex-shrink: 0;` 固定在上方
- `.category-scroll`：`flex: 1; display: flex; flex-direction: column; overflow: hidden;`
- `.cat-scroll-body`：`flex: 1; overflow-y: auto;` 独立滚动
- `.nav-brand`：`margin-left: calc(200px + 28px - 32px);` 标题对齐主内容
- `.side-right`：`overflow-y: auto;` 独立滚动

---

## 实现约定说明
- 页面以单文件组件实现 `HomeView.vue`，包含模板/脚本/样式
- 仅在复用或复杂性上升时才抽出子组件到 `frontend/src/components`

---

## TODO 列表（可执行项）
- [x] 1. 创建 `HomeView.vue` 单文件页面（三栏布局、100vh 固定高度）
- [x] 2. 实现顶部搜索栏（搜索框、登录/注册入口）
- [x] 3. 实现左侧导航栏（栏目切换 + 分类快捷入口）
- [x] 4. 实现热门活动横向卡片流（固定在上方）
- [x] 5. 实现分类活动列表（标签固定 + 独立滚动，按 activity_type 过滤排序）
- [x] 6. 实现日历与日程面板（右侧辅助栏）
- [x] 7. 骨架屏加载状态
- [x] 8. 添加 `activity_type` 到 mock 数据
- [x] 9. 侧栏贴左 + 标题对齐
- [ ] 10. 编写单元测试（组件）与集成测试（搜索/分类/日历联动）
- [ ] 11. 图片懒加载与手势支持（移动端滑动热点卡片）
- [ ] 12. 无障碍检查与对比度优化

---

文件结束。

概述
- 布局：顶部绿色顶栏（网站标题 + 搜索框），页面主体采用三栏式：左侧竖向导航栏、中间主内容区、右侧辅助信息栏。
- 目的：兼顾“活动发现”与“个人规划”，用户进入即可检索活动，同时可快速浏览热门活动并查看个人日程。

布局细节
- 顶部顶栏（全宽，绿色）
  - 左侧：网站标题与 logo
  - 居中偏上：明显的搜索框（占据视觉中心，支持关键词/分类/日期搜索）
  - 右侧（可选）：用户头像/登录状态、快速操作按钮

- 左侧竖向导航（固定宽度）
  - 用于栏目切换：全部、热门、按类别、我的活动、创建活动、筛选器等
  - 视觉上突出（背景或边框），在窄屏下收起为抽屉或底部导航

- 中间主内容（流式宽度，分上下两块）
  - 上方：热门活动横向卡片流（可左右滑动）
    - 每张卡片显示：海报图、标题、时间、地点、报名状态、简短标签
    - 支持左右滚动（桌面为左右箭头或滚动条，移动端为手势滑动）
  - 下方：按类别分区的活动列表
    - 类别来源：从所有活动中提取 `activity_type` 字段去重生成（如志愿类、竞赛类、讲座类、招募类等），而非从知识图谱节点获取
    - 用户点击类别标签后，中间区域局部刷新显示该类型的活动列表
    - 支持按时间/热度排序、筛选（地点、标签、主办方）

- 右侧辅助栏（固定窄栏）
  - 上：日历（当月视图）——点击某日可以高亮当天活动
  - 下：该日用户日程（私人视图）——结合用户已报名/收藏/日程的事项
  - 可选：快捷添加活动按钮、提醒设置、今日推荐

交互与行为
- 搜索优先：页面顶部搜索框支持智能提示、类别补全、历史记录、回车提交并展示结果
- 热门活动卡片：鼠标悬停显示更多信息（摘要、参与人数、收藏按钮）；点击进入活动详情
- 类别列表：点击类别后中间区域局部刷新（AJAX），保持滚动位置或回到顶部由设计决定
- 日历互动：选择日期时同步筛选中间显示该日活动；在日历中可直接加入/预约
- 响应式行为：
  - 小屏（≤768px）：顶栏保留搜索为收缩形式（可展开），左侧导航折为抽屉，三栏变为单列（主内容优先，辅助栏下移至页尾或折叠）
  - 中屏/大屏：三栏并列展示，热门横向卡片显示更多卡片

可访问性与性能
- 无障碍：所有交互控件添加合适 `aria-` 标签，卡片与按钮可键盘导航，色彩对比满足 WCAG AA
- 性能：图片使用懒加载，热门卡片使用虚拟化或按需渲染，活动列表分页或无限滚动（带占位骨架）

组件建议（页面内可直接实现或按需抽出子组件）
- `HomePage.vue`（页面单文件组件，包含模板/脚本/样式）
  - 说明：遵循项目约定，页面以单个 `.vue` 文件为主；仅在复用或复杂时拆分子组件到 `frontend/src/components`。

API 与数据交互
- 搜索：GET `/api/activities?query=...&category=...&date=...&page=...`
- 热门：GET `/api/activities?sort=hot&limit=...`
- 类别列表：从前端已有活动数据中提取 `activity_type` 去重获得（如志愿类、竞赛类、讲座类等），无需额外 API 请求
- 日历/日程：GET `/api/calendar?user_id=...&month=YYYY-MM`
 - 事件详情与报名：GET `/api/activities/:id`、POST `/api/activities/:id/register`

实现要点（工程与 UX）
- 首屏优化：将顶部与热门卡片作为首屏关键渲染块，延迟次要模块加载
- 搜索体验：提供联想建议与快速过滤，并支持 query 参数跳转（方便分享结果页）
- 状态保持：在左侧切换类别或翻页时保持用户的搜索/筛选状态（query params 或 store 存储）
- 日历联动：日历选择联动过滤中间内容；用户添加日程后即时更新右侧日程区域

TODO 列表（可执行项）
- [x] 1. 创建 `HomePage.vue` 单文件页面（实现三栏布局与顶栏）
- [x] 2. 实现 `TopBar`（含搜索，支持建议与回车提交）
- [x] 3. 实现 `SideNav`（栏目与筛选项）并与路由或 store 联动
- [x] 4. 实现 `HorizontalCards`（热门活动横向卡片流）
- [x] 5. 实现 `CategoryList`（按类别的活动列表，支持标签筛选）
- [x] 6. 实现 `CalendarWidget` 与 `MySchedule` 并完成日历联动逻辑
- [x] 7. 骨架屏（性能优化基础）
- [ ] 8. 编写单元测试（组件）与集成测试（搜索/分类/日历联动）
- [ ] 9. 图片懒加载与手势支持（移动端滑动热点卡片）
- [ ] 10. 无障碍检查与对比度优化

实现约定说明
- 页面首选以单文件组件实现：`HomePage.vue` 包含页面逻辑、样式与模板；仅在需要复用或复杂性上升时才抽出组件到 `frontend/src/components`。

---

文件结束。