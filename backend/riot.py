import asyncio
import os
import time
from urllib.parse import quote
import httpx
from . import db

class RiotError(Exception): pass

class RiotClient:
    def __init__(self,client):
        self.client=client; self.last=0
    async def get(self,path,platform=False,params=None):
        interval=max(1.21,float(os.getenv('RIOT_REQUEST_INTERVAL','1.25')))
        key=os.getenv('RIOT_API_KEY')
        if not key: raise RiotError('尚未配置 RIOT_API_KEY，请在 .env 中添加后重启')
        host='na1' if platform else 'americas'
        for attempt in range(3):
            await asyncio.sleep(max(0,interval-(time.monotonic()-self.last)))
            self.last=time.monotonic()
            try:
                r=await self.client.get(f'https://{host}.api.riotgames.com{path}',params=params,headers={'X-Riot-Token':key})
            except httpx.HTTPError: raise RiotError('Riot 连接失败，请稍后重试')
            if r.status_code==429:
                try: pause=float(r.headers.get('Retry-After',5))
                except ValueError: pause=5
                if pause>60: raise RiotError('Riot 暂时限流，请稍后重新同步')
                await asyncio.sleep(max(1,min(60,pause)))
                continue
            if r.status_code in [401,403]: raise RiotError('Riot API Key 无效或已过期，请更新后重启')
            if r.status_code==404: raise RiotError('未找到该 Riot ID 或比赛，请检查名称和标签')
            if r.status_code>=500 and attempt<2:
                await asyncio.sleep(2); continue
            if r.status_code!=200: raise RiotError(f'Riot 请求失败（{r.status_code}），请稍后重试')
            return r.json()
        raise RiotError('Riot 暂时限流，请稍后重新同步')

def participant_record(data, puuid, champions):
    info=data.get('info',{})
    if info.get('queueId') not in [420,440] or info.get('gameDuration',0)<300: return None
    p=next((p for p in info.get('participants',[]) if p.get('puuid')==puuid),None)
    if not p or p.get('gameEndedInEarlySurrender'): return None
    role=p.get('teamPosition')
    if role not in ['TOP','JUNGLE','MIDDLE','BOTTOM','UTILITY']: return None
    c=next((c for c in champions if c['key']==p.get('championId')),None)
    if not c: return None
    return (data['metadata']['matchId'],puuid,c['id'],role,info['queueId'],int(p['win']),info['gameStartTimestamp']/1000)

async def sync(request,catalog,job):
    # Only one job is allowed at a time in main.py, keeping one shared rate budget.
    try:
        async with httpx.AsyncClient(timeout=25) as client:
            riot=RiotClient(client)
            account=await riot.get('/riot/account/v1/accounts/by-riot-id/'+quote(request.game_name,safe='')+'/'+quote(request.tag_line,safe=''))
            # Validate NA presence before accepting an account from global Riot IDs.
            await riot.get('/lol/summoner/v4/summoners/by-puuid/'+quote(account['puuid'],safe=''),platform=True)
            ids=await riot.get('/lol/match/v5/matches/by-puuid/'+quote(account['puuid'],safe='')+'/ids',params={'queue':request.queue,'start':0,'count':request.count,'startTime':int(time.time()-90*86400)})
            job['total']=len(ids)
            staged=[]
            for i,mid in enumerate(ids):
                with db.connect() as connection:
                    exists=connection.execute('SELECT 1 FROM matches WHERE match_id=? AND puuid=?',(mid,account['puuid'])).fetchone()
                if not exists:
                    record=participant_record(await riot.get('/lol/match/v5/matches/'+quote(mid,safe='')),account['puuid'],catalog['champions'])
                    if record: staged.append(record)
                job['completed']=i+1
            # Commit new matches and switch active account only after a complete sync.
            with db.connect() as connection:
                connection.executemany('INSERT OR IGNORE INTO matches VALUES(?,?,?,?,?,?,?)',staged)
            db.set_preference('account',{'puuid':account['puuid'],'game_name':account.get('gameName',request.game_name),'tag_line':account.get('tagLine',request.tag_line),'synced_at':time.time()})
            job.update(status='done',message=f'已检查 {len(ids)} 场，新增 {len(staged)} 场有效排位记录')
    except RiotError as exc: job.update(status='error',message=str(exc))
    except Exception: job.update(status='error',message='同步失败，原有战绩已保留，请稍后重试')
