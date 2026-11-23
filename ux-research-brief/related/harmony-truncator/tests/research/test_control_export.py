import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import shutil

from truncator.common.storage import read, save, digest
from research.controls.evidence import evidence_identity, validate_interaction
from research.controls.export import export_control_group, interaction_files


class PortableActionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.source = self.root / 'source'
        self.out = self.root / 'export'
        self.action = {'kind':'swipe','selector':{'id':'view'},'from':[.8,.5],'to':[.2,.5]}
        session = {'status':'verified','process':{'pid':12,'start_ticks':100}}
        for name in ('initial','after'):
            folder = self.source / name
            folder.mkdir(parents=True)
            (folder/'snapshot.jpeg').write_bytes(b'image')
            for tree in ('tree-before.json','tree-after.json'): save(folder/tree,{})
            save(folder/'capture.json',{'screenshot_sha256':digest(b'image'), 'hap_sha256':'hap',
                'session':session,'recipe':{'actions':[self.action] if name=='after' else []}})
        previous = evidence_identity(self.source/'initial')
        record = read(self.source/'after/capture.json')
        record['continued_from'] = {'capture':previous['capture'],'capture_sha256':previous['sha256']['capture.json']}
        save(self.source/'after/capture.json',record)
        attrs = {'id':'view','bounds':'[0,0][100,100]'}
        save(self.source/'after/action-before-000.json',{'attributes':attrs})
        save(self.source/'after/replay.json',[{'index':0,'phase':'route','action':self.action,
            'status':'dispatched','location_wait':{'ready':True},'matches':[attrs],
            'arguments':['swipe','80','50','20','50','600']}])
        self.group = {'id':'group','direction':{'axis':'horizontal'},
            'states':[{'state':'scroll',**previous}], 'interactions':[
                {**evidence_identity(self.source/'after'),'state':'scroll','before':previous,'actions':[self.action]}]}
        shutil.copytree(self.source/'initial', self.out/'initial')

    def export(self):
        export_control_group(self.group,self.out,{(self.source/'initial').resolve():'initial'})
        return read(self.out/'control-group.json')['interactions'][0]

    def test_portable_dispatch_verifies_without_reading_original_paths(self):
        action = self.export()
        original_open = Path.open
        def local_only(path, *args, **kwargs):
            self.assertFalse(path.resolve().is_relative_to(self.source.resolve()))
            return original_open(path,*args,**kwargs)
        with patch.object(Path,'open',local_only):
            validate_interaction(action,root=self.out)
        self.assertIn('replay.json',action['evidence_files'])
        self.assertIn('action-before-000.json',action['evidence_files'])

    def test_changed_replay_coordinates_fail_after_export(self):
        action = self.export()
        file = self.out/action['capture']/'replay.json'
        replay = read(file); replay[0]['arguments'][1]='1'; save(file,replay)
        with self.assertRaisesRegex(ValueError,'coordinates'):
            validate_interaction(action,root=self.out)

    def test_portable_reference_cannot_escape_package(self):
        action = self.export();action['before']['capture']='../source/initial'
        with self.assertRaisesRegex(ValueError,'escapes'):
            validate_interaction(action,root=self.out)

    def test_checkpoint_evidence_is_part_of_required_inventory(self):
        files=interaction_files({'setup_actions':[self.action],'actions':[{**self.action,'checks':[{'equals':'done'}]}]}, Path('uncreated-capture'))
        self.assertIn('action-before-000.json',files)
        self.assertIn('action-before-001.json',files)
        self.assertIn('action-after-001.json',files)
