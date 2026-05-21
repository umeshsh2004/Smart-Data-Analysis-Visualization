import unittest


class TestSmoke(unittest.TestCase):
    def test_imports(self) -> None:
        import src.new_project.filters  # noqa: F401
        import src.new_project.preprocessing  # noqa: F401


if __name__ == "__main__":
    unittest.main()

