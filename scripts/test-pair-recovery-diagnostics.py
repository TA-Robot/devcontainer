import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

HERE=Path(__file__).resolve().parents[1]/'experiments/development-harness/scheduling/pair_diagnostic_v1'
spec=importlib.util.spec_from_file_location('usage_recovery_audit',HERE/'audit_usage.py')
audit=importlib.util.module_from_spec(spec);spec.loader.exec_module(audit)


def row(kind,**payload):return {'type':kind,'payload':payload}


class RecoveryTests(unittest.TestCase):
    def test_known_responses_after_gap_are_retained_without_admitting_cost(self):
        one=dict(input_tokens=20,cached_input_tokens=7,output_tokens=5,cache_write_input_tokens=0,
                 reasoning_output_tokens=0,total_tokens=25)
        two={k:v*2 for k,v in one.items()}
        rows=[row('session_meta',id='root',parent_thread_id=None),
              row('token_usage_record',thread_id='root',response_id='r1',usage=one,thread_token_usage=one),
              row('event_msg',type='token_count',info={'total_token_usage':one}),
              row('response_item',type='message',role='assistant',content='PRIVATE_PARTIAL'),
              row('event_msg',type='token_count',info={'total_token_usage':one}),
              row('inter_agent_communication_metadata',trigger_turn=False),
              row('token_usage_record',thread_id='root',response_id='r2',usage=one,thread_token_usage=two),
              row('event_msg',type='token_count',info={'total_token_usage':two}),
              row('event_msg',type='task_complete',turn_id='t')]
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);(p/'root.jsonl').write_text('\n'.join(json.dumps(r) for r in rows)+'\n')
            result=audit.audit(p)
            self.assertEqual(result['known_usage'],two)
            self.assertEqual(result['known_response_records'],2)
            self.assertEqual(result['status'],'partial')
            self.assertEqual(result['billing_completeness'],'unknown')
            self.assertEqual(result['observation_gaps'],1)
            self.assertNotIn('PRIVATE_PARTIAL',json.dumps(result))
            rows.insert(-1,rows[6])
            (p/'root.jsonl').write_text('\n'.join(json.dumps(r) for r in rows)+'\n')
            with self.assertRaises(ValueError):audit.audit(p)

    def test_unchanged_counter_is_not_a_second_response(self):
        amount=dict(input_tokens=20,cached_input_tokens=7,output_tokens=5,cache_write_input_tokens=0,
                    reasoning_output_tokens=0,total_tokens=25)
        rows=[row('session_meta',id='root',parent_thread_id=None),
              row('token_usage_record',thread_id='root',response_id='r1',usage=amount,thread_token_usage=amount),
              row('event_msg',type='token_count',info={'total_token_usage':amount}),
              row('event_msg',type='token_count',info={'total_token_usage':amount})]
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);(p/'root.jsonl').write_text('\n'.join(json.dumps(r) for r in rows)+'\n')
            result=audit.audit(p)
            self.assertEqual(result['known_response_records'],1)
            self.assertEqual(result['observation_gaps'],0)
            self.assertEqual(result['billing_completeness'],'unknown')


if __name__=='__main__':unittest.main()
