from datetime import datetime, timedelta

from flask import current_app
from sqlalchemy.exc import IntegrityError

from ..extensions import db
from ..models import (
    CrawlLog,
    DataSource,
    DictEntry,
    Notification,
    Poster,
    Subscription,
    User,
    UserCalendarEvent,
)
from .audit_service import create_audit_log
from .knowledge_service import rebuild_poster_knowledge
from .poster_service import generate_poster_html


def ensure_default_admin() -> None:
    username = current_app.config["DEFAULT_ADMIN_USERNAME"]
    password = current_app.config["DEFAULT_ADMIN_PASSWORD"]

    existing_user = User.query.filter_by(username=username).first()
    if existing_user is not None:
        return

    admin = User(username=username, role="admin", email="admin@example.edu")
    admin.set_password(password)
    db.session.add(admin)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()


def _ensure_user(username: str, password: str, role: str, email: str) -> User:
    user = User.query.filter_by(username=username).first()
    if user is None:
      user = User(username=username, role=role, email=email)
      db.session.add(user)
    user.role = role
    user.email = email
    user.set_password(password)
    db.session.flush()
    return user


def _upsert_poster(created_by: int, payload: dict) -> Poster:
    poster = Poster.query.filter_by(source_url=payload["source_url"]).first()
    if poster is None:
        poster = Poster(created_by=created_by, source_url=payload["source_url"])
        db.session.add(poster)

    for key, value in payload.items():
        setattr(poster, key, value)

    poster.created_by = created_by
    poster.content_html = generate_poster_html(
        title=poster.title,
        summary=poster.summary,
        event_time=poster.event_time,
        location=poster.location,
        organizer=poster.organizer,
        activity_type=poster.activity_type,
    )
    db.session.flush()
    return poster


def _ensure_data_source() -> DataSource:
    source = DataSource.query.filter_by(name="中山大学官网").first()
    if source is None:
        source = DataSource(name="中山大学官网", base_url="https://www.sysu.edu.cn/")
        db.session.add(source)

    source.base_url = "https://www.sysu.edu.cn/"
    source.enabled = True
    source.crawl_mode = "basic"
    source.source_level = "official"
    source.allowed_domains = "www.sysu.edu.cn"
    source.list_selector = None
    source.content_selector = None
    source.owner = "SYSU"
    source.notes = "官方首页演示数据源；实际活动抓取建议配置更精确的栏目地址和 CSS 选择器。"
    source.request_interval = 1
    db.session.flush()

    if not CrawlLog.query.filter_by(data_source_id=source.id).first():
        now = datetime.utcnow()
        log = CrawlLog(
            data_source_id=source.id,
            status="completed",
            message="演示日志：已抓取官网首页并生成草稿。",
            started_at=now - timedelta(minutes=3),
            finished_at=now - timedelta(minutes=2),
            pages_found=1,
            pages_succeeded=1,
            pages_failed=0,
            duplicates_skipped=0,
            drafts_created=1,
            average_quality_score=75,
        )
        db.session.add(log)
    return source


def _ensure_dict_entries() -> None:
    entries = [
        ("place", "大学生活动中心大礼堂", "大活,大活礼堂", "大型讲座、晚会和开幕式常用场地"),
        ("place", "图书馆报告厅", "图书馆,报告厅", "报告会与学术沙龙常用场地"),
        ("org", "共青团中山大学委员会", "校团委,团委", "校园文化与志愿服务活动组织方"),
        ("org", "计算机学院", "计院,计算机学院", "技术讲座、竞赛与创新活动组织方"),
        ("topic", "人工智能", "AI,大模型,机器学习", "技术与创新主题"),
        ("topic", "志愿服务", "志愿者,公益", "公益实践与校园服务主题"),
    ]
    for category, standard_name, aliases, description in entries:
        entry = DictEntry.query.filter_by(category=category, standard_name=standard_name).first()
        if entry is None:
            entry = DictEntry(category=category, standard_name=standard_name)
            db.session.add(entry)
        entry.aliases = aliases
        entry.description = description


def _ensure_unique(model, defaults: dict, **filters):
    item = model.query.filter_by(**filters).first()
    if item is None:
        item = model(**filters, **defaults)
        db.session.add(item)
    else:
        for key, value in defaults.items():
            setattr(item, key, value)
    db.session.flush()
    return item


def seed_demo_posters() -> None:
    ensure_default_admin()

    admin = _ensure_user(
        current_app.config["DEFAULT_ADMIN_USERNAME"],
        current_app.config["DEFAULT_ADMIN_PASSWORD"],
        "admin",
        "admin@example.edu",
    )
    test = _ensure_user("test", "test123456", "publisher", "test@example.edu")

    now = datetime.utcnow()
    d = lambda offset=0, hour=0: now + timedelta(days=offset, hours=hour)
    # 故意让少许活动共享同一天以产生日历热力图深浅差异
    CLUSTER_A = 6   # day+6: 3 个活动
    CLUSTER_B = 14  # day+14: 4 个活动

    posters = [
        # ── 讲座 (3 published) ──
        _upsert_poster(admin.id, {
            "title": "人工智能创新应用讲座",
            "raw_text": "计算机学院邀请企业工程师分享大模型应用开发经验，包含案例拆解、问答和学习路径建议。本次讲座面向全校本科生和研究生，无需报名直接入场。主讲人为某头部科技公司的 AI 研究员，将结合校园场景讲解大模型在学术写作、数据分析、代码生成等方面的实际应用。",
            "summary": "从大模型产品到校园创新实践的技术讲座，含案例拆解和动手环节。",
            "event_time": d(7, 4),
            "location": "图书馆报告厅",
            "organizer": "计算机学院",
            "status": "published", "source_type": "manual",
            "source_url": "https://demo.sysu/activity/ai-lecture",
            "activity_type": "讲座",
            "tags": "AI,大模型,创新",
            "quality_score": 88,
        }),
        _upsert_poster(admin.id, {
            "title": "从校园到职场：软件工程职业发展讲座",
            "raw_text": "特邀三位来自腾讯、字节跳动、华为的校友返校分享，内容覆盖技术面试准备、应届生成长路径、大厂 vs 创业公司选择等热门话题。现场设有 Q&A 环节，欢迎携带简历参加最后的自由交流环节。",
            "summary": "三位互联网大厂校友分享软件工程职业发展路径与面试经验。",
            "event_time": d(CLUSTER_A, 7),
            "location": "行政楼 B 座报告厅",
            "organizer": "计算机学院",
            "status": "published", "source_type": "manual",
            "source_url": "https://demo.sysu/activity/career-talk",
            "activity_type": "讲座",
            "tags": "职业发展,校友,面试",
            "quality_score": 90,
        }),
        _upsert_poster(admin.id, {
            "title": "量子计算前沿学术报告",
            "raw_text": "邀请清华大学交叉信息研究院教授主讲，介绍量子计算基础原理、近期突破及在密码学和优化问题中的应用前景。报告后安排 30 分钟讨论环节，欢迎物理、数学、计算机等相关专业师生参加。",
            "summary": "清华大学教授主讲量子计算原理、最新进展与应用前景。",
            "event_time": d(21, 5),
            "location": "物理学院学术报告厅",
            "organizer": "物理学院",
            "status": "published", "source_type": "manual",
            "source_url": "https://demo.sysu/activity/quantum-lecture",
            "activity_type": "讲座",
            "tags": "量子计算,学术报告,前沿",
            "quality_score": 93,
        }),

        # ── 晚会 (3 published) ──
        _upsert_poster(admin.id, {
            "title": "2026 迎新文艺晚会",
            "raw_text": "一年一度的迎新文艺晚会将在梁銶琚堂盛大上演。节目涵盖民乐合奏、街舞、话剧、合唱等多种形式，由校艺术团和各院系联合演出。晚会设有抽奖环节，奖品包括平板电脑、蓝牙耳机等。欢迎全校师生到场观看，凭校园卡入场。",
            "summary": "校艺术团与各院系联合演出，民乐、街舞、话剧等精彩节目轮番上演。",
            "event_time": d(30, 7),
            "location": "梁銶琚堂",
            "organizer": "共青团中山大学委员会",
            "status": "published", "source_type": "manual",
            "source_url": "https://demo.sysu/activity/welcome-gala",
            "activity_type": "晚会",
            "tags": "迎新,文艺,演出",
            "quality_score": 91,
        }),
        _upsert_poster(admin.id, {
            "title": "校园十大歌手总决赛",
            "raw_text": "经过初赛、复赛的激烈角逐，十二位校园歌手晋级总决赛。决赛现场由专业评审和观众投票共同决定最终排名。现场设互动环节，观众可通过小程序为喜爱选手投票。往届冠军将作为表演嘉宾助阵。",
            "summary": "十二强选手巅峰对决，专业评审+现场投票，往届冠军助阵演出。",
            "event_time": d(25, 6.5),
            "location": "梁銶琚堂",
            "organizer": "校学生会文艺部",
            "status": "published", "source_type": "manual",
            "source_url": "https://demo.sysu/activity/singer-finals",
            "activity_type": "晚会",
            "tags": "歌手大赛,文艺,决赛",
            "quality_score": 87,
        }),
        _upsert_poster(admin.id, {
            "title": "中秋游园赏月晚会",
            "raw_text": "中秋节当晚在草坪广场举行，设灯笼 DIY、猜灯谜、月饼品尝、汉服体验等多个游园摊位。主舞台穿插民谣弹唱和古典舞表演。活动现场提供免费茶水和月饼，欢迎师生携家属参加。",
            "summary": "中秋草坪游园，灯笼DIY、灯谜、汉服体验、民谣弹唱，免费茶点。",
            "event_time": d(10, 7.5),
            "location": "南校园草坪广场",
            "organizer": "校学生会",
            "status": "published", "source_type": "manual",
            "source_url": "https://demo.sysu/activity/mid-autumn",
            "activity_type": "晚会",
            "tags": "中秋,游园,晚会",
            "quality_score": 86,
        }),

        # ── 竞赛 (3 published) ──
        _upsert_poster(admin.id, {
            "title": "2026 年大学生数学建模竞赛校内选拔赛",
            "raw_text": "全国大学生数学建模竞赛校内选拔赛正式启动。参赛队伍每队 3 人，在 72 小时内完成选题、建模、求解和论文撰写。比赛提供机房和指导老师值班答疑。优胜队伍将代表学校参加国赛，并获校级奖励证书和奖金。",
            "summary": "3 人组队、72 小时建模挑战，优胜队代表学校参加全国赛。",
            "event_time": d(3, 8),
            "location": "数学学院机房",
            "organizer": "数学学院",
            "status": "published", "source_type": "manual",
            "source_url": "https://demo.sysu/activity/math-modeling",
            "activity_type": "竞赛",
            "tags": "数学建模,竞赛,国赛选拔",
            "quality_score": 89,
        }),
        _upsert_poster(admin.id, {
            "title": "中山大学程序设计竞赛校赛",
            "raw_text": "面向全校本科生和研究生，采用 ACM-ICPC 赛制，个人参赛。题目涵盖数据结构、算法设计、动态规划等方向。比赛时长 4 小时，平台为在线评测系统。前十名选手将颁发证书及奖品，并优先推荐参加省赛和区域赛。",
            "summary": "ACM 赛制个人赛，4 小时算法挑战，前十名推荐省赛。",
            "event_time": d(CLUSTER_A, 2),
            "location": "计算机学院实验中心",
            "organizer": "计算机学院",
            "status": "published", "source_type": "manual",
            "source_url": "https://demo.sysu/activity/acm-contest",
            "activity_type": "竞赛",
            "tags": "ACM,算法,编程竞赛",
            "quality_score": 92,
        }),
        _upsert_poster(admin.id, {
            "title": "大学生创新创业大赛路演答辩",
            "raw_text": "各参赛团队提交商业计划书后，进入路演答辩环节。每队有 8 分钟展示时间和 5 分钟评委问答。评委由校内教授和校外投资人组成。获奖项目将获得学校创业孵化基地入驻资格和种子资金支持。",
            "summary": "创业计划书路演答辩，校内外评委评审，优胜项目获孵化基地入驻资格。",
            "event_time": d(CLUSTER_A, 3),
            "location": "创新创业中心路演厅",
            "organizer": "创新创业学院",
            "status": "published", "source_type": "manual",
            "source_url": "https://demo.sysu/activity/innovation-contest",
            "activity_type": "竞赛",
            "tags": "创业,路演,创新大赛",
            "quality_score": 88,
        }),

        # ── 论坛 (3 published) ──
        _upsert_poster(admin.id, {
            "title": "校园志愿服务文化论坛",
            "raw_text": "论坛围绕志愿服务项目设计、社区协作和校园公益传播展开交流。邀请广东省志愿者联合会代表、校内公益社团负责人和优秀志愿者进行主题分享与圆桌讨论。",
            "summary": "志愿服务主题论坛，含主题分享、圆桌讨论和优秀项目展示。",
            "event_time": d(9, 3),
            "location": "图书馆报告厅",
            "organizer": "共青团中山大学委员会",
            "status": "published", "source_type": "manual",
            "source_url": "https://demo.sysu/activity/volunteer-forum",
            "activity_type": "论坛",
            "tags": "志愿服务,公益,论坛",
            "quality_score": 84,
        }),
        _upsert_poster(admin.id, {
            "title": "粤港澳大湾区青年学者交叉学科论坛",
            "raw_text": "汇聚粤港澳三地高校青年学者，围绕人工智能、生物医药、新能源材料等交叉学科方向进行学术报告和合作洽谈。论坛设主题报告、海报展示和一对一交流环节，旨在促进跨校跨学科合作。",
            "summary": "粤港澳三地青年学者跨学科交流，主题报告+海报展示+合作洽谈。",
            "event_time": d(CLUSTER_B, 1),
            "location": "图书馆报告厅",
            "organizer": "研究生院",
            "status": "published", "source_type": "manual",
            "source_url": "https://demo.sysu/activity/gba-forum",
            "activity_type": "论坛",
            "tags": "粤港澳,交叉学科,青年学者",
            "quality_score": 94,
        }),
        _upsert_poster(admin.id, {
            "title": "校园可持续发展与学生行动论坛",
            "raw_text": "由环境学院和绿色校园办公室联合主办，讨论碳中和校园建设、垃圾分类推广、绿色出行倡导等议题。设有学生提案环节，优秀提案将提交学校相关部门参考实施。",
            "summary": "聚焦碳中和校园、垃圾分类和绿色出行，设学生提案环节。",
            "event_time": d(15, 4),
            "location": "环境学院会议室",
            "organizer": "环境学院",
            "status": "published", "source_type": "manual",
            "source_url": "https://demo.sysu/activity/green-forum",
            "activity_type": "论坛",
            "tags": "可持续发展,碳中和,绿色校园",
            "quality_score": 85,
        }),

        # ── 展览 (3 published) ──
        _upsert_poster(admin.id, {
            "title": "2026 校园科技文化节开幕式暨创新成果展",
            "raw_text": "校园科技文化节将在大学生活动中心大礼堂举行开幕式，同期在大堂举办学生创新成果展，展出近一年来各院系学生的科创作品、论文海报和发明专利。展览持续一周，面向校内外开放，团体参观可预约讲解服务。",
            "summary": "科技文化节开幕+学生创新成果展，展示科创作品、论文海报和专利。",
            "event_time": d(5, 2),
            "location": "大学生活动中心大礼堂",
            "organizer": "共青团中山大学委员会",
            "status": "published", "source_type": "manual",
            "source_url": "https://demo.sysu/activity/tech-culture-opening",
            "activity_type": "展览",
            "tags": "科技,文化节,创新成果展",
            "cover_image_url": "https://www.sysu.edu.cn/sites/default/files/logo_0.png",
            "quality_score": 92,
        }),
        _upsert_poster(admin.id, {
            "title": "岭南画派学生美术作品展",
            "raw_text": "展出艺术学院学生创作的国画、油画、水彩和综合材料作品 60 余幅，以岭南画派的传承与创新为主线。展期两周，期间安排两次艺术家导览和一次创作分享会。优秀作品将选送参加广东省大学生艺术展演。",
            "summary": "艺术学院学生 60+ 幅作品，岭南画派传承创新，含艺术家导览。",
            "event_time": d(2, 1),
            "location": "图书馆一楼展览厅",
            "organizer": "艺术学院",
            "status": "published", "source_type": "manual",
            "source_url": "https://demo.sysu/activity/art-exhibition",
            "activity_type": "展览",
            "tags": "美术,岭南画派,艺术学院",
            "quality_score": 90,
        }),
        _upsert_poster(admin.id, {
            "title": "「光影中大」校园摄影展",
            "raw_text": "由学生摄影社主办，展出 100 幅以中大校园建筑、自然风光和人文瞬间为主题的摄影作品。展览设最佳人气奖由观众投票选出。开幕式当天有手机摄影技巧分享讲座，欢迎摄影爱好者参加。",
            "summary": "100 幅校园主题摄影作品，设观众投票最佳人气奖，开幕式有摄影讲座。",
            "event_time": d(12, 1),
            "location": "图书馆一楼展览厅",
            "organizer": "学生摄影社",
            "status": "published", "source_type": "manual",
            "source_url": "https://demo.sysu/activity/photo-exhibition",
            "activity_type": "展览",
            "tags": "摄影,展览,校园",
            "quality_score": 83,
        }),

        # ── 招聘 (3 published) ──
        _upsert_poster(admin.id, {
            "title": "2026 年春季校园招聘双选会",
            "raw_text": "邀请 80 余家用人单位进校招聘，涵盖互联网、金融、制造、教育、医疗等多个行业。现场设简历投递、现场面试和企业宣讲区域。参会企业包括华为、腾讯、阿里巴巴、中国银行、南方电网、字节跳动等知名企业。建议提前准备多份纸质简历，穿着正装。",
            "summary": "80+ 企业进校招聘，互联网/金融/制造/教育全覆盖，现场投递简历面试。",
            "event_time": d(CLUSTER_B, 1),
            "location": "体育馆主馆",
            "organizer": "就业指导中心",
            "status": "published", "source_type": "manual",
            "source_url": "https://demo.sysu/activity/job-fair",
            "activity_type": "招聘",
            "tags": "招聘,双选会,春招",
            "quality_score": 95,
        }),
        _upsert_poster(admin.id, {
            "title": "互联网大厂校招经验分享暨内推专场",
            "raw_text": "由计算机学院和就业指导中心联合举办。邀请已获得字节跳动、阿里巴巴、腾讯、美团等 offer 的应届毕业生分享笔试面试经验。现场提供各公司内推码，并在活动后安排一对一简历修改服务（限前 50 名报名者）。",
            "summary": "拿到大厂 offer 的应届生分享经验，现场提供内推码和简历修改服务。",
            "event_time": d(8, 6.5),
            "location": "计算机学院学术报告厅",
            "organizer": "就业指导中心",
            "status": "published", "source_type": "manual",
            "source_url": "https://demo.sysu/activity/intern-recruit",
            "activity_type": "招聘",
            "tags": "校招,互联网,内推",
            "quality_score": 87,
        }),
        _upsert_poster(admin.id, {
            "title": "金融行业实习招聘宣讲周",
            "raw_text": "连续五天，每天两个金融企业专场。第一天银行专场（工商银行、建设银行、招商银行），第二天证券专场（中信证券、国泰君安），第三天保险专场（平安集团、泰康保险），第四天基金/信托专场，第五天综合金融专场。各企业将进行现场初步面试，请携带简历。",
            "summary": "五天十场金融企业宣讲+面试，覆盖银行/证券/保险/基金全赛道。",
            "event_time": d(16, 2),
            "location": "管理学院多功能厅",
            "organizer": "就业指导中心",
            "status": "published", "source_type": "manual",
            "source_url": "https://demo.sysu/activity/finance-recruit",
            "activity_type": "招聘",
            "tags": "金融,实习,宣讲会",
            "quality_score": 89,
        }),

        # ── 体育 (3 published) ──
        _upsert_poster(admin.id, {
            "title": "2026 年校运会田径比赛",
            "raw_text": "年度校运会包含短跑、长跑、跳高、跳远、铅球、接力等传统田径项目，分男子组和女子组。各院系以院为单位组队参赛，设团体总分奖和精神文明奖。开幕式有各院系方阵入场仪式和健美操表演。",
            "summary": "年度校运会田径比赛，各院系组队参赛，含方阵入场和健美操表演。",
            "event_time": d(CLUSTER_B, 1),
            "location": "东校园田径场",
            "organizer": "体育部",
            "status": "published", "source_type": "manual",
            "source_url": "https://demo.sysu/activity/sports-meet",
            "activity_type": "体育",
            "tags": "校运会,田径,体育",
            "quality_score": 91,
        }),
        _upsert_poster(admin.id, {
            "title": "院系篮球联赛决赛",
            "raw_text": "经过小组赛和淘汰赛一个月的激烈角逐，计算机学院与医学院会师决赛。比赛采用 FIBA 规则，四节制，设中场三分球大赛环节欢迎现场观众参与。赛后举行颁奖仪式。",
            "summary": "计算机学院 vs 医学院决赛，中场三分球大赛，四节制 FIBA 规则。",
            "event_time": d(6, 4.5),
            "location": "南校园综合体育馆",
            "organizer": "体育部",
            "status": "published", "source_type": "manual",
            "source_url": "https://demo.sysu/activity/basketball-final",
            "activity_type": "体育",
            "tags": "篮球,决赛,体育",
            "quality_score": 82,
        }),
        _upsert_poster(admin.id, {
            "title": "校园马拉松暨彩色跑活动",
            "raw_text": "围绕校园主干道设 5 公里赛道，沿途设 4 个彩色粉末喷洒站。不计名次，以趣味参与为主。报名即获纪念 T 恤和号码布，完赛获纪念奖牌。活动收益将捐赠给乡村教育公益项目。现场有 DJ 音乐和热身教练带队拉伸。",
            "summary": "5 公里校园彩色跑，4 个彩粉站，趣味参与不计名次，收益捐公益。",
            "event_time": d(11, 1.5),
            "location": "南校园主校道",
            "organizer": "体育部",
            "status": "published", "source_type": "manual",
            "source_url": "https://demo.sysu/activity/color-run",
            "activity_type": "体育",
            "tags": "马拉松,彩色跑,公益",
            "quality_score": 86,
        }),

        # ── 其他 (3 published) ──
        _upsert_poster(admin.id, {
            "title": "国际文化节暨留学生国家展",
            "raw_text": "来自 30 多个国家的留学生设展位展示本国特色文化、美食和传统服饰。现场有各国歌舞表演、语言角（可体验基础韩语/日语/法语等）和世界美食集市。活动免费开放，部分美食需购买代金券。",
            "summary": "30+ 国家留学生设展位，歌舞表演、语言角、世界美食集市。",
            "event_time": d(19, 2.5),
            "location": "梁銶琚堂前广场",
            "organizer": "国际交流与合作处",
            "status": "published", "source_type": "manual",
            "source_url": "https://demo.sysu/activity/international-festival",
            "activity_type": "其他",
            "tags": "国际文化,留学生,美食",
            "quality_score": 88,
        }),
        _upsert_poster(admin.id, {
            "title": "新生心理适应工作坊",
            "raw_text": "由心理咨询中心主办，面向大一新生开设。通过团体活动、角色扮演和分享讨论等方式，帮助新生适应大学生活、缓解学业压力、建立社交网络。每期限 30 人，需提前通过心理健康服务平台报名。",
            "summary": "心理咨询中心主办，团体活动+角色扮演，帮助新生适应大学生活。",
            "event_time": d(4, 3),
            "location": "心理咨询中心团体活动室",
            "organizer": "心理咨询中心",
            "status": "published", "source_type": "manual",
            "source_url": "https://demo.sysu/activity/workshop-new-student",
            "activity_type": "其他",
            "tags": "心理健康,新生适应,工作坊",
            "quality_score": 85,
        }),
        _upsert_poster(admin.id, {
            "title": "图书馆信息素养系列培训",
            "raw_text": "本学期开设四场专题培训：(1) 学术数据库检索技巧（知网/Web of Science/Scopus），(2) EndNote 文献管理入门，(3) 学术论文写作规范与查重避坑，(4) 数据可视化工具入门（Tableau/Python）。每场培训 90 分钟，含实操环节，请携带笔记本电脑。",
            "summary": "四场专题培训：数据库检索、EndNote、论文写作、数据可视化实操。",
            "event_time": d(1, 3),
            "location": "图书馆多媒体培训室",
            "organizer": "图书馆",
            "status": "published", "source_type": "manual",
            "source_url": "https://demo.sysu/activity/library-training",
            "activity_type": "其他",
            "tags": "图书馆,信息素养,培训",
            "quality_score": 87,
        }),

        # ── 待审核/驳回 (保留以演示工作流) ──
        _upsert_poster(test.id, {
            "title": "测试用户发布的摄影工作坊",
            "raw_text": "摄影工作坊正在等待管理员审核，内容包含校园取景、构图练习和作品互评。",
            "summary": "用于演示发布者提交审核与管理员审核流程。",
            "event_time": d(12, 5),
            "location": "逸夫艺术楼",
            "organizer": "学生摄影社",
            "status": "pending_review", "source_type": "manual",
            "source_url": "https://demo.sysu/activity/photo-workshop",
            "activity_type": "其他",
            "tags": "摄影,工作坊",
            "quality_score": 76,
        }),
        _upsert_poster(test.id, {
            "title": "被驳回的社团招新夜",
            "raw_text": "该活动缺少准确时间和地点，保留为驳回状态以演示重新编辑提交。",
            "summary": "用于演示驳回原因和再次提交。",
            "event_time": None,
            "location": None,
            "organizer": "测试社团",
            "status": "rejected",
            "review_comment": "请补充准确活动时间和地点后再提交。",
            "source_type": "manual",
            "source_url": "https://demo.sysu/activity/rejected-club-night",
            "activity_type": "晚会",
            "tags": "社团,招新",
            "quality_score": 52,
        }),
    ]

    for poster in posters:
        if poster.status == "published":
            rebuild_poster_knowledge(poster)

    source = _ensure_data_source()
    _ensure_dict_entries()

    db.session.flush()
    _ensure_unique(Subscription, {"notify_method": "platform"}, user_id=test.id, keyword="人工智能")
    # 给 test 用户在 2 个日期各加 3+ 日程以展示热力图深浅
    for pid in [posters[0].id, posters[1].id, posters[2].id, posters[3].id, posters[4].id, posters[5].id]:
        _ensure_unique(UserCalendarEvent, {}, user_id=test.id, poster_id=pid)
    _ensure_unique(Notification, {
        "title": "你订阅的活动有更新",
        "body": "人工智能创新应用讲座已发布，可以前往活动详情查看。",
        "is_read": False,
    }, user_id=test.id, poster_id=posters[1].id)

    redis = getattr(current_app, "redis", None)
    if redis is not None:
        redis.sadd(f"user:{test.id}:favorite_activities", posters[0].id, posters[1].id)
        redis.sadd(f"activity:{posters[0].id}:registrations", test.id)
        redis.sadd(f"activity:{posters[1].id}:registrations", test.id)

    if not getattr(seed_demo_posters, "_audit_logged", False):
        create_audit_log(
            actor_id=admin.id,
            action="seed_demo",
            target_type="demo",
            target_id=source.id,
            summary="Seeded demo accounts, activities, subscriptions, notifications, calendar and data source examples.",
        )
        seed_demo_posters._audit_logged = True

    db.session.commit()
