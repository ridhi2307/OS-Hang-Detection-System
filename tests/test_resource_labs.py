import unittest

from backend.resource_labs import allocation, cpu, disk


class ResourceLabs(unittest.TestCase):
    def test_rr_arrival_at_boundary_precedes_requeued_job(self):
        runs = cpu(dict(arrivals="1 3", bursts="4 1", quantum="2"))["runs"]
        self.assertEqual(runs[2]["steps"], [[0, 1, "Idle", "No process ready"],
                         [1, 3, "P1", "Quantum expired"], [3, 4, "P2", "Completed"],
                         [4, 6, "P1", "Completed"]])
        self.assertEqual(runs[2]["metrics"], [0.5, 3, 0])

    def test_shortest_job_respects_arrivals(self):
        runs = cpu(dict(arrivals="0 0 1", bursts="6 2 1", quantum="1"))["runs"]
        self.assertEqual([step[2] for step in runs[1]["steps"]], ["P2", "P3", "P1"])
        self.assertEqual(runs[1]["metrics"][0], 1.33)

    def test_disk_reference_and_duplicates(self):
        runs = disk(dict(requests="98 183 37 122 14 124 65 67", head="53"))["runs"]
        self.assertEqual([run["metrics"][0] for run in runs], [640, 236, 299, 331, 382, 322])
        self.assertEqual(disk(dict(requests="40 40", head="40"))["runs"][2]["metrics"], [0, 0])

    def test_fragmentation(self):
        runs = allocation(dict(holes="100 500 200 300 600", requests="212 417 112 426"))["runs"]
        self.assertEqual([r["metrics"][0] for r in runs], [3, 4, 3])
        self.assertEqual(runs[0]["steps"][-1][1], "Fragmented free space")

    def test_invalid_workloads(self):
        for fn, args in [(cpu, dict(arrivals="1", bursts="1 2", quantum="1")),
                         (cpu, dict(arrivals="0", bursts="1", quantum="0")),
                         (disk, dict(head="200", requests="2")),
                         (allocation, dict(holes="-1", requests="1"))]:
            with self.subTest(fn=fn), self.assertRaises(ValueError):
                fn(args)
