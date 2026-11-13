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
        self.assertIn("drawtext", fe.filtergraph(segs, labels=["BENCH", ""]))

    def test_transitions(self):
        joins = fe.join_plan(4, ["fade", "cut", "dissolve"], 0.3)
        self.assertEqual([j[0] for j in joins], ["fade", "fade", "dissolve"])
        self.assertAlmostEqual(joins[1][1], 1 / 30.0)
        self.assertEqual(len(fe.join_plan(4, ["fade"], 0.3)), 3)
        with self.assertRaises(ValueError):
            fe.join_plan(3, ["spin"], 0.3)
        graph = fe.filtergraph_joined([(0, 8), (10, 16), (20, 29)], fe.join_plan(3, ["fade"], 0.3))
        self.assertIn("xfade=transition=fade:duration=0.300:offset=8.000", graph)
        self.assertIn("offset=14.000", graph)
        self.assertIn("acrossfade", graph)


class Recipe(unittest.TestCase):
    def setUp(self):
        import json, sys
        d = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                         ".claude", "skills", "fonzi-edit")
        if d not in sys.path:
            sys.path.insert(0, d)
        import fonzi_recipe
        self.rc = fonzi_recipe
        with open(os.path.join(d, "recipe.example.json")) as fh:
            self.recipe = json.load(fh)

    def test_timeline_is_ninety_seconds_with_eight_exercises(self):
        total, groups = self.rc.timeline(self.recipe)
        self.assertAlmostEqual(total, 90.0, delta=0.01)
        self.assertEqual(len(groups), 8)
        self.assertEqual([g["index"] for g in groups], list(range(1, 9)))

    def test_slow_clip_counts_double(self):
        self.assertEqual(self.rc.out_len({"start": 10, "end": 14, "speed": 0.5}), 8)

    def test_join_graph_has_every_join_and_cutaway(self):
        self.rc.timeline(self.recipe)
        n = len(self.recipe["clips"])
        g = self.rc.join_graph(self.recipe, n, True)
        self.assertEqual(g.count("xfade="), n - 1)
        self.assertEqual(g.count("overlay="), len(self.recipe["broll"]))
        self.assertIn("loudnorm", g)

    def test_overlay_plan_ties_callouts_to_clip_time(self):
        total, groups = self.rc.timeline(self.recipe)
        plan = self.rc.overlay_plan(self.recipe, total, groups)
        self.assertEqual(len(plan["callouts"]), 4)
        first = self.recipe["clips"][0]
        self.assertAlmostEqual(plan["callouts"][0]["abs_at"], first["_start"] + first["callouts"][0]["at"])
        self.assertTrue(all(0 <= c["anchor"][0] <= 1 and 0 <= c["anchor"][1] <= 1 for c in plan["callouts"]))


if __name__ == "__main__":
    unittest.main()
