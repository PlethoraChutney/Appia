import unittest
import os
import appia
from appia.processors import hplc

class TestProcessing(unittest.TestCase):
    def test_find_files(self):
        appia_dir = os.path.split(
            os.path.dirname(os.path.realpath(__file__))
        )[0]

        test_files_glob = os.path.join(
            appia_dir, 'test-files', '*'
        )
        found_files = appia.processors.core.get_files(test_files_glob)

        self.assertEqual(len(found_files['waters']), 27)
        self.assertEqual(len(found_files['shimadzu']), 7)
        self.assertEqual(len(found_files['agilent']), 3)
        self.assertEqual(len(found_files['akta']), 1)

    def test_waters_processing(self):
        appia_dir = os.path.split(
            os.path.dirname(os.path.realpath(__file__))
        )[0]

        waters_file = os.path.join(
            appia_dir, 'test-files', 'results1844.arw'
        )

        results = hplc.append_waters([waters_file], flow_rate=0.5)[0]
        self.assertEqual(results.shape[0], 13202)
        self.assertEqual(results.shape[1], 6)
        self.assertEqual(results['Sample'][0], 'SEC_08')
        self.assertAlmostEqual(sum(results['Value']), 638.5193493218148)
        self.assertTrue(all(results.columns == ['mL', 'Sample', 'Channel', 'Time', 'Normalization', 'Value']))
        
        channels = set(results.Channel)
        self.assertEqual(len(channels), 1)
        self.assertEqual(channels.pop(), 'ex280/em350')

        norm = results.loc[results['Normalization'] == 'Normalized']
        self.assertEqual(min(norm.Value), 0)
        self.assertEqual(max(norm.Value), 1)

if __name__ == '__main__':
    unittest.main()