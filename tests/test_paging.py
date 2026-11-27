import unittest
from backend.paging import compare_pages


class PagingTests(unittest.TestCase):
    def test_reference_workload(self):
        result = compare_pages("7 0 1 2 0 3 0 4 2 3 0 3 2", 3)
        self.assertEqual([result[k]["faults"] for k in ("FIFO", "LRU")], [10, 9])

    def test_hit_changes_only_lru_order(self):
        result = compare_pages("0,1,0,2", 2)
        self.assertEqual(result["FIFO"]["trace"][-1]["evicted"], 0)
        self.assertEqual(result["LRU"]["trace"][-1]["evicted"], 1)
        self.assertEqual(result["FIFO"]["trace"][0]["frames"], [0])

    def test_invalid_input(self):
        for pages, frames in [("", 1), ("1 100", 3), ("x", 1), ("0 " * 41, 3), ("1", True), ("1", 9)]:
            with self.subTest(pages=pages, frames=frames), self.assertRaises(ValueError):
                compare_pages(pages, frames)
