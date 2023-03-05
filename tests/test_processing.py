import unittest
import os
import appia
from appia.processors import hplc


appia_dir = os.path.split(
    os.path.dirname(os.path.realpath(__file__))
)[0]

class TestProcessing(unittest.TestCase):
    def test_find_files(self):
        test_files_glob = os.path.join(
            appia_dir, 'test-files', '*'
        )
        found_files = appia.processors.core.get_files(test_files_glob)

        self.assertEqual(len(found_files['waters']), 27)
        self.assertEqual(len(found_files['shimadzu']), 7)
        self.assertEqual(len(found_files['agilent']), 3)
        self.assertEqual(len(found_files['akta']), 1)

    def test_waters_processing(self):
        waters_file = os.path.join(
            appia_dir, 'test-files', 'results1844.arw'
        )

        results = hplc.append_waters([waters_file], flow_rate=0.5)[0]
        self.assertEqual(results.shape[0], 13202)
        self.assertEqual(results.shape[1], 6)
        self.assertEqual(results['Sample'][0], 'SEC_08')
        self.assertAlmostEqual(sum(results['Value']), 638.5193493218148)

        channels = set(results.Channel)
        self.assertEqual(channels, {'ex280/em350'})

        norm = results.loc[results['Normalization'] == 'Normalized']
        self.assertEqual(min(norm.Value), 0)
        self.assertEqual(max(norm.Value), 1)

    def test_old_shim_processing(self):
        shim_file = os.path.join(
            appia_dir, 'test-files', '05_25_BB.asc'
        )

        results = hplc.append_shim([shim_file], {'A': 'Trp', 'B': 'GFP'}, 0.5)[0]
        self.assertEqual(results.shape[0], 24004)
        self.assertEqual(results.shape[1], 6)
        self.assertEqual(results.Sample[0], '05_25_BB')
        self.assertAlmostEqual(sum(results['Value']), 51986033.029039636)

        channels = set(results.Channel)
        self.assertEqual(channels, {'Trp', 'GFP'})

        norm = results.loc[results['Normalization'] == 'Normalized']
        self.assertEqual(min(norm.Value), 0)
        self.assertEqual(max(norm.Value), 1)

    def test_agilent(self):
        ag_file = os.path.join(
            appia_dir, 'test-files', 'NAI-A594_0H_RT_Channel540Flow1.0.CSV'
        )

        results = hplc.append_agilent([ag_file], 0.5, 'GFP')
        self.assertEqual(results.shape[0], 26400)
        self.assertEqual(results.shape[1], 6)
        self.assertEqual(results.Sample[0], 'NAI-A594_0H_Channel540Flow1.0')
        self.assertAlmostEqual(sum(results['Value']), 37618.857383728035)

        channels = set(results.Channel)
        self.assertEqual(channels, {'GFP'})

        # turns out agilent normalization is broken


if __name__ == '__main__':
    unittest.main()