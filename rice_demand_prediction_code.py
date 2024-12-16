# -*- coding: utf-8 -*-
"""RICE_DEMAND_PREDICTION_CODE.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1qcb8sPsDVI7gmjgQWFe5Bsa3_ueiz61K

**Install necessary libraries**
"""

!pip install catboost

"""**Import required libraries**"""

import pandas as pd
import numpy as np
import xgboost as xgb
from catboost import CatBoostRegressor
from sklearn.svm import SVR
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error,mean_absolute_percentage_error
import matplotlib.pyplot as plt

"""**Mount Google Drive to access the dataset**"""

from google.colab import drive
drive.mount('/content/drive')

"""**Step 1: Load the dataset**

*   Load the dataset from the specified path in Google Drive
*   The dataset is expected to be in CSV format and contains monthly data
*   Ensure the 'Month' column is in a recognizable date format





"""

file_path = '/content/drive/MyDrive/DATASET/FPS_Dataset.csv'  # Update the path if needed
df = pd.read_csv(file_path)

"""

1.   Convert the 'Month' column to datetime format
2.   Format: 'Jan-20', 'Feb-20', etc.


"""

df['Month'] = pd.to_datetime(df['Month'], format='%b-%y')

# Sort the dataset by the 'Month' column for chronological order
df = df.sort_values('Month')

df.head()  # Display the first few rows of the dataset

"""**Step 2: Preprocess the data**


*   Convert the 'CMR' column to numeric, handling any non-numeric values
*   Replace invalid values with NaN and impute them with the median value


"""

df['CMR'] = pd.to_numeric(df['CMR'], errors='coerce')
df['CMR'] = df['CMR'].fillna(df['CMR'].median())

"""
**Step 3: Create lag features**


*   Add lag features to capture historical trends in the 'CMR' data
*   For each of the last 12 months, create a new column


"""

for i in range(1, 13):
    df[f'last_{i}_month'] = df['CMR'].shift(i)

# Fill missing values in lag feature columns with the median of the respective columns
for col in df.columns:
    if 'last_' in col:
        df[col] = df[col].fillna(df[col].median())

"""**Step 4: Additional feature engineering**


*   Extract useful time-based features from the 'Month' column
*   Features include month, quarter, and year


"""

df['month'] = df['Month'].dt.month  # Extract the month as a numeric feature
df['quarter'] = df['Month'].dt.quarter  # Extract the quarter (1-4)
df['year'] = df['Month'].dt.year  # Extract the year

"""
**Step 5: Handle rows with NaN values created by lag features**


*  Drop rows that contain NaN values due to the shifting operation in lag features


"""

df = df.dropna()

"""
**Step 6: Split the dataset into training and testing sets**


*   Use data from 2018 to 2022 as the training set
*   Use data from 2023 as the testing set


"""

train_data = df[df['Month'].dt.year <= 2022]  # Training data: up to 2022
test_data = df[df['Month'].dt.year == 2023]  # Testing data: 2023

# Separate features (X) and target variable (y)
X_train = train_data.drop(['Month', 'CMR'], axis=1)  # Features for training
y_train = train_data['CMR']  # Target variable for training
X_test = test_data.drop(['Month', 'CMR'], axis=1)  # Features for testing
y_test = test_data['CMR']  # Target variable for testing

"""**Step 7: Train and evaluate models**

**XGBoost Model**


---


**Define hyperparameters for XGBoost. These parameters include:**
max_depth: Maximum depth of a tree
* learning_rate: Boosting learning rate
* n_estimators: Number of trees (boosting rounds)
* objective: Loss function (regression in this case)
* eval_metric: Evaluation metric used during training
"""

params = {
    'max_depth': 5,
    'learning_rate': 0.1,
    'n_estimators': 100,
    'objective': 'reg:squarederror',
    'eval_metric': 'rmse'
}

# Initialize and train the XGBoost regressor
xgb_model = xgb.XGBRegressor(**params)
xgb_model.fit(X_train, y_train)

# Make predictions using the XGBoost model
train_pred = xgb_model.predict(X_train)
test_pred = xgb_model.predict(X_test)

# Combine train and test predictions for evaluation
predictions = np.concatenate([train_pred, test_pred])

# Create a dataframe to store actual values and predictions
results = pd.DataFrame({
    'Month': pd.concat([train_data['Month'], test_data['Month']]).reset_index(drop=True),
    'Actual': pd.concat([train_data['CMR'], test_data['CMR']]).reset_index(drop=True),
    'XGBoost_Prediction': predictions
})

"""**CatBoost Model**


---


**Define hyperparameters for CatBoost. These include:**
* depth: Depth of the tree
* iterations: Number of boosting iterations
* l2_leaf_reg: L2 regularization term for leaf weights
* learning_rate: Boosting learning rate
"""

best_params = {'depth': 5, 'iterations': 100, 'l2_leaf_reg': 1, 'learning_rate': 0.2}

# Initialize and train the CatBoost regressor
final_cb = CatBoostRegressor(**best_params, random_state=42, silent=True)
final_cb.fit(X_train, y_train)

# Make predictions using the CatBoost model
train_pred = final_cb.predict(X_train)
test_pred = final_cb.predict(X_test)

# Combine train and test predictions for evaluation
predictions = np.concatenate([train_pred, test_pred])

# Create a dataframe to store actual values and predictions
results['CatBoost_Prediction'] = predictions

""" **Support Vector Regression (SVR) Model**


---


**Define parameters for SVR. These include:**
* kernel: Kernel type ('linear', 'poly', 'rbf', 'sigmoid')


* C: Regularization parameter (higher C -> less regularization)
"""

kernel = 'rbf'  # Radial basis function kernel
C = 10000  # Regularization parameter

# Initialize and train the SVR model
svr_model = SVR(kernel=kernel, C=C)
svr_model.fit(X_train, y_train)

# Make predictions using the SVR model
train_pred = svr_model.predict(X_train)
test_pred = svr_model.predict(X_test)

# Combine train and test predictions for evaluation
predictions = np.concatenate([train_pred, test_pred])

# Add SVR predictions to the results dataframe
results['SVR_Prediction'] = predictions

"""**Random Forest Model**


---


**Define hyperparameters for Random Forest. These include:**
* n_estimators: Number of trees
* max_depth: Maximum depth of the tree
* random_state: Random seed for reproducibilit
"""

params = {
    'n_estimators': 100,
    'max_depth': 10,
    'random_state': 42
}

# Initialize and train the Random Forest regressor
rf_model = RandomForestRegressor(**params)
rf_model.fit(X_train, y_train)

# Make predictions using the Random Forest model
train_pred = rf_model.predict(X_train)
test_pred = rf_model.predict(X_test)

# Combine train and test predictions for evaluation
predictions = np.concatenate([train_pred, test_pred])

# Add Random Forest predictions to the results dataframe
results['RandomForest_Prediction'] = predictions

# Display the final results
display(results)

"""**Step 8: Visualize and evaluate model performance**

"""

# results for all models are combined into one DataFrame
results = pd.DataFrame({
    'Month': pd.concat([train_data['Month'], test_data['Month']]).reset_index(drop=True),
    'Actual': pd.concat([train_data['CMR'], test_data['CMR']]).reset_index(drop=True),
    'XGBoost_Prediction': xgb_model.predict(pd.concat([X_train, X_test])),
    'CatBoost_Prediction': final_cb.predict(pd.concat([X_train, X_test])),
    'SVR_Prediction': svr_model.predict(pd.concat([X_train, X_test])),
    'RandomForest_Prediction': rf_model.predict(pd.concat([X_train, X_test]))
})

# Visualization for all models
plt.figure(figsize=(20, 12))

# Models to visualize
models = ['XGBoost_Prediction', 'CatBoost_Prediction', 'SVR_Prediction', 'RandomForest_Prediction']
model_names = ['XGBoost', 'CatBoost', 'SVR', 'Random Forest']
colors = ['red', 'green', 'purple', 'blue']

for i, (model, name, color) in enumerate(zip(models, model_names, colors)):
    plt.subplot(3, 2, i + 1)

    # Plot the actual data
    plt.plot(results['Month'], results['Actual'], marker='o', linestyle='-', color='black', label='Actual')

    # Plot the model predictions
    results_filtered = results[(results['Month'] >= '2023-01-01')]
    plt.plot(results_filtered['Month'], results_filtered[model], marker='o', linestyle='-', color=color, label=f'{name} Prediction')

    # Add a vertical line to separate train and test data
    plt.axvline(x=pd.Timestamp('2023-01-01'), color='gray', linestyle='--')

    # Fill the area between the model predictions and the horizontal axis
    plt.fill_between(results_filtered['Month'], results_filtered[model], color=color, alpha=0.1)

    # Add title and labels
    plt.title(f'{name} Model Prediction')
    plt.xlabel('Month')
    plt.ylabel('CMR')

    # Format the x-axis with date ticks
    plt.xticks(pd.date_range(start=df['Month'].min(), end=df['Month'].max(), freq='2MS').to_pydatetime(), rotation=45)

    # Set x-axis and y-axis limits
    plt.xlim(df['Month'].min() - pd.DateOffset(months=1), df['Month'].max() + pd.DateOffset(months=1))
    plt.ylim(results['Actual'].min() * 0.9, results['Actual'].max() * 1.1)

    # Add legend
    plt.legend()

# Adjust layout to prevent overlap
plt.tight_layout()

# Display the plot
plt.show()

# Calculate and print model performance metrics for each model
for model, name in zip(models, model_names):
    mape = mean_absolute_percentage_error(results['Actual'], results[model])*100
    rmse = mean_squared_error(results['Actual'],results[model],squared=False)
    r2 = r2_score(results['Actual'], results[model])
    mae = mean_absolute_error(results['Actual'], results[model])

    print(f"{name} Model Performance:")
    print(f"Mean Absolute Percentage Error (MAPE): {mape:.3f}%")
    print(f"Root Mean Squared Error (RMSE): {rmse:.2f}")
    print(f"R² Score: {r2:.2f}")
    print(f"Mean Absolute Error (MAE): {mae:.2f}\n")

"""**Performance Metrics Visualization**"""

# Values for
mape_values = [6.210, 4.778, 15.730, 23.227]
rmse_values = [371.93, 313.11, 443.95, 463.14]
r2_values = [0.91, 0.94, 0.87, 0.86]
mae_values = [132.13, 97.69, 205.48, 334.13]
labels = ['XGBoost', 'CatBoost', 'SVR', 'RandomForest']

# Create subplots
fig, axes = plt.subplots(2, 2, figsize=(12, 10))
fig.suptitle('Comparison of Model Performance Metrics')

# Plot MAPE
axes[0, 0].plot(labels, mape_values, marker='o', linestyle='--', color='red')
axes[0, 0].set_title('MAPE')
axes[0, 0].set_xlabel('Models')
axes[0, 0].set_ylabel('MAPE')
for label, value in zip(labels, mape_values):
    axes[0, 0].text(label, value, f'{value:.2f}', ha='left', va='bottom')

# Plot RMSE
axes[0, 1].plot(labels, rmse_values, marker='o', linestyle='--', color='blue')
axes[0, 1].set_title('RMSE')
axes[0, 1].set_xlabel('Models')
axes[0, 1].set_ylabel('RMSE')
for label, value in zip(labels, rmse_values):
    axes[0, 1].text(label, value, f'{value:.2f}', ha='left', va='bottom')

# Plot R² Score
axes[1, 0].plot(labels, r2_values, marker='o', linestyle='--', color='green')
axes[1, 0].set_title('R² Score')
axes[1, 0].set_xlabel('Models')
axes[1, 0].set_ylabel('R² Score')
for label, value in zip(labels, r2_values):
    axes[1, 0].text(label, value, f'{value:.2f}', ha='left', va='bottom')

# Plot MAE
axes[1, 1].plot(labels, mae_values, marker='o', linestyle='--', color='black')
axes[1, 1].set_title('MAE')
axes[1, 1].set_xlabel('Models')
axes[1, 1].set_ylabel('MAE')
for label, value in zip(labels, mae_values):
    axes[1, 1].text(label, value, f'{value:.2f}', ha='left', va='bottom')

# Adjust layout
plt.tight_layout(rect=[0, 0, 0.9, 0.9])
plt.show()

"""**Future Predictions for 2024**"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score

# Combine train and test data for a complete dataset
df_combined = pd.concat([train_data, test_data]).reset_index(drop=True)

# Create the results DataFrame for train and test data
results = pd.DataFrame({
    'Month': df_combined['Month'],
    'Actual': df_combined['CMR'],
    'CatBoost_Prediction': final_cb.predict(pd.concat([X_train, X_test])),
    'XGBoost_Prediction': xgb_model.predict(pd.concat([X_train, X_test]))
})

# Predicting for the year 2024
dates_2024 = pd.date_range(start='2024-01-01', end='2024-12-01', freq='MS')
X_2024 = pd.DataFrame({'Month': dates_2024})

# Creating lag features for 2024 predictions
for i in range(1, 13):
    X_2024[f'last_{i}_month'] = df_combined['CMR'].shift(i).fillna(df_combined['CMR'].median()).iloc[-12:].reset_index(drop=True)

# Additional feature engineering for 2024
X_2024['month'] = X_2024['Month'].dt.month
X_2024['quarter'] = X_2024['Month'].dt.quarter
X_2024['year'] = X_2024['Month'].dt.year

# Remove rows with NaN values due to lag features
X_2024 = X_2024.dropna()

# Predict using both models
results_2024 = pd.DataFrame({'Month': dates_2024})
results_2024['CatBoost_Prediction'] = final_cb.predict(X_2024.drop('Month', axis=1))
results_2024['XGBoost_Prediction'] = xgb_model.predict(X_2024.drop('Month', axis=1))

# Filter results to exclude predictions before 2023
results['CatBoost_Prediction'] = np.where(results['Month'] >= '2023-01-01', results['CatBoost_Prediction'], np.nan)
results['XGBoost_Prediction'] = np.where(results['Month'] >= '2023-01-01', results['XGBoost_Prediction'], np.nan)

# Concatenate the 2024 predictions to the results to ensure continuity
results = pd.concat([results, results_2024], ignore_index=True)

# Visualization for all models
plt.figure(figsize=(20, 12))

# Models to visualize
models = ['CatBoost_Prediction', 'XGBoost_Prediction']
model_names = ['CatBoost', 'XGBoost']
colors = ['green', 'red']

for i, (model, name, color) in enumerate(zip(models, model_names, colors)):
    plt.subplot(2, 2, i + 1)

    # Plot the actual data
    plt.plot(results['Month'], results['Actual'], marker='o', linestyle='-', color='black', label='Actual')

    # Plot the model predictions for training and test data from 2023 onwards
    plt.plot(results['Month'], results[model], marker='o', linestyle='-', color=color, label=f'{name} Prediction')

    # Plot the model predictions for 2024
    plt.plot(results_2024['Month'], results_2024[model], marker='o', linestyle='-', color=color, alpha=0.5, label=f'{name} 2024 Prediction')

    # Add a vertical line to separate train and test data
    plt.axvline(x=pd.Timestamp('2023-01-01'), color='gray', linestyle='--')

    # Add a vertical line to indicate 2024
    plt.axvline(x=pd.Timestamp('2024-01-01'), color='gray', linestyle='--')

    # Add title and labels
    plt.title(f'{name} Model Prediction')
    plt.xlabel('Month')
    plt.ylabel('CMR')

    # Format the x-axis with date ticks
    plt.xticks(pd.date_range(start=df_combined['Month'].min(), end=dates_2024.max(), freq='3MS').to_pydatetime(), rotation=45, fontweight='bold')

    # Set x-axis and y-axis limits
    plt.xlim(df_combined['Month'].min() - pd.DateOffset(months=1), dates_2024.max() + pd.DateOffset(months=1))
    plt.ylim(results['Actual'].min() * 0.9, results['Actual'].max() * 1.1)

    # Add legend
    plt.legend()

# Adjust layout to prevent overlap
plt.tight_layout()

# Display the plot
plt.show()