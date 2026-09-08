import asyncio
import io
import json
import time
import pytest
from PIL import Image
from fastapi import HTTPException
from fastapi.testclient import TestClient
from backend.main import app
from backend import db,vision,riot
from backend.catalog import load_catalog

@pytest.fixture
def client(tmp_path,monkeypatch):
    monkeypatch.setenv('DRAFT_DB',str(tmp_path/'test.db'))
    monkeypatch.delenv('RIOT_API_KEY',raising=False)
    monkeypatch.delenv('OPENAI_API_KEY',raising=False)
    return TestClient(app,base_url='http://localhost')

def test_manual_mvp_works_without_credentials(client):
    assert len(client.get('/api/champions').json()['champions'])>=170
    assert client.get('/api/status').json()['vision_ready'] is False
    assert client.put('/api/pool',json={'champion_id':'Nami','role':'UTILITY','comfort':5}).status_code==200
    recs=client.post('/api/recommend',json={'role':'UTILITY','pool_only':True}).json()['recommendations']
    assert recs[0]['champion']['id']=='Nami' and recs[0]['win_rate'] is None
    assert client.delete('/api/pool/UTILITY/Nami').status_code==200
    assert client.get('/api/profile').json()['pool']==[]

def test_invalid_and_foreign_requests(client):
    assert client.post('/api/recommend',json={'bans':['NotAChampion']}).status_code==422
    assert client.put('/api/pool',json={'champion_id':'Nami','role':'UTILITY','comfort':100}).status_code==422
    assert client.put('/api/pool',headers={'Origin':'https://untrusted.example'},json={'champion_id':'Nami','role':'UTILITY','comfort':5}).status_code==403

def test_missing_api_configuration_is_actionable(client):
    r=client.post('/api/vision/bans',files={'file':('ban.png',b'image','image/png')})
    assert r.status_code==503 and 'OPENAI_API_KEY' in r.json()['detail']
    r=client.post('/api/riot/sync',json={'game_name':'Name','tag_line':'NA1'})
    assert r.status_code==503

def test_queue_window_recency_and_player_isolation(client):
    now=time.time(); db.set_preference('account',{'puuid':'mine'})
    rows=[('NA1_1','mine','Lux','MIDDLE',420,1,now),('NA1_2','mine','Lux','MIDDLE',420,0,now-30*86400),('NA1_3','mine','Lux','MIDDLE',440,1,now),('NA1_4','other','Lux','MIDDLE',420,1,now),('NA1_5','mine','Lux','MIDDLE',420,0,now-100*86400)]
    with db.connect() as connection: connection.executemany('INSERT INTO matches VALUES(?,?,?,?,?,?,?)',rows)
    stats=db.statistics(420,now)[('Lux','MIDDLE')]
    assert stats['games']==2 and stats['wins']==1
    assert stats['weighted_games']==pytest.approx(1.5)
    assert db.statistics(440,now)[('Lux','MIDDLE')]['games']==1

def test_vision_unknown_id_empty_slot_and_repeated_slots():
    data={'slots':[{'side':'left','slot':0,'champion_id':'Imaginary','state':'champion'},{'side':'left','slot':1,'champion_id':None,'state':'empty'},{'side':'left','slot':1,'champion_id':'Lux','state':'champion'},{'side':'right','slot':0,'champion_id':'Lux','state':'champion'}]}
    slots=vision.normalize_slots(data,{'Lux'})
    assert len(slots)==3 and slots[0]['state']=='uncertain' and slots[0]['champion_id'] is None
    assert slots[1]['state']=='empty' and slots[2]['champion_id']=='Lux'

def test_image_validation_and_context_preservation():
    out=io.BytesIO();Image.new('RGB',(1400,700),'#333333').save(out,format='PNG')
    parts=vision.image_inputs(out.getvalue())
    assert len(parts)==2 and all(p['type']=='input_image' for p in parts)
    with pytest.raises(HTTPException): vision.image_inputs(b'not an image')
    with pytest.raises(HTTPException) as err: vision.image_inputs(b'x'*(vision.MAX_BYTES+1))
    assert err.value.status_code==413

def test_only_own_ranked_non_remake_match_is_retained():
    data={'metadata':{'matchId':'NA1_1'},'info':{'queueId':420,'gameDuration':1400,'gameStartTimestamp':1_700_000_000_000,'participants':[{'puuid':'mine','teamPosition':'UTILITY','championId':25,'win':True},{'puuid':'other','teamPosition':'BOTTOM','championId':22,'win':False}]}}
    row=riot.participant_record(data,'mine',load_catalog()['champions'])
    assert row[2:6]==('Morgana','UTILITY',420,1)
    data['info']['participants'][0]['gameEndedInEarlySurrender']=True
    assert riot.participant_record(data,'mine',load_catalog()['champions']) is None

def test_openai_request_uses_image_and_validated_structured_output(client,monkeypatch):
    monkeypatch.setenv('OPENAI_API_KEY','test-secret')
    out=io.BytesIO();Image.new('RGB',(100,100),'navy').save(out,format='PNG')
    captured={}
    class Response:
        status_code=200
        def json(self):return {'status':'completed','output':[{'content':[{'type':'output_text','text':json.dumps({'slots':[{'side':'left','slot':0,'champion_id':'Lux','state':'champion'}]})}]}]}
    class MockClient:
        def __init__(self,**kwargs):pass
        async def __aenter__(self):return self
        async def __aexit__(self,*args):pass
        async def post(self,url,**kwargs):captured.update(kwargs);return Response()
    monkeypatch.setattr(vision.httpx,'AsyncClient',MockClient)
    r=client.post('/api/vision/bans',files={'file':('ban.png',out.getvalue(),'image/png')})
    assert r.status_code==200 and r.json()['slots'][0]['champion_id']=='Lux'
    assert captured['json']['text']['format']['strict'] is True
    assert captured['json']['input'][0]['content'][1]['type']=='input_image'
    assert 'test-secret' not in r.text
