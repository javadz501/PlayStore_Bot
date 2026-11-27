import unittest

from Services.architectures import (
    ARCHITECTURE_ABIS,
    SUPPORTED_ARCHITECTURES,
    UNSUPPORTED_ARCHITECTURES,
    architecture_plan,
)


class ArchitecturePlanTests(unittest.TestCase):
    def test_all_mode_returns_verified_architectures(self):
        self.assertEqual(architecture_plan("all", "arm64"), ("arm64", "armv7"))

    def test_single_mode_preserves_selected_architecture(self):
        self.assertEqual(architecture_plan("single", "armv7"), ("armv7",))

    def test_x86_targets_are_explicitly_unsupported(self):
        self.assertIn("x86", UNSUPPORTED_ARCHITECTURES)
        self.assertIn("x86_64", UNSUPPORTED_ARCHITECTURES)
        self.assertNotIn("x86", SUPPORTED_ARCHITECTURES)
        self.assertNotIn("x86_64", SUPPORTED_ARCHITECTURES)

    def test_abi_mapping(self):
        self.assertEqual(ARCHITECTURE_ABIS["arm64"], "arm64-v8a")
        self.assertEqual(ARCHITECTURE_ABIS["armv7"], "armeabi-v7a")

    def test_unknown_architecture_is_rejected(self):
        with self.assertRaises(ValueError):
            architecture_plan("single", "x86_64")


if __name__ == "__main__":
    unittest.main()
