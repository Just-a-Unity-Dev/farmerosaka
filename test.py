import unittest


class ExampleTests(unittest.TestCase):
    def test_example(self):
        x = 0
        self.assertEqual(x, 0)


if __name__ == '__main__':
    unittest.main()
