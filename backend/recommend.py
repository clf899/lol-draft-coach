"""Transparent kit heuristics; scores are NOT probabilities of winning."""
from collections import defaultdict
from .models import Draft

def rank(draft: Draft, catalog: dict, pool: list, statistics: dict):
    champs = {c['id']:c for c in catalog['champions']}
    # The user's own slot is a candidate to replace, not an ally to reward.
    allies = [p for p in draft.allies if p.champion_id and p.role != draft.role]
    enemies = [p for p in draft.enemies if p.champion_id]
    excluded = set(draft.bans) | {p.champion_id for p in allies+enemies}
    personal = {p['champion_id']:p for p in pool if p['role']==draft.role}
    def weight(p): return 1.0 if p.status=='locked' else 0.45
    def presence(picks):
        result = defaultdict(float)
        for p in picks:
            for trait in champs[p.champion_id]['traits']: result[trait] += weight(p)
        return result
    a, e = presence(allies), presence(enemies)
    opponent_role = {'UTILITY':'BOTTOM','BOTTOM':'BOTTOM'}.get(draft.role,draft.role)
    lane_enemies = [p for p in enemies if p.role == opponent_role or (draft.role in ['BOTTOM','UTILITY'] and p.role=='UTILITY')]
    lane_known = any(p.role for p in lane_enemies)
    lane = presence(lane_enemies)
    uncertain = any(p.status=='hover' for p in allies+enemies) or len(enemies)<5 or any(p.role is None for p in enemies)
    result = []
    for c in champs.values():
        cid = c['id']; traits=set(c['traits'])
        if cid in excluded or (draft.pool_only and cid not in personal): continue
        if draft.role not in c['roles'] and cid not in personal: continue
        s = statistics.get((cid,draft.role),{})
        games=s.get('games',0); wins=s.get('wins',0)
        wg=s.get('weighted_games',games); ww=s.get('weighted_wins',wins)
        adjusted=(ww+20)/(wg+40)
        comfort=personal.get(cid,{}).get('comfort')
        personal_score = 20 + (comfort-3)*6 if comfort else 17
        personal_score = max(0,min(40,personal_score + (adjusted-.5)*24))
        composition=12.; matchup=10.; synergy=7.
        reasons=[]; risks=[]
        if comfort:
            reasons.append(f'你的熟练度 {comfort}/5' + ('，适合作为稳定选择' if comfort>=4 else ''))
        else: risks.append('尚未标注个人熟练度')
        if games: reasons.append(f'该位置近 90 天已同步 {games} 场，胜率 {wins/games:.0%}')
        if games<10: risks.append('个人样本不足，胜率对排序的影响已降低')
        if allies:
            if 'frontline' in traits and a['frontline']<1:
                bonus=6*(1-min(1,a['frontline'])); composition+=bonus; reasons.append('补足目前阵容的前排')
            if 'engage' in traits and a['engage']<1:
                composition+=5*(1-min(1,a['engage'])); reasons.append('提供主动开团手段')
            if 'peel' in traits and a['carry']>0:
                composition+=min(4,a['carry']*3); reasons.append('为队伍输出位提供保护')
            damage_weight=sum(weight(p) for p in allies if champs[p.champion_id]['damage']!=c['damage'])
            same_weight=sum(weight(p) for p in allies if champs[p.champion_id]['damage']==c['damage'])
            if same_weight<.5 and damage_weight>=2:
                composition+=4; reasons.append('改善队伍物理与魔法伤害分布')
            elif same_weight>=3 and draft.role!='UTILITY':
                composition-=3; risks.append('队伍伤害类型比较集中')
        if 'antidive' in traits or 'peel' in traits:
            if e['dive']>0: matchup+=min(8,e['dive']*3); reasons.append('技能组有助于应对敌方突进')
        if 'sustain' in traits and e['poke']>0:
            matchup+=min(5,e['poke']*2); reasons.append('续航有助于承受敌方消耗')
        if lane_known and draft.role != 'JUNGLE':
            if 'sustain' in traits and lane['poke']>0:
                matchup+=min(3,lane['poke']*2); reasons.append('对线续航可缓解已知对手的消耗压力')
            if 'antidive' in traits and lane['dive']>0:
                matchup+=min(3,lane['dive']*2); reasons.append('对线具有应对突进的技能手段')
            if 'poke' in traits and lane['sustain']>0:
                matchup-=min(3,lane['sustain']); risks.append('对线对手具备续航，消耗收益可能受限')
        if 'dive' in traits and e['antidive']>0:
            matchup-=min(6,e['antidive']*2); risks.append('敌方有反突进手段，进场时机要求较高')
        if 'poke' in traits and e['dive']>=1 and 'peel' not in traits:
            matchup-=min(4,e['dive']); risks.append('需注意敌方突进，保持输出距离')
        if draft.role in ['UTILITY','BOTTOM']:
            partner_role='BOTTOM' if draft.role=='UTILITY' else 'UTILITY'
            partner=next((p for p in allies if p.role==partner_role),None)
            if partner:
                pt=set(champs[partner.champion_id]['traits']); w=weight(partner)
                if ('engage' in traits and 'aoe' in pt) or ('aoe' in traits and 'engage' in pt):
                    synergy+=6*w; reasons.append('下路搭档可衔接控制与范围伤害')
                if ('peel' in traits and 'carry' in pt) or ('carry' in traits and 'peel' in pt):
                    synergy+=5*w; reasons.append('下路具备保护与持续输出的配合')
        if cid=='Yasuo' and a['knockup']>0:
            synergy+=min(8,a['knockup']*4); reasons.append('队友击飞可以提供接大机会')
        if 'knockup' in traits and any(p.champion_id=='Yasuo' for p in allies):
            synergy+=6*next(weight(p) for p in allies if p.champion_id=='Yasuo'); reasons.append('击飞技能可配合亚索')
        if not lane_known and enemies: risks.append('敌方对线位置未确定，当前以整体阵容判断')
        if any(p.status=='hover' for p in allies+enemies): risks.append('预选按 45% 权重参与，锁定后会重新评估')
        parts={'personal':round(personal_score,1),'composition':round(max(0,min(25,composition)),1),'matchup':round(max(0,min(20,matchup)),1),'synergy':round(max(0,min(15,synergy)),1)}
        result.append({'champion':c,'score':round(sum(parts.values()),1),'components':parts,'reasons':reasons[:5] or ['可用于当前选择的位置'],'risks':risks[:4], 'comfort':comfort, 'games':games,'wins':wins,'win_rate':round(wins/games*100,1) if games else None,'uncertain':uncertain})
    result.sort(key=lambda x:(-x['score'],-(x['comfort'] or 0),-x['games'],x['champion']['name']))
    return {'recommendations':result[:5], 'candidates':len(result), 'method':'kit-rules-v1', 'patch':catalog['version'], 'uncertain':uncertain, 'note':'适配评分不是获胜概率；阵容部分来自技能组规则，不是全服克制胜率。'}
