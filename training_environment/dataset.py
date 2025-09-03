import torch
import pandas as pd

from data_pipeline import utils as dp_utils
from scipy.signal import savgol_filter
from torch.utils.data import Dataset


# ------------------------------------------------------------------
# 1) Dataset
# ------------------------------------------------------------------
class TimeSeriesDataset(Dataset):
    def __init__(
        self,
        table_name,
        window_size,
        column_of_interest,
        datetime_column="timestamp",
        split_date=None,
        train_test_split=0.85,
        normalize=False,
        train_test="train",
    ):
        # get dataframe from postgres
        df = dp_utils.get_table(table_name=table_name)
        df.dropna(inplace=True)
        df = df.drop_duplicates(subset=["timestamp"], keep="first")
        df[datetime_column] = pd.to_datetime(df[datetime_column], format="mixed")
        df.set_index(datetime_column, inplace=True)
        df.sort_index(inplace=True, ascending=True)  # sort by ascending date

        self.window_size = window_size

        # Ignore data before split_date
        if split_date is not None:
            df = df[df.index > pd.to_datetime(split_date)]

        # Train-test split
        train_size = int(len(df) * train_test_split)
        if train_test == "train":
            df = df.iloc[:train_size]
            # print(df.head())
        elif train_test == "test":
            df = df.iloc[train_size:]
        else:
            raise ValueError(f"Invalid value for train_test: '{train_test}'")

        self.series = df[column_of_interest].values

        # Store references for (possible) normalization
        self.normalize = normalize
        if normalize and len(self.series) > 1:
            self.mean_val = self.series.mean()
            self.std_val = self.series.std() + 1e-8  # epsilon to avoid div-by-zero
            self.series = (self.series - self.mean_val) / self.std_val
        else:
            self.mean_val = 0.0
            self.std_val = 1.0

        self.series = self.filter_data(self.series, window=29, polyorder=2)

        # Keep the index if you want to refer back to actual time steps
        self.df_index = (
            df.index
        )  # So we can match predictions with timestamps if needed

    def __getitem__(self, index):
        # Return a single window + target
        if index + self.window_size >= len(self.series):
            raise IndexError("Index out of range for dataset")

        x = self.series[index : index + self.window_size]
        y = self.series[index + self.window_size]

        x = torch.tensor(x, dtype=torch.float32)
        y = torch.tensor(y, dtype=torch.float32)
        return x, y

    def __len__(self):
        return max(0, len(self.series) - self.window_size)

    def filter_data(self, data, window=9, polyorder=2):
        """Applies Savitzky-Golay filter and returns the filtered data."""
        return savgol_filter(data, window, polyorder)

    def inverse_transform(self, values):
        """
        Invert the normalization for an array/list of values back to original scale.
        """
        if not self.normalize:
            return values
        return [(v * self.std_val + self.mean_val) for v in values]