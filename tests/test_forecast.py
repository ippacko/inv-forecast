import unittest

from src.forecast import metrics, moving_average, seasonal_naive


class ForecastTests(unittest.TestCase):
    def test_seasonal_naive_repeats_weekly_pattern(self):
        self.assertEqual(seasonal_naive([1, 2, 3, 4, 5, 6, 7], 3), [1, 2, 3])

    def test_moving_average_is_stable(self):
        self.assertEqual(moving_average([2, 4, 6, 8], 2, window=2), [7, 7])

    def test_metrics_capture_perfect_prediction(self):
        self.assertEqual(metrics([1, 2], [1, 2]), {"mae": 0.0, "rmse": 0.0, "bias": 0.0})


if __name__ == "__main__":
    unittest.main()
