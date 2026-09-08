import asyncio
import os
import uuid
from pathlib import Path
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, UploadFile, File, Request, Query
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware
from fastapi.staticfiles import StaticFiles
from .catalog import ROOT,load_catalog
from .models import Draft,PoolEntry,SyncRequest
from .recommend import rank
from . import db,vision,riot

load_dotenv(ROOT/'.env')
app=FastAPI(title='Draft Coach API',version='0.1.0')
ORIGINS=['http://127.0.0.1:8000','http://localhost:8000','http://127.0.0.1:5173','http://localhost:5173']
app.add_middleware(TrustedHostMiddleware,allowed_hosts=['localhost','127.0.0.1'])
app.add_middleware(CORSMiddleware,allow_origins=ORIGINS,allow_methods=['GET','POST','PUT','DELETE'],allow_headers=['Content-Type'])
catalog=load_catalog()
known={c['id'] for c in catalog['champions']}
jobs={}
tasks=set()

@app.middleware('http')
async def local_origin(request:Request,call_next):
    if request.method not in ['GET','HEAD','OPTIONS'] and request.headers.get('origin') and request.headers['origin'] not in ORIGINS:
        return JSONResponse({'detail':'只接受本地网页的请求'},status_code=403)
    response=await call_next(request)
    response.headers['X-Content-Type-Options']='nosniff'
    response.headers['Referrer-Policy']='same-origin'
    if request.url.path.startswith('/api/'): response.headers['Cache-Control']='no-store'
    return response

@app.get('/api/status')
def status():
    return {'vision_ready':bool(os.getenv('OPENAI_API_KEY')),'riot_ready':bool(os.getenv('RIOT_API_KEY')),'patch':catalog['version'],'region':'NA','version':'0.1.0'}

@app.get('/api/champions')
def champions(): return catalog

@app.get('/api/profile')
def profile(queue:int=Query(default=420,pattern=None)):
    if queue not in [420,440]: raise HTTPException(422,'不支持的队列')
    account=db.preference('account',{})
    public_account={k:v for k,v in account.items() if k!='puuid'}
    return {'account':public_account,'pool':db.pool(),'statistics':[{'champion_id':k[0],'role':k[1],**v} for k,v in db.statistics(queue).items()]}

@app.put('/api/pool')
def save_pool(entry:PoolEntry):
    if entry.champion_id not in known: raise HTTPException(422,'未知英雄')
    with db.connect() as connection:
        connection.execute('INSERT INTO pool VALUES(?,?,?) ON CONFLICT(champion_id,role) DO UPDATE SET comfort=excluded.comfort',(entry.champion_id,entry.role,entry.comfort))
    return {'ok':True}

@app.delete('/api/pool/{role}/{champion_id}')
def delete_pool(role:str,champion_id:str):
    with db.connect() as connection: connection.execute('DELETE FROM pool WHERE role=? AND champion_id=?',(role,champion_id))
    return {'ok':True}

@app.post('/api/recommend')
def recommend(draft:Draft):
    ids=set(draft.bans)|{p.champion_id for p in draft.allies+draft.enemies if p.champion_id}
    if ids-known: raise HTTPException(422,'阵容中存在未知英雄')
    return rank(draft,catalog,db.pool(),db.statistics(draft.queue))

@app.post('/api/vision/bans')
async def bans(file:UploadFile=File(...)):
    raw=await file.read(vision.MAX_BYTES+1)
    await file.close()
    return await vision.recognize(raw,catalog)

@app.post('/api/riot/sync',status_code=202)
async def start_sync(request:SyncRequest):
    if not os.getenv('RIOT_API_KEY'): raise HTTPException(503,'请先在项目 .env 中配置 RIOT_API_KEY 并重启')
    if any(j['status']=='running' for j in jobs.values()): raise HTTPException(409,'已有同步正在进行')
    jobs.clear()
    jid=uuid.uuid4().hex; job={'id':jid,'status':'running','completed':0,'total':0,'message':'正在查找 NA 账号…'}
    jobs[jid]=job
    task=asyncio.create_task(riot.sync(request,catalog,job)); tasks.add(task); task.add_done_callback(tasks.discard)
    return job

@app.get('/api/riot/sync/{job_id}')
def sync_status(job_id:str):
    if job_id not in jobs: raise HTTPException(404,'同步任务不存在，请重新开始')
    return jobs[job_id]

# Production local mode: one origin for the built React app and Python API.
build=ROOT/'frontend/out'
if build.exists(): app.mount('/',StaticFiles(directory=build,html=True),name='web')
