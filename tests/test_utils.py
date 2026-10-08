# -*- coding: utf-8 -*-
"""Deterministic unit tests for the pure-Numpy helpers used by training.

These tests cover ``utils/assets.py`` and ``utils/vscp.py``, the two modules
that carry real logic without pulling in torch, mmcv or mmseg. They run in
CI on a stock runner: no GPU, no dataset, no network, no wall-clock input.
"""

import sys
import unittest
from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from utils import assets, vscp  # noqa: E402  (path bootstrap must run first)


class MadosAssetMappingsTest(unittest.TestCase):
    """The class/band tables in ``utils/assets.py`` define the label space."""

    def test_mados_cat_mapping_covers_all_fifteen_classes_in_label_order(self):
        self.assertEqual(list(assets.mados_cat_mapping.keys()), assets.labels)
        self.assertEqual(list(assets.mados_cat_mapping.values()), list(range(1, 16)))

    def test_mados_color_mapping_covers_every_label(self):
        self.assertEqual(sorted(assets.mados_color_mapping.keys()), sorted(assets.labels))
        self.assertEqual(len(assets.mados_color_mapping), 15)
        for label, colour in assets.mados_color_mapping.items():
            self.assertIsInstance(colour, str, label)
            self.assertTrue(colour, label)

    def test_s2_mapping_maps_the_eleven_reflectance_bands_in_order(self):
        bands = [
            'nm440', 'nm490', 'nm560', 'nm665', 'nm705', 'nm740',
            'nm783', 'nm842', 'nm865', 'nm1600', 'nm2200',
        ]
        self.assertEqual([assets.s2_mapping[band] for band in bands], list(range(11)))
        self.assertEqual(assets.s2_mapping['Class'], 11)

    def test_cat_map_rejects_unknown_labels(self):
        with self.assertRaises(KeyError):
            assets.cat_map('Not A MADOS Class')


class BoolFlagTest(unittest.TestCase):
    """``bool_flag`` parses the ``--vscp``/``--model_ema`` style CLI flags."""

    def test_bool_flag_parses_truthy_strings_as_true(self):
        for value in ('true', 'True', 'on', '1'):
            self.assertIs(assets.bool_flag(value), True, value)

    def test_bool_flag_parses_falsy_strings_as_false(self):
        for value in ('false', 'False', 'off', '0'):
            self.assertIs(assets.bool_flag(value), False, value)


class CosineSchedulerTest(unittest.TestCase):
    """``cosine_scheduler`` drives the warm-up/decay schedules in training."""

    def test_cosine_scheduler_constant_schedule_stays_constant(self):
        schedule = assets.cosine_scheduler(0.999, 0.999, 4, 10)
        self.assertEqual(len(schedule), 40)
        np.testing.assert_allclose(schedule, 0.999)

    def test_cosine_scheduler_returns_one_value_per_iteration(self):
        schedule = assets.cosine_scheduler(1e-4, 1e-6, 80, 137)
        self.assertEqual(len(schedule), 80 * 137)

    def test_cosine_scheduler_warmup_reaches_base_then_decays_monotonically(self):
        schedule = assets.cosine_scheduler(
            base_value=1.0,
            final_value=0.0,
            epochs=5,
            niter_per_ep=4,
            warmup_epochs=1,
            start_warmup_value=0.0,
        )
        self.assertEqual(len(schedule), 20)
        self.assertEqual(schedule[0], 0.0)
        self.assertAlmostEqual(schedule[3], 1.0, places=12)
        self.assertTrue(np.all(np.diff(schedule[3:]) <= 1e-12))
        self.assertLess(schedule[-1], 0.01)


class VscpAugmentationTest(unittest.TestCase):
    """``VSCP`` pastes only the labelled pixels of the partner sample."""

    def _build_batch(self):
        # Two base samples (0, 1) and their partners (2, 3).
        image = np.full((4, 1, 2, 2), 0.0, dtype=np.float32)
        target = np.full((4, 2, 2), -1, dtype=np.int64)
        image[0] = 1.0
        image[1] = 2.0
        image[2] = 9.0
        image[3] = 7.0
        target[2] = np.array([[0, -1], [1, -1]])
        target[3] = np.array([[2, -1], [-1, 3]])
        return image, target

    def test_vscp_pastes_only_labelled_partner_pixels(self):
        image, target = self._build_batch()
        augmented_image, augmented_target = vscp.VSCP(image, target)

        self.assertEqual(augmented_image.shape, (2, 1, 2, 2))
        self.assertEqual(augmented_target.shape, (2, 2, 2))

        np.testing.assert_array_equal(augmented_image[0, 0], np.array([[9.0, 1.0], [9.0, 1.0]]))
        np.testing.assert_array_equal(augmented_target[0], np.array([[0, -1], [1, -1]]))

        np.testing.assert_array_equal(augmented_image[1, 0], np.array([[7.0, 2.0], [2.0, 7.0]]))
        np.testing.assert_array_equal(augmented_target[1], np.array([[2, -1], [-1, 3]]))

    def test_vscp_leaves_inputs_untouched(self):
        image, target = self._build_batch()
        image_before = image.copy()
        target_before = target.copy()

        vscp.VSCP(image, target)

        np.testing.assert_array_equal(image, image_before)
        np.testing.assert_array_equal(target, target_before)

    def test_vscp_ignores_partner_without_annotations(self):
        image = np.zeros((2, 1, 2, 2), dtype=np.float32)
        image[0] = 5.0
        image[1] = 8.0
        target = np.full((2, 2, 2), -1, dtype=np.int64)

        augmented_image, augmented_target = vscp.VSCP(image, target)

        self.assertEqual(augmented_image.shape, (1, 1, 2, 2))
        np.testing.assert_array_equal(augmented_image[0, 0], np.full((2, 2), 5.0, dtype=np.float32))
        np.testing.assert_array_equal(augmented_target[0], np.full((2, 2), -1))


if __name__ == '__main__':
    unittest.main()
