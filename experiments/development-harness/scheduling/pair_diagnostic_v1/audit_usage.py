"""Read-only lower-bound usage audit; gaps never become zero-cost responses."""
import argparse
import hashlib
import json
from pathlib import Path

FIELDS=('input_tokens','cached_input_tokens','output_tokens','cache_write_input_tokens','reasoning_output_tokens','total_tokens')


def audit(folder):
    threads=[];sources={}
    for path in sorted(folder.rglob('*.jsonl')):
        data=path.read_bytes();sources[str(path.relative_to(folder))]=hashlib.sha256(data).hexdigest()
        rows=[json.loads(line) for line in data.splitlines()]
        meta=rows[0]['payload'];tid=meta['id'];known={k:0 for k in FIELDS}
        seen=set();gaps=[];fresh=0;pending=False;owned=True;complete=[];aborted=[]
        for i,row in enumerate(rows[1:],1):
            p=row['payload'];kind=row['type']
            if kind=='session_meta':owned=p['id']==tid;continue
            if kind=='event_msg' and p.get('type')=='thread_settings_applied' and p.get('thread_id')==tid:
                owned=True;continue
            if not owned:continue
            if kind=='response_item' and (p.get('type') in ('reasoning','function_call','custom_tool_call')
                    or p.get('type')=='message' and p.get('role')=='assistant'):pending=True
            if kind=='token_usage_record':
                if p['thread_id']!=tid or p['response_id'] in seen:raise ValueError('foreign or duplicate usage record')
                amount=p['usage']
                if any(type(amount.get(k)) is not int or amount[k]<0 for k in FIELDS):raise ValueError('invalid usage')
                if amount['total_tokens']!=amount['input_tokens']+amount['output_tokens']:raise ValueError('inconsistent usage')
                seen.add(p['response_id'])
                for k in FIELDS:known[k]+=amount[k]
                if known!=p['thread_token_usage']:raise ValueError('cumulative mismatch')
                fresh+=1;pending=False
            elif kind=='compacted':
                if p.get('compaction_response_id') not in seen:raise ValueError('compaction usage missing')
            elif kind=='event_msg':
                event=p.get('type')
                if event=='token_count':
                    info=p.get('info')
                    if fresh!=1 and (pending or not info or info['total_token_usage']!=known):
                        following=rows[i+1]['type'] if i+1<len(rows) else None
                        gaps.append({'ordinal':row.get('ordinal',i),'unaccounted_model_output':pending,
                                     'next_record_type':following})
                    fresh=0
                elif event=='task_complete':complete.append(p['turn_id'])
                elif event=='turn_aborted':aborted.append(p.get('turn_id'))
        threads.append({'thread_id':tid,'parent_thread_id':meta.get('parent_thread_id'),
                        'known_response_records':len(seen),'known_usage':known,'observation_gaps':gaps,
                        'completed_turns':complete,'aborted_turns':aborted})
    gaps=sum(len(t['observation_gaps']) for t in threads)
    return {'status':'partial' if gaps else 'recorded','billing_completeness':'unknown',
            'scope':'response records only; excludes any unreported interrupted consumption',
            'threads':threads,'known_usage':{k:sum(t['known_usage'][k] for t in threads) for k in FIELDS},
            'known_response_records':sum(t['known_response_records'] for t in threads),
            'observation_gaps':gaps,'source_sha256':sources}


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--sessions',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();value=audit(a.sessions)
    with a.output.open('x') as f:json.dump(value,f,indent=2);f.write('\n')
