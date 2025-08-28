import torch
import pandas as pd
import torch.nn as nn
import matplotlib.pyplot as plt
from torch.utils.data import DataLoader
from dataset import TimeSeriesDataset
from data_pipeline import utils as dp_utils

# ------------------------------------------------------------------
# 1) MLP Model
# ------------------------------------------------------------------
class MLP(nn.Module):
    def __init__(self, input_dim, hidden_dim=128, dropout_p=0.5):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, hidden_dim ),
            nn.GELU(),
            nn.Dropout(p=dropout_p),
            nn.Linear(hidden_dim , 1)
        )

    def forward(self, x):
        return self.net(x)

# ------------------------------------------------------------------
# 2) Training Loop
# ------------------------------------------------------------------
def train(model, criterion, optimizer, dataloader, test_dataloader=None, epochs=10):
    train_losses = []
    test_losses = []

    for epoch in range(epochs):
        model.train()
        epoch_loss = 0.0

        for X_train, y_train in dataloader:
            y_train = y_train.view(-1, 1)  # (batch_size, 1)

            optimizer.zero_grad()
            outputs = model(X_train)        # (batch_size, 1)
            loss = criterion(outputs, y_train)
            loss.backward()
            optimizer.step()

            epoch_loss += loss.item()

        train_loss = epoch_loss / len(dataloader)
        train_losses.append(train_loss)

        # Evaluate on test set if provided
        if test_dataloader is not None:
            model.eval()
            test_loss = 0.0
            with torch.no_grad():
                for X_test, y_test in test_dataloader:
                    y_test = y_test.view(-1, 1)
                    preds = model(X_test)
                    test_loss += criterion(preds, y_test).item()
            test_loss /= len(test_dataloader)
            test_losses.append(test_loss)
            print(f"Epoch {epoch+1}/{epochs} => Train Loss: {train_loss:.4f}, Test Loss: {test_loss:.4f}")
        else:
            print(f"Epoch {epoch+1}/{epochs} => Train Loss: {train_loss:.4f}")

    return train_losses, test_losses

# ------------------------------------------------------------------
# 3) Multi-step Forecast (rolling out in time)
# ------------------------------------------------------------------
def multi_step_forecast(model, dataset, horizon=5):
    """
    Forecast 'horizon' steps ahead by iteratively using the model's predictions.
    """
    model.eval()

    # 1) Grab the last window of data from the dataset
    last_window = dataset.series[-dataset.window_size:]  # shape = [window_size]

    # 2) Create a batch dimension for the model: [1, window_size]
    window_x = torch.tensor(last_window, dtype=torch.float32).view(1, -1)

    # 3) Iteratively predict horizon steps, each time sliding the window
    forecast_normalized = []
    with torch.no_grad():
        for _ in range(horizon):
            pred = model(window_x)   # shape [1,1]
            pred_val = pred.item()   # scalar (normalized)
            forecast_normalized.append(pred_val)

            # Slide the window left by 1, append the new prediction
            window_x = window_x[:, 1:]  # drop oldest point
            new_pred = torch.tensor([[pred_val]], dtype=torch.float32)
            window_x = torch.cat([window_x, new_pred], dim=1)  # shape [1, window_size]

    # 4) Invert normalization to get original scale (if dataset.normalize=True)
    if dataset.normalize:
        forecast_vals = dataset.inverse_transform(forecast_normalized)

    return forecast_vals


# ------------------------------------------------------------------
# 4) Set up the main code
# ------------------------------------------------------------------
if __name__ == '__main__':
    table_name = "w4_calc"
    column_of_interest = "w4_building_consumption"
    split_date = None
    window_size = 8000
    horizon_steps = 100
    epochs = 100

    # 1) Create train/test sets
    train_battery_dataset = TimeSeriesDataset(
        table_name=table_name,
        column_of_interest=column_of_interest,
        window_size=window_size,
        split_date=split_date,
        train_test_split=1,   # notice 1 means we are merging the test and train datasets for training. This is fine because we are doing forecasting
        train_test='train',
        normalize=True
    )
    test_battery_dataset = TimeSeriesDataset(
        table_name=table_name,
        column_of_interest=column_of_interest,
        window_size=window_size,
        split_date=split_date,
        train_test_split=0.85,
        train_test='test',
        normalize=True
    )

    # 2) Build dataloaders
    train_loader = DataLoader(train_battery_dataset, batch_size=32, shuffle=True)
    test_loader = DataLoader(test_battery_dataset, batch_size=32, shuffle=False)

    # 3) Define model, loss, optimizer
    model = MLP(window_size, hidden_dim=22)
    criterion = nn.MSELoss()
    optimizer = torch.optim.AdamW(model.parameters(), lr=1e-4)

    # 4) Train
    train_loss, test_loss = train(model, criterion, optimizer, train_loader, test_loader, epochs=epochs)

    # 5) Save training & test loss
    loss_df = pd.DataFrame()
    if train_loss and test_loss:
        loss_df['train_loss'] = train_loss
        loss_df['test_loss'] = test_loss
        dp_utils.save_df_to_db(
            loss_df,
            "MLP_loss_calc",
            if_exists="replace"
        )

    # ------------------------------------------------------------------
    # 6) Forecast
    # ------------------------------------------------------------------
    forecast_vals = multi_step_forecast(model, test_battery_dataset, horizon=horizon_steps)

    # 1) Last timestamp in the test dataset (test_battery_dataset.df_index)
    df_index = test_battery_dataset.df_index  # This is the test portion's index
    last_timestamp = df_index[-1]

    # 2) Infer the frequency (if your data is regular). Pandas can guess or we can manually compute.
    # freq = pd.infer_freq(df_index)  # might return None if not strictly regular
    # if  len(df_index) < 2:
    #     freq = df_index[-1] - df_index[-2]
    # else:
    #     freq = pd.Timedelta("10min")

    freq = pd.Timedelta("10min")

    # 3) Create future timestamps
    forecast_timestamps = [last_timestamp + (i+1)*freq for i in range(horizon_steps)]

    # 4) Save result into postgres
    forecast_df = pd.DataFrame()
    if forecast_vals and forecast_timestamps:
        forecast_df['timestamp'] = forecast_timestamps
        forecast_df[f'{column_of_interest}'] = forecast_vals
        dp_utils.save_df_to_db(
            forecast_df,
            "MLP_forecast_calc",
            if_exists="replace"
        )

