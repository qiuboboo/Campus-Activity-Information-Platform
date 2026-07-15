/**
 * Mock 内存数据存储
 */

export const DEMO_USER = {
  id: 1,
  username: 'admin',
  email: 'admin@example.com',
  role: 'admin',
  created_at: '2026-01-01T00:00:00',
}

export const REGULAR_USER = {
  id: 2,
  username: 'zhangsan',
  email: 'zhangsan@example.com',
  role: 'publisher',
  created_at: '2026-03-15T00:00:00',
}

export const VERIFICATION_CODES = {}
export const CAPTCHA_CODES = {}
export const REGISTERED_USERS = {}
export const SESSIONS = {}
export const UPLOADS = new Map()
let _nextUserId = 3
export function getNextUserId() {
  return _nextUserId++
}
let _nextActivityId = 10
export function getNextActivityId() { return _nextActivityId++ }
let _nextUploadId = 1
export function getNextUploadId() { return String(_nextUploadId++) }

export const USER_STATE = {
  favorites: { 1: [1, 3], 2: [2] },
  registrations: {},
  subscriptions: { 1: [{ id: 1, keyword: '人工智能', created_at: '2026-05-20T08:00:00' }], 2: [] },
  notifications: { 1: [{ id: 1, title: '新活动待审核', body: '有 1 条活动等待审核。', read: false, created_at: '2026-05-25T09:00:00' }], 2: [{ id: 2, title: '活动提醒', body: '校园十大歌手决赛将在本周举行。', read: false, created_at: '2026-05-24T09:00:00' }] },
}

export const DATA_SOURCES = [
  { id: 1, name: '中山大学新闻网', url: 'https://www.sysu.edu.cn', enabled: true, last_status: '2026-05-24 抓取成功' },
  { id: 2, name: '校园讲座公告', url: 'https://lecture.sysu.edu.cn', enabled: true, last_status: '2026-05-23 抓取成功' },
]

export const AUDIT_LOGS = [
  { id: 1, created_at: '2026-05-24T10:00:00', actor: 'admin', action: 'approve', target: '活动 #1', summary: '批准中山大学第12届学术科技节' },
]

export const ACTIVITIES = [
  // ---- 已发布（published） ----
  {
    id: 1,
    title: '中山大学第12届学术科技节',
    raw_text: '一年一度的学术科技节即将开幕，包含学术讲座、科技展览、创新竞赛等多个环节。欢迎全校师生参与。',
    summary: '涵盖学术讲座、科技展览、创新竞赛的综合性学术活动。',
    event_time: '2026-06-15T09:00:00',
    location: '广州校区南校园',
    organizer: '中山大学团委',
    status: 'published',
    activity_type: '讲座',
    created_at: '2026-05-20T10:00:00',
  },
  {
    id: 2,
    title: '校园十大歌手决赛之夜',
    raw_text: '经过层层选拔，十大歌手决赛即将震撼上演。现场设有抽奖环节，观众可参与互动投票。',
    summary: '年度校园音乐盛事，十大歌手终极对决。',
    event_time: '2026-06-20T19:00:00',
    location: '东校园体育馆',
    organizer: '学生会文艺部',
    status: 'published',
    activity_type: '晚会',
    created_at: '2026-05-21T14:00:00',
  },
  {
    id: 3,
    title: 'ACM程序设计校内选拔赛',
    raw_text: '面向全校本科生的算法编程竞赛，优秀选手将组队参加ACM-ICPC区域赛。比赛时长5小时，题目难度梯度分布。',
    summary: '算法编程竞赛，选拔校队成员参加ACM-ICPC。',
    event_time: '2026-06-10T13:00:00',
    location: '计算机学院实验中心',
    organizer: 'ACM集训队',
    status: 'published',
    activity_type: '竞赛',
    created_at: '2026-05-18T09:00:00',
  },
  {
    id: 4,
    title: '粤港澳大湾区青年论坛',
    raw_text: '邀请粤港澳三地青年学者、创业者分享前沿见解，探讨科技创新与区域发展。设圆桌讨论和自由交流环节。',
    summary: '粤港澳三地青年学者与创业者交流论坛。',
    event_time: '2026-07-01T08:30:00',
    location: '珠海校区国际学术中心',
    organizer: '港澳台事务办公室',
    status: 'published',
    activity_type: '论坛',
    created_at: '2026-05-22T16:00:00',
  },
  {
    id: 5,
    title: '中山大学春季艺术展',
    raw_text: '展出全校师生绘画、书法、摄影、雕塑作品200余件，设有现场创作体验区。展期两周，免费开放。',
    summary: '全校师生艺术作品联合展览，含现场创作体验。',
    event_time: '2026-06-01T09:00:00',
    location: '南校园图书馆展厅',
    organizer: '艺术学院',
    status: 'published',
    activity_type: '展览',
    created_at: '2026-05-15T11:00:00',
  },
  {
    id: 6,
    title: '腾讯2026校园招聘宣讲会',
    raw_text: '腾讯公司2026届校园招聘正式启动，现场接收简历并进行技术分享。涵盖开发、产品、设计、运营等岗位。',
    summary: '腾讯校招宣讲，现场收简历与技术分享。',
    event_time: '2026-06-25T14:30:00',
    location: '东校园行政楼报告厅',
    organizer: '就业指导中心',
    status: 'published',
    activity_type: '招聘',
    created_at: '2026-05-23T08:00:00',
  },
  {
    id: 7,
    title: '夏季校园马拉松',
    raw_text: '全程5公里，途经校园主要景观。设男子组、女子组和团体组。完赛可获得定制奖牌和纪念T恤。',
    summary: '校园5公里马拉松，完赛可获定制奖牌。',
    event_time: '2026-06-12T07:00:00',
    location: '东校园田径场',
    organizer: '体育部',
    status: 'published',
    activity_type: '体育',
    created_at: '2026-05-19T15:00:00',
  },
  {
    id: 8,
    title: '摄影技巧分享工作坊',
    raw_text: '特邀国家地理签约摄影师主讲，涵盖构图、光线、后期处理等实用内容。参与者请自带相机或手机。',
    summary: '摄影师分享构图、光线、后期处理技巧。',
    event_time: '2026-06-18T15:00:00',
    location: '传播与设计学院',
    organizer: '摄影协会',
    status: 'published',
    activity_type: '其他',
    created_at: '2026-05-24T10:00:00',
  },
  // ---- 草稿（draft） ----
  {
    id: 9,
    title: '秋季社团招新嘉年华',
    raw_text: '全校社团联合招新，设舞台表演、互动游戏、集章抽奖等活动。预计参与社团超过100个。',
    summary: '百团大战，社团招新与舞台表演。',
    event_time: '2026-09-10T09:00:00',
    location: '东校园中心广场',
    organizer: '学生社团联合会',
    status: 'draft',
    activity_type: '其他',
    created_by: 2,
    created_at: '2026-05-22T12:00:00',
  },
]

// 日程事件（按用户 id 索引）
export const CALENDAR_EVENTS = {
  1: [
    { time: '09:00', title: '审核待发布活动', type: 'info' },
    { time: '14:00', title: '服务器维护', type: 'warning' },
    { time: '16:30', title: '团队周会', type: 'info' },
  ],
  2: [
    { time: '08:30', title: 'ACM选拔赛筹备会', type: 'info' },
    { time: '10:00', title: '检查活动草稿', type: 'warning' },
    { time: '14:00', title: '摄影工作坊场地确认', type: 'info' },
    { time: '19:00', title: '十大歌手决赛彩排', type: 'warning' },
  ],
}

export function resetDb() {
  Object.keys(VERIFICATION_CODES).forEach((k) => delete VERIFICATION_CODES[k])
  Object.keys(CAPTCHA_CODES).forEach((k) => delete CAPTCHA_CODES[k])
  Object.keys(REGISTERED_USERS).forEach((k) => delete REGISTERED_USERS[k])
  Object.keys(SESSIONS).forEach((k) => delete SESSIONS[k])
  UPLOADS.clear()
  _nextUserId = 3
  _nextActivityId = 10
  _nextUploadId = 1
  ACTIVITIES.length = 0
}
