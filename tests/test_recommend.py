import pytest
from pydantic import ValidationError
from backend.catalog import load_catalog,ROLES
from backend.models import Draft,Pick
from backend.recommend import rank

CATALOG=load_catalog()
def get(draft,pool=None,stats=None,patch_stats=None): return rank(draft,CATALOG,pool or [],stats or {},patch_stats)['recommendations']

@pytest.mark.parametrize('role',ROLES)
def test_all_roles_have_five_valid_candidates(role):
    recs=get(Draft(role=role))
    assert len(recs)==5
    assert all(role in r['champion']['roles'] and 0<=r['score']<=100 for r in recs)

def test_picks_bans_and_user_slot():
    draft=Draft(role='UTILITY',bans=['Leona'],allies=[Pick(champion_id='Nami',role='UTILITY',status='hover'),Pick(champion_id='MissFortune',role='BOTTOM')],enemies=[Pick(champion_id='Nautilus',role='UTILITY')],pool_only=True)
    pool=[{'champion_id':c,'role':'UTILITY','comfort':5} for c in ['Leona','Nami','Nautilus']]
    assert [r['champion']['id'] for r in get(draft,pool)]==['Nami']

def test_pick_conflict_is_rejected():
    with pytest.raises(ValidationError): Draft(bans=['Leona'],allies=[Pick(champion_id='Leona')])
    with pytest.raises(ValidationError): Draft(allies=[Pick(champion_id='Lux')],enemies=[Pick(champion_id='Lux')])

def test_small_perfect_sample_does_not_dominate_established_record():
    d=Draft(pool_only=True)
    pool=[{'champion_id':'Soraka','role':'UTILITY','comfort':4}]
    small=get(d,pool,{('Soraka','UTILITY'):{'games':3,'wins':3}})[0]
    established=get(d,pool,{('Soraka','UTILITY'):{'games':80,'wins':46}})[0]
    assert established['components']['personal']>small['components']['personal']
    assert small['win_rate']==100 # True observed rate stays distinct from score.

def test_role_statistics_do_not_leak():
    r=get(Draft(role='UTILITY',pool_only=True),[{'champion_id':'Lux','role':'UTILITY','comfort':4}],{('Lux','MIDDLE'):{'games':50,'wins':40}})[0]
    assert r['games']==0 and r['win_rate'] is None

def test_hover_counts_less_than_lock():
    pool=[{'champion_id':'Janna','role':'UTILITY','comfort':4}]
    hovered=get(Draft(pool_only=True,enemies=[Pick(champion_id='Zed',status='hover')]),pool)[0]
    locked=get(Draft(pool_only=True,enemies=[Pick(champion_id='Zed',status='locked')]),pool)[0]
    assert locked['components']['matchup']>hovered['components']['matchup']

def test_personal_pool_is_role_specific_and_allows_off_meta():
    pool=[{'champion_id':'Talon','role':'UTILITY','comfort':5},{'champion_id':'Nami','role':'MIDDLE','comfort':5}]
    recs=get(Draft(role='UTILITY',pool_only=True),pool)
    assert [r['champion']['id'] for r in recs]==['Talon']
    assert get(Draft(role='TOP',pool_only=True),pool)==[]

def test_known_lane_position_changes_assessment():
    pool=[{'champion_id':'Soraka','role':'UTILITY','comfort':4}]
    unknown=get(Draft(pool_only=True,enemies=[Pick(champion_id='Xerath')]),pool)[0]
    known=get(Draft(pool_only=True,enemies=[Pick(champion_id='Xerath',role='UTILITY')]),pool)[0]
    assert known['components']['matchup']>unknown['components']['matchup']

def test_current_patch_strength_and_direct_matchup_affect_ranking():
    draft=Draft(role='UTILITY',pool_only=True,enemies=[Pick(champion_id='Thresh',role='UTILITY')])
    pool=[{'champion_id':'Morgana','role':'UTILITY','comfort':3},{'champion_id':'Nami','role':'UTILITY','comfort':3}]
    patch_stats={
        'patch':'16.17','rows':400,
        'champions':{('Morgana','UTILITY'):{'games':100,'wins':55},('Nami','UTILITY'):{'games':100,'wins':45}},
        'matchups':{('Morgana','Thresh','UTILITY'):{'games':40,'wins':24},('Nami','Thresh','UTILITY'):{'games':40,'wins':16}},
    }
    recs=get(draft,pool,patch_stats=patch_stats)
    morgana=next(r for r in recs if r['champion']['id']=='Morgana')
    nami=next(r for r in recs if r['champion']['id']=='Nami')
    assert morgana['score']>nami['score']
    assert morgana['matchup_games']==40 and morgana['global_games']==100

def test_one_match_is_smoothed_instead_of_dominating():
    draft=Draft(role='UTILITY',pool_only=True,enemies=[Pick(champion_id='Thresh',role='UTILITY')])
    pool=[{'champion_id':'Morgana','role':'UTILITY','comfort':3}]
    baseline=get(draft,pool)[0]['components']['matchup']
    patch_stats={'patch':'16.17','rows':2,'champions':{},'matchups':{('Morgana','Thresh','UTILITY'):{'games':1,'wins':1}}}
    observed=get(draft,pool,patch_stats=patch_stats)[0]['components']['matchup']
    assert 0 < observed-baseline < 2
