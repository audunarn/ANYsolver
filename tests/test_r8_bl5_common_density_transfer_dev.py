"""Small guards for saved-state BL5 density layout and admission."""

import importlib.util
from pathlib import Path
import copy
import unittest


SOURCE = Path(__file__).resolve().parents[1] / "scripts/r8_bl5_common_density_transfer_dev.py"
SPEC = importlib.util.spec_from_file_location("r8_bl5_common_density_transfer_dev", SOURCE)
TRANSFER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(TRANSFER)


class DensityLayoutTests(unittest.TestCase):
    def test_support_major_to_channel_major_signs_and_inverse(self):
        mu = [1., 2., 3., 4., 5., 11., 12., 13., 14., 15.]
        self.assertEqual(TRANSFER.map_external_to_native(mu, 2),
                         [-1., -11., -2., -12., -3., -13., -5., -15., 4., 14.])
        self.assertEqual(TRANSFER.map_native_to_external(
            TRANSFER.map_external_to_native(mu, 2), 2), mu)

    def test_short_density_rejected(self):
        with self.assertRaises(ValueError):
            TRANSFER.map_external_to_native([1.] * 9, 2)
        with self.assertRaises(ValueError):
            TRANSFER.map_native_to_external([1.] * 9, 2)


class StationAdmissionTests(unittest.TestCase):
    def setUp(self):
        self.stations = [{"sample_index": i, "multiplier_rows": [0, 1, 2, 3, 4],
                          "shell_reference_m": [[0., 0., 0.], [.125, 0., 0.]],
                          "shell_alpha": (i + .5) / 8., "measure_m": .125 / 8.}
                         for i in range(8)]

    def test_complete_support_is_admitted(self):
        TRANSFER._admit_native_stations(self.stations, [0., .125], 1)

    def test_missing_duplicate_shifted_and_wrong_measure_refused(self):
        variants = []
        variants.append(self.stations[:-1])
        duplicate_index = copy.deepcopy(self.stations)
        duplicate_index[1]["sample_index"] = 0
        variants.append(duplicate_index)
        duplicate_location = copy.deepcopy(self.stations)
        duplicate_location[1]["shell_alpha"] = duplicate_location[0]["shell_alpha"]
        variants.append(duplicate_location)
        shifted = copy.deepcopy(self.stations)
        shifted[0]["shell_reference_m"] = [[.1, 0., 0.], [.225, 0., 0.]]
        variants.append(shifted)
        wrong_measure = copy.deepcopy(self.stations)
        wrong_measure[0]["measure_m"] += .001
        variants.append(wrong_measure)
        wrong_row = copy.deepcopy(self.stations)
        wrong_row[0]["multiplier_rows"][4] = 0
        variants.append(wrong_row)
        for stations in variants:
            with self.subTest(stations=stations):
                with self.assertRaises(ValueError):
                    TRANSFER._admit_native_stations(stations, [0., .125], 1)


if __name__ == "__main__":
    unittest.main()
