"""Refresh official bilingual Data Dragon metadata + portrait assets; no API key."""
import concurrent.futures
import json
from pathlib import Path
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
def fetch(url):
    with urllib.request.urlopen(url, timeout=45) as response:
        return response.read()

def main():
    version = json.loads(fetch('https://ddragon.leagueoflegends.com/api/versions.json'))[0]
    base = f'https://ddragon.leagueoflegends.com/cdn/{version}'
    with concurrent.futures.ThreadPoolExecutor(2) as executor:
        en, zh = list(executor.map(lambda lang: json.loads(fetch(f'{base}/data/{lang}/champion.json'))['data'], ['en_US', 'zh_CN']))
    out = ROOT / 'data'
    portraits = ROOT / 'frontend/public/champions'
    out.mkdir(exist_ok=True)
    portraits.mkdir(parents=True, exist_ok=True)
    entries = [{ 'id': c['id'], 'key': int(c['key']), 'name': c['name'], 'zh': zh.get(c['id'],c)['name'], 'title': zh.get(c['id'],c)['title'], 'tags': c['tags'], 'image': f"/champions/{c['image']['full']}" } for c in en.values()]
    catalog = {'version': version, 'source': f'{base}/data/en_US/champion.json', 'champions': entries}
    (out/'champions.json').write_text(json.dumps(catalog, ensure_ascii=False, indent=2))
    def portrait(c):
        dest = portraits / c['image'].split('/')[-1]
        if not dest.exists():
            dest.write_bytes(fetch(f"{base}/img/champion/{dest.name}"))
    with concurrent.futures.ThreadPoolExecutor(8) as executor:
        list(executor.map(portrait, entries))
    print(f"Data Dragon {version}: {len(entries)} champions and portraits ready")

if __name__ == '__main__':
    main()
