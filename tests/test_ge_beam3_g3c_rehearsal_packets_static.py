"""Synthetic byte and manifest guards; not numerical evidence."""
from pathlib import Path
from hashlib import sha256
import copy
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'tests')]
import ge_beam3_g3c_rehearsal_packets as a
import test_ge_beam3_g3c_rehearsal_mutations_static as fake


class PacketTests(unittest.TestCase):
    def test_exclusive_containment_and_hashes(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d); raw=b'raw diagnostic\n'; a.exclusive(root/'x',raw)
            self.assertEqual(a.read_bound(root,'x',a.fingerprint(raw)),raw)
            with self.assertRaises(FileExistsError): a.exclusive(root/'x',raw)
            for name in ('../x','a/x','C:x','..'):
                with self.assertRaises(ValueError): a.contained(root,name)
            with self.assertRaises(ValueError): a.read_bound(root,'x',dict(bytes=len(raw),sha256='0'*64))

    def test_exact_manifest_schema_inventory_and_types(self):
        rows=[dict(case_id='case',prefix=i,name=f'prefix-{i:03d}.json',bytes=1,sha256='1'*64) for i in range(3)]
        value=a.manifest('2'*64,'case',2,'3'*64,rows)
        for key,bad in [('bytes',True),('prefix',1.0),('name','../escape'),('sha256','A'*64)]:
            v=copy.deepcopy(value); v['packets'][1][key]=bad
            with self.assertRaises(ValueError): a.validate_manifest(v,'2'*64,'case',2,'3'*64)
        v=copy.deepcopy(value); v['packets'].pop()
        with self.assertRaises(ValueError): a.validate_manifest(v,'2'*64,'case',2,'3'*64)

    def test_wrong_command_scale_rejected(self):
        raw=fake.fake_origin('J_B2_PAIR','NONE',.01,2)
        a.verify_commands(raw,'J_B2_PAIR::BASE::S0::NONE',2)
        value=a.p.strict(raw)
        for entry in value['history']: entry['command']['force_scale']=1.
        wrong=a.p.canonical(fake.m.repair(value))
        with self.assertRaises(ValueError): a.verify_commands(wrong,'J_B2_PAIR::BASE::S0::NONE',2)
        with self.assertRaises(ValueError): a.verify_commands(raw,'J_B2_PAIR::BASE::S0::NONE',True)


if __name__=='__main__': unittest.main()
