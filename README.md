# Draft Coach

为你自己的英雄池做选择的英雄联盟 BP 助手。NA · 五个位置 · Mac 本地网页。

## 在 Mac 上启动

解压进入项目目录，运行：

```bash
bash scripts/start.sh
```

然后打开 **http://127.0.0.1:8000**。需要 Python 3.11+；源代码仓库首次构建还需要 Node.js 22.13+。交付 ZIP 包包含构建好的网页，首次使用无需 Node。安装依赖时需要联网。

不填 API Key 也可以使用手动 BP、英雄池和推荐。首次启动会从 `.env.example` 建立 `.env`。

```dotenv
OPENAI_API_KEY=填写你的图片理解API密钥
OPENAI_VISION_MODEL=gpt-4.1-mini
RIOT_API_KEY=填写你的RiotAPI密钥
RIOT_REQUEST_INTERVAL=1.25
```

填写后重启。密钥只留在后端环境中；不要上传 `.env`。图片调用使用独立的 API 服务额度。

## 使用流程

1. 选自己的位置、单／双排或灵活排位。
2. 在「我的英雄池」里按位置添加英雄，设置熟练度 1–5；可加入非主流位置英雄。
3. 输入双方阵容，分别标记锁定／预选。敌方位置不确定时保持「位置未知」。自己的预选可以留在自己的位置，推荐引擎会比较替换候选。
4. 点击 Ban 空位手动添加，或将 BP 图片拖入底部 Ban 区域，或使用 ⌘V 粘贴图片。
5. 在识别结果中检查头像，校正不确定项，再点击应用；新截图结果与已有 Ban 合并。点击 Ban 头像可移除。
6. 通过右上角「账号与连接」填写 Riot 名称和标签，同步 NA 账号近 90 天、最近 20/50/100 场的指定排位队列记录。首次同步较慢，可继续操作 BP。

## 已实现的范围

- 173 位英雄（随附 Data Dragon 16.17.1），中英文名称、中文称号及常用简称搜索，本地英雄头像。
- 五个位置的手动输入，已锁定、预选、未知位置，Ban/已选冲突检查。
- 按位置维护英雄池与手动熟练度，SQLite 持久化；当前 BP 仅保存在当前浏览器标签页。
- 自动更新 Top 5、评分分项、推荐理由、风险、真实个人胜率与样本量。
- 图片拖放、文件上传和剪贴板粘贴；视觉 LLM + 结构化输出；结果可编辑。
- Riot ID 查找、NA 账号校验、Match-V5 排位同步、限流、任务进度、本机缓存和去重。
- API 未配置、网络失败、限流、无可选英雄、无战绩与图片无法辨认的提示。

## 推荐如何计算

这是一版**可解释的技能组规则引擎**，不是训练好的胜率预测器，也未接入全服 counter/synergy 统计。角色与技能标签是人工维护的启发式元数据；版本号来自官方英雄资料，并不表示规则已按该版本统计校准。

| 分项 | 上限 | 输入 |
| --- | ---: | --- |
| 个人表现 | 40 | 分位置熟练度、同期同队列个人战绩 |
| 阵容补足 | 25 | 前排、开团、保护、粗略伤害分布 |
| 敌方应对 | 20 | 突进、反突进、消耗、续航及已知对线位置 |
| 队友配合 | 15 | 下路控制与范围伤害、保护输出、亚索击飞配合 |

预选以 0.45 权重参与。比赛使用 30 天半衰期；个人胜率向 50% 基准收缩，先验强度为 40 场：`(加权胜场 + 20) / (加权场次 + 40)`。页面仍显示未修正的真实胜率，不把评分展示为赢面。

不确定位置按当前已知的整体阵容判断，并标记信息不足。尚未实现对所有敌方位置排列的概率枚举。若没有个人英雄池，通用候选来自人工位置标签。粗粒度标签无法涵盖全部装备变化、技能交互和选手操作水平。

## 图片识别的实现与限制

FastAPI 校验图片类型、大小和像素数，纠正 EXIF 方向。模型同时看到完整图片和顶部细节条，自己定位客户端与 Ban 栏；没有硬编码固定分辨率，也不依赖韩文或英文文字 OCR。**当前没有单独训练的客户端边框检测器**。

模型输出位置、槽位、标准英雄 ID、已识别／空／不确定状态。后端校验英雄 ID 和槽位；不合法的 ID 变为待确认。不同队伍可能重复 Ban，应用时去重；局部截图不清除已有 Ban。本应用不持久保存上传截图，识别完成后不保留上传文件；API 请求设为 `store:false`，服务商数据政策仍适用。

外部模型调用和 Riot 同步已实现；开发环境未提供两项 API Key，所以未进行真实付费图片识别或真实账号同步。接口契约与异常路径用模拟响应验证。必须在自己的 NA/Mac 截图上实测准确率、延迟和模型选择；不把模型自报置信度当准确概率。

## 开发

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.lock
pip install pytest
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```

另开终端：

```bash
cd frontend
npm ci
npm run dev:local
```

开发网页通过 Vite 代理 `/api` 到 Python。正式本地运行使用同源 FastAPI 托管 React 构建产物，避免浏览器配置密钥。

```bash
python -m pytest -q
cd frontend
npm run typecheck
npm run build:local
```

`frontend/vite.local.config.ts` 是 MVP 的 Vite/React 构建入口。保留的 Sites/Vinext 脚手架用于未来网页托管；它不包含 Python 服务，不能把前端单独发布后当作完整线上版本。

刷新英雄资料和头像：`python scripts/refresh_catalog.py`。人工位置、技能标签与简称位于 `backend/catalog.py`，评分逻辑位于 `backend/recommend.py`。

## GitHub

项目仓库：[clf899/lol-draft-coach](https://github.com/clf899/lol-draft-coach)。

```bash
git clone https://github.com/clf899/lol-draft-coach.git
cd lol-draft-coach
bash scripts/start.sh
```

从仓库首次运行需要 Python 3.11+ 和 Node.js 22.13+；启动脚本会安装依赖并构建网页。请把 API Key 填在本机 `.env` 中。源码不包含个人密钥、比赛数据库或上传的截图。

## 后续扩展

- 用真实 BP 样本评估识别，并校准规则。
- 接入合法获得、按版本与段位分层的 matchup / synergy 统计。
- 使用 `Draft` 统一输入模型接入 Mac 本地客户端读取器，复用推荐引擎。
- 开放多人使用前增加应用身份验证、按用户隔离数据、限额、数据库迁移及适当 Riot API 申请。当前服务只绑定 `127.0.0.1`，是单用户本地版。

## 数据与文档

- [Riot Data Dragon](https://developer.riotgames.com/docs/lol#data-dragon)
- [Riot API 与 Key 类型](https://developer.riotgames.com/docs/portal)：开发 Key 每 24 小时失效；个人与公开产品的 Key 用途不同。
- [Riot 游戏与客户端接口政策](https://developer.riotgames.com/docs/lol)
- [OpenAI 图片理解](https://developers.openai.com/api/docs/guides/images-vision)
- [结构化输出](https://developers.openai.com/api/docs/guides/structured-outputs)

Draft Coach is not endorsed by Riot Games and does not reflect the views or opinions of Riot Games or anyone officially involved in producing or managing Riot Games properties. Riot Games and all associated properties are trademarks or registered trademarks of Riot Games, Inc.
