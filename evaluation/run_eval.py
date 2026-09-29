import csv, json, re, sys, time
from pathlib import Path
import requests

ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / 'evaluation' / 'questions.csv'
RESULTS = ROOT / 'evaluation' / 'results.csv'
SCORES = ROOT / 'evaluation' / 'scores.csv'
API = 'http://localhost:8000/api/ask'


def expected_hit(expected_doc, expected_section, result):
    if expected_doc == 'NONE': return False
    hay = ' '.join([s.get('document','') + ' ' + s.get('section','') for s in result.get('sources',[])])
    return expected_doc.lower().split(';')[0].lower() in hay.lower() or any(x.strip().lower() in hay.lower() for x in expected_doc.split(';'))


def main():
    rows = list(csv.DictReader(INPUT.open(encoding='utf-8')))
    results=[]; scores=[]
    for row in rows:
        t=time.perf_counter()
        try:
            r=requests.post(API,json={'question':row['question'],'top_k':5,'rerank':True},timeout=180)
            data=r.json(); err='' if r.ok else data.get('detail','request failed')
        except Exception as e:
            data={'answer':'','sources':[],'retrieved_chunks':[],'answerable':False}; err=str(e)
        latency=round((time.perf_counter()-t)*1000,1)
        sources=data.get('sources',[])
        hit=expected_hit(row['expected_document'],row['expected_section'],data)
        ranks=[]
        for i,s in enumerate(sources,1):
            if row['expected_document']!='NONE' and any(d.strip().lower() in s.get('document','').lower() for d in row['expected_document'].split(';')):
                ranks.append(i)
        rr=1/ranks[0] if ranks else 0
        unanswerable_ok = row['type']=='unanswerable' and not data.get('answerable',False)
        results.append({**row,'answer':data.get('answer',''),'answerable':data.get('answerable',False),'sources_json':json.dumps(sources),'retrieved_chunks_json':json.dumps(data.get('retrieved_chunks',[])),'latency_ms':latency,'error':err})
        scores.append({**row,'hit_at_5':int(hit),'mrr':rr,'unanswerable_correct':int(unanswerable_ok) if row['type']=='unanswerable' else '','citation_count':len(sources),'latency_ms':latency,'error':err})
    with RESULTS.open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=results[0].keys()); w.writeheader(); w.writerows(results)
    with SCORES.open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=scores[0].keys()); w.writeheader(); w.writerows(scores)
    print(f'Wrote {RESULTS}')
    print(f'Wrote {SCORES}')
    print(f'Retrieval hit@5: {sum(x["hit_at_5"] for x in scores)/len(scores):.3f}')
    print(f'MRR: {sum(x["mrr"] for x in scores)/len(scores):.3f}')

if __name__=='__main__': main()
