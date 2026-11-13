import os
import unittest

from _load import load

fe = load(os.path.join(".claude", "skills", "fonzi-edit"), "fonzi_edit")

# the clip changes in the first raw file this was built on (244 s, twelve lifts)
CUTS = [24, 37.1, 37.2, 37.5, 37.6, 41.6, 41.7, 41.8, 44.8, 68.77, 103.43, 119,
        139.33, 161.2, 184.33, 205.3, 222.9, 223.3, 230.2, 242.03]


class Plan(unittest.TestCase):
    def test_drive_links(self):
        fid = "1f6cZwaAuBrGV1Lg2SZUc1X8ZNnJu_i-Q"
        self.assertEqual(fe.drive_id("https://drive.google.com/file/d/%s/view?usp=drivesdk" % fid), fid)
        self.assertEqual(fe.drive_id("https://drive.google.com/uc?export=download&id=%s" % fid), fid)
        self.assertIsNone(fe.drive_id("/videos/raw.mp4"))

    def test_setup_clips_are_dropped(self):
        clips = fe.clips_from_cuts(CUTS, 244.07)
        self.assertEqual(len(clips), 12)
        self.assertTrue(all(b - a >= fe.MIN_CLIP for a, b in clips))
        self.assertFalse(any(37 < a < 44 for a, b in clips))

    def test_plan_hits_the_length_in_order(self):
        segs = fe.plan(CUTS, 244.07, 90)
        self.assertEqual(len(segs), 12)
        self.assertAlmostEqual(sum(b - a for a, b in segs), 90, delta=0.02)
        self.assertEqual(segs, sorted(segs))
        clips = fe.clips_from_cuts(CUTS, 244.07)
        for (a, b), (ca, cb) in zip(segs, clips):
            self.assertGreaterEqual(a, ca + fe.MARGIN - 0.04)
            self.assertLessEqual(b, cb - fe.MARGIN + 0.04)

    def test_short_clips_give_all_they_have(self):
        self.assertEqual(fe.allot([2, 10, 10], 12), [2, 5, 5])
        self.assertEqual(fe.allot([3, 4], 90), [3, 4])

    def test_one_take_and_short_sources(self):
        (a, b), = fe.plan([], 200, 90)
        self.assertAlmostEqual(b - a, 90, delta=0.05)
        (a, b), = fe.plan([], 20, 90)
        self.assertAlmostEqual(b - a, 19, delta=0.05)

    def test_too_many_clips_keeps_the_longest(self):
        cuts = [i * 6 for i in range(1, 20)]
        segs = fe.plan(cuts, 120, 10)
        self.assertEqual(len(segs), 5)
        self.assertAlmostEqual(sum(b - a for a, b in segs), 10, delta=0.2)

    def test_segments_and_filter(self):
        segs = fe.parse_segments("4-12, 30-36.5")
        self.assertEqual(segs, [(4.0, 12.0), (30.0, 36.5)])
        with self.assertRaises(ValueError):
            fe.parse_segments("12-4")
        graph = fe.filtergraph(segs)
        self.assertIn("concat=n=2:v=1:a=1", graph)
        self.assertIn("loudnorm", graph)


if __name__ == "__main__":
    unittest.main()
