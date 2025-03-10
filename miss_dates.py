from sklearn.ensemble import RandomForestRegressor
import pandas as pd

# Sample Data Preparation
df = pd.DataFrame({
    'VISITNUM': [1, 2, 3, 4],
    'AGE': [32, 45, 29, 40],
    'AESTDTC': [pd.Timestamp('2024-01-10'), pd.NaT, pd.Timestamp('2024-03-10'), pd.NaT]
})

# Feature Engineering (Days since baseline)
df['BASELINE_DAYS'] = (df['AESTDTC'] - pd.Timestamp('2024-01-01')).dt.days

# Handle missing baseline days separately to avoid incorrect fill
baseline_days_mean = df['BASELINE_DAYS'].mean()

# Create training data where dates are not missing
training_data = df[df['AESTDTC'].notna()]
if not training_data.empty:
    X_train = training_data[['VISITNUM', 'AGE']]
    y_train = training_data['BASELINE_DAYS']

    # Model Training
    model = RandomForestRegressor(random_state=42)
    model.fit(X_train, y_train)

    # Predict missing dates
    missing_dates_idx = df['AESTDTC'].isna()
    if missing_dates_idx.any():  # Proceed only if there are missing dates
        X_pred = df.loc[missing_dates_idx, ['VISITNUM', 'AGE']]
        df.loc[missing_dates_idx, 'Predicted_Days'] = model.predict(X_pred)
        df.loc[missing_dates_idx, 'Predicted_Date'] = pd.Timestamp('2024-01-01') + pd.to_timedelta(df.loc[missing_dates_idx, 'Predicted_Days'], unit='D')
else:
    print("No valid data available for training. Skipping predictions.")

# Final Output
print(df)
