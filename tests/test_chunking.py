import unittest

from utils.chunking import chunked


class ChunkingTests(unittest.TestCase):
    def test_chunked_splits_items_into_fixed_size_groups(self):
        self.assertEqual(chunked([1, 2, 3, 4, 5], 2), [[1, 2], [3, 4], [5]])

    def test_chunked_rejects_invalid_size(self):
        with self.assertRaises(ValueError):
            chunked([1], 0)


if __name__ == "__main__":
    unittest.main()
