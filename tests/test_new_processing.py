import unittest
import os
from appia.processors import hplc, fplc
from appia.parsers import process_parser


appia_dir = os.path.split(
    os.path.dirname(os.path.realpath(__file__))
)[0]

class FakeArgs(object):
    def __init__(self, arg_dict):
        for key, val in arg_dict.items():
            setattr(self, key, val)

    def __getattr__(self, attr):
        return None

class TestProcessing(unittest.TestCase):

    def test_waters_processing(self):
        waters_file = os.path.join(
            appia_dir, 'test-files', 'results1844.arw'
        )

        results = hplc.WatersProcessor(waters_file, hplc_flow_rate = 0.5)
        self.assertEqual(results.manufacturer, 'Waters')
        self.assertEqual(results.flow_rate, 0.5)
        self.assertEqual(results.sample_name, 'SEC_08')
        self.assertEqual(results.channel, 'ex280/em350')
        self.assertEqual(results.method, 'Sup6Inc_10_300_TrpGFP_LineA')

        df = results.df
        self.assertEqual(df.shape[0], 13202)
        self.assertEqual(df.shape[1], 6)
        self.assertEqual(df['Sample'][0], 'SEC_08')
        self.assertAlmostEqual(sum(df['Value']), 638.5193493218148)

        channels = set(df.Channel)
        self.assertEqual(channels, {'ex280/em350'})

        norm = df.loc[df['Normalization'] == 'Normalized']
        self.assertEqual(min(norm.Value), 0)
        self.assertEqual(max(norm.Value), 1)


    def test_old_shim_processing(self):
        shim_file = os.path.join(
            appia_dir, 'test-files', '05_25_BB.asc'
        )

        results = hplc.OldShimProcessor(
            shim_file,
            hplc_flow_rate = 0.5,
            channel_mapping = {'A': 'Trp', 'B': 'GFP'}
        )

        df = results.df
        self.assertEqual(df.shape[0], 24004)
        self.assertEqual(df.shape[1], 6)
        self.assertEqual(df.Sample[0], '05_25_BB')
        self.assertAlmostEqual(sum(df['Value']), 51986033.02903766)

        channels = set(df.Channel)
        self.assertEqual(channels, {'Trp', 'GFP'})

        norm = df.loc[df['Normalization'] == 'Normalized']
        self.assertEqual(min(norm.Value), 0)
        self.assertEqual(max(norm.Value), 1)

    def test_new_shim(self):
        shim_file = os.path.join(
            appia_dir, 'test-files', 'new-shim-1.txt'
        )
        results = hplc.NewShimProcessor(
            shim_file,
            hplc_flow_rate = 0.5
        )

        df = results.df
        self.assertEqual(df.shape, (14406, 6))
        self.assertEqual(df.Sample[0], 'Tommy-S-1-031022')
        self.assertAlmostEqual(sum(df.Value), 507623541.7662889)

        channels = set(df.Channel)
        self.assertEqual(channels, {'UV', 'Ex:280/Em:330', 'Ex:494/Em:520'})

        norm = df.loc[df['Normalization'] == 'Normalized']
        self.assertEqual(min(norm.Value), 0)
        self.assertEqual(max(norm.Value), 1)

    def test_agilent(self):
        ag_file = os.path.join(
            appia_dir, 'test-files', 'NAI-A594_0H_RT_Channel540_Flow1.0.CSV'
        )

        results = hplc.AgilentProcessor(
            ag_file,
            hplc_flow_rate = 0.5,
            agilent_channel_name = 'test-channel'
        )
        self.assertEqual(results.channel, 'test-channel')
        self.assertEqual(results.flow_rate, 0.5)

        results = hplc.AgilentProcessor(ag_file)
        self.assertEqual(results.channel, '540')
        self.assertEqual(results.flow_rate, 1.0)

        df = results.df
        self.assertEqual(df.shape, (52800, 6))
        self.assertEqual(df.Sample[0], 'NAI-A594_0H_RT')
        self.assertAlmostEqual(sum(df.Value), 37860.58000314166)

        channels = set(df.Channel)
        self.assertEqual(channels, {'540'})

        norm = df.loc[df['Normalization'] == 'Normalized']
        self.assertEqual(min(norm.Value), 0)
        self.assertEqual(max(norm.Value), 1)

    def test_akta(self):
        akta_file = os.path.join(
            appia_dir, 'test-files', '2018_0821SEC_detergentENaC.csv'
        )

        results = fplc.AktaProcessor(
            akta_file,
            fplc_cv = 24
        )
        df = results.df

        self.assertEqual(df.shape, (87002, 7))
        self.assertEqual(df.Sample[0], '2018_0821SEC_detergentENaC')
        self.assertAlmostEqual(sum(df.Value), 1062056.7151461844)
        self.assertEqual(set(df.Channel), {'mS/cm', 'mAU', '%'})
        
        norm = df.loc[df['Normalization'] == 'Normalized']
        self.assertEqual(min(norm.Value), 0)
        self.assertEqual(max(norm.Value), 1)

if __name__ == '__main__':
    unittest.main()