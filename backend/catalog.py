import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ROLES = ['TOP', 'JUNGLE', 'MIDDLE', 'BOTTOM', 'UTILITY']
ROLE_NAMES = dict(zip(ROLES, ['上单', '打野', '中单', '下路', '辅助']))
# Editorial role/kit labels, not patch-specific popularity or matchup statistics.
ROLE_LISTS = {
 'TOP': 'Aatrox Akali Ambessa Aurora Camille Chogath Darius DrMundo Fiora Gangplank Garen Gnar Gragas Gwen Heimerdinger Illaoi Irelia Jax Jayce KSante Kayle Kennen Kled Malphite Maokai Mordekaiser Nasus Olaf Ornn Pantheon Poppy Quinn Renekton Rengar Riven Rumble Ryze Sett Shen Singed Sion Smolder TahmKench Teemo Trundle Tryndamere Urgot Vayne Vladimir Volibear Warwick MonkeyKing Yasuo Yone Yorick Zaahen',
 'JUNGLE': 'Amumu Belveth Brand Briar Chogath Diana DrMundo Ekko Elise Evelynn Fiddlesticks Graves Gragas Gwen Hecarim Ivern JarvanIV Jax Karthus Kayn Khazix Kindred LeeSin Lillia MasterYi Morgana Naafiri Nidalee Nocturne Nunu Olaf Pantheon Poppy Qiyana Rammus RekSai Rell Rengar Sejuani Shaco Shyvana Skarner Sylas Talon Taliyah Trundle Udyr Vi Viego Volibear Warwick MonkeyKing XinZhao Zac Zed Zyra',
 'MIDDLE': 'Ahri Akali Akshan Anivia Annie AurelionSol Aurora Azir Brand Cassiopeia Chogath Corki Diana Ekko Fizz Galio Gragas Heimerdinger Hwei Irelia Jayce Kassadin Katarina Kayle Kennen Leblanc Lissandra Lucian Lux Malphite Malzahar Mel Morgana Naafiri Neeko Orianna Pantheon Qiyana Ryze Seraphine Smolder Swain Sylas Syndra Taliyah Talon Tristana TwistedFate Veigar Velkoz Vex Viktor Vladimir Xerath Yasuo Yone Zed Ziggs Zoe Zyra',
 'BOTTOM': 'Aphelios Ashe Caitlyn Corki Draven Ezreal Hwei Jhin Jinx Kaisa Kalista Karthus KogMaw Lucian MissFortune Nilah Samira Senna Seraphine Sivir Smolder Swain Tristana Twitch Varus Vayne Veigar Xayah Yasuo Yunara Zeri Ziggs',
 'UTILITY': 'Alistar Amumu Ashe Bard Blitzcrank Brand Braum Camille Elise Fiddlesticks Galio Gragas Heimerdinger Hwei Ivern Janna Karma Leona Lulu Lux Malphite Maokai Milio Morgana Nami Nautilus Neeko Pantheon Poppy Pyke Rakan Rell Renata Senna Seraphine Sett Shaco Shen Sona Soraka Swain TahmKench Taric Thresh Velkoz Xerath Yuumi Zilean Zyra',
}
TRAIT_LISTS = {
 'engage': 'Alistar Amumu Annie Ashe Blitzcrank Diana Galio Gragas Hecarim JarvanIV Kennen Kled Leona Lissandra Malphite Maokai Nautilus Neeko Nocturne Ornn Rakan Rell Sejuani Sett Shen Sion Skarner Thresh Vi Volibear Warwick MonkeyKing XinZhao Yone Zac',
 'peel': 'Alistar Anivia Braum Galio Gragas Ivern Janna Karma Lulu Milio Morgana Nami Poppy Rakan Renata Seraphine Shen Sona Soraka TahmKench Taric Thresh Zilean',
 'frontline': 'Alistar Amumu Braum Chogath DrMundo Galio Garen Gnar Gragas Hecarim Illaoi JarvanIV KSante Kled Leona Malphite Maokai Mordekaiser Nasus Nautilus Nunu Olaf Ornn Poppy Rammus Rell Renekton Sejuani Sett Shen Singed Sion Skarner TahmKench Taric Trundle Udyr Urgot Volibear Warwick MonkeyKing Zac',
 'dive': 'Aatrox Akali Ambessa Belveth Briar Camille Diana Ekko Elise Evelynn Fizz Gwen Hecarim Irelia JarvanIV Jax Kassadin Katarina Kayn Khazix Kled LeeSin MasterYi Naafiri Nocturne Pantheon Qiyana RekSai Renekton Rengar Riven Shaco Sylas Talon Vi Viego Warwick MonkeyKing XinZhao Yasuo Yone Zed',
 'poke': 'Ashe Azir Brand Caitlyn Corki Ezreal Heimerdinger Hwei Jayce Karma Lux Nidalee Senna Varus Velkoz Xerath Ziggs Zoe Zyra',
 'sustain': 'Bard Ivern Janna Karma Lulu Milio Nami Rakan Senna Seraphine Sona Soraka Taric Yuumi Zilean',
 'knockup': 'Alistar Blitzcrank Braum Chogath Diana Galio Gragas Janna JarvanIV Malphite Maokai Nami Nautilus Nunu Ornn Poppy Rakan RekSai Rell Sion Vi MonkeyKing XinZhao Yone Zac',
 'aoe': 'Amumu Annie Brand Diana Fiddlesticks Galio Gangplank Hwei Karthus Kennen Lillia Lissandra Lux Malphite MissFortune Neeko Orianna Rell Rumble Seraphine Sona Swain Viktor MonkeyKing Xayah Yasuo Yone Ziggs Zyra',
 'carry': 'Aphelios Ashe Azir Caitlyn Cassiopeia Draven Jinx Kaisa Kalista Kayle Kindred KogMaw Lucian MasterYi Nilah Samira Sivir Smolder Tristana Twitch Varus Vayne Xayah Yasuo Yone Yunara Zeri',
 'antidive': 'Alistar Braum Galio Janna Lulu Lissandra Malzahar Poppy Rammus Renata Shen TahmKench Taric Vex',
}
ALIASES = {
 'MissFortune':'mf 女枪 赏金', 'MonkeyKing':'wukong 猴子', 'Nasus':'狗头', 'Renekton':'鳄鱼', 'Azir':'沙皇',
 'Twitch':'老鼠', 'Vayne':'vn 薇恩', 'JarvanIV':'皇子 j4', 'LeeSin':'盲僧 瞎子', 'Khazix':'螳螂', 'Rengar':'狮子狗',
 'Chogath':'大虫子', 'KogMaw':'大嘴', 'Nautilus':'泰坦', 'Blitzcrank':'机器人', 'Leona':'日女 女坦',
 'Soraka':'奶妈', 'Lulu':'露露', 'Janna':'风女', 'Nami':'娜美', 'Sona':'琴女', 'Seraphine':'萨勒芬妮 歌姬',
 'Morgana':'莫甘娜', 'Shaco':'小丑', 'Talon':'男刀', 'Irelia':'刀妹', 'Riven':'锐雯 瑞文', 'Yasuo':'亚索',
 'Yone':'永恩', 'Warwick':'狼人', 'Kindred':'千珏 狼狗', 'Ambessa':'狼母', 'Aurora':'兔子',
 'Hecarim':'人马', 'MasterYi':'剑圣', 'Fiora':'剑姬', 'Tryndamere':'蛮王', 'Gangplank':'船长',
 'DrMundo':'蒙多', 'TwistedFate':'卡牌 tf', 'Fiddlesticks':'稻草人', 'Malphite':'石头人', 'AurelionSol':'龙王',
 'Tristana':'小炮', 'Jinx':'金克丝', 'Swain':'乌鸦', 'Elise':'蜘蛛', 'Rell':'芮尔', 'Renata':'烈娜塔',
 'Bard':'巴德', 'Pyke':'派克', 'Milio':'米利欧', 'Thresh':'锤石', 'Lux':'拉克丝 光辉',
 'Nocturne':'noc 梦魇', 'Velkoz':'大眼', 'Anivia':'冰鸟', 'Kassadin':'卡萨丁', 'Katarina':'卡特',
 'TahmKench':'蛤蟆 塔姆', 'KSante':'奎桑提', 'Nunu':'努努 雪人', 'Kaisa':'卡莎', 'Lucian':'卢锡安 奥巴马',
 'Graves':'男枪', 'XinZhao':'赵信', 'Nidalee':'豹女', 'RekSai':'挖掘机', 'Viego':'破败王', 'Belveth':'卑尔维斯',
 'Veigar':'小法', 'Heimerdinger':'大头', 'Mordekaiser':'铁男', 'Orianna':'发条', 'Ziggs':'炸弹人',
}

def load_catalog():
    data = json.loads((ROOT/'data/champions.json').read_text())
    for c in data['champions']:
        c['roles'] = [r for r, ids in ROLE_LISTS.items() if c['id'] in ids.split()]
        if not c['roles']:
            c['roles'] = ['MIDDLE'] if 'Mage' in c['tags'] else ['BOTTOM'] if 'Marksman' in c['tags'] else ['UTILITY'] if 'Support' in c['tags'] else ['TOP','JUNGLE']
        c['traits'] = [t for t, ids in TRAIT_LISTS.items() if c['id'] in ids.split()]
        c['damage'] = 'magic' if 'Mage' in c['tags'] else 'physical'
        if c['id'] in 'Akali Diana Ekko Elise Evelynn Fizz Gwen Karthus Kennen Lillia Rumble Shyvana Teemo'.split(): c['damage']='magic'
        c['aliases'] = ALIASES.get(c['id'], '')
    return data
