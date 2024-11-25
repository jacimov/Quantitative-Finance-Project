"""
Time Series Train-Test Split Module

This module provides functionality for splitting time series data into training
and testing sets. Unlike traditional random splits used in machine learning,
this module performs chronological splits to maintain the temporal order of
the data, which is crucial for financial time series analysis.
"""


def split_data(data, train_ratio=3/4):
    """
    Split time series data into training and testing sets chronologically.

    This function performs a chronological split of time series data,
    maintaining the temporal order which is crucial for financial data
    analysis. The split is performed at a specified ratio point in the data.

    Args:
        data (pd.DataFrame): Time series data to split
        train_ratio (float, optional): Ratio of data to use for training.
            Defaults to 3/4 (75% training, 25% testing)

    Returns:
        tuple[pd.DataFrame, pd.DataFrame]: A tuple containing:
            - train_data: Training dataset
            - test_data: Testing dataset

    Example:
        >>> train_data, test_data = split_data(forex_data, train_ratio=0.8)
        >>> print(f"Training size: {len(train_data)}")
        >>> print(f"Testing size: {len(test_data)}")
    """
    train_size = int(len(data) * train_ratio)
    train_data = data.iloc[:train_size]
    test_data = data.iloc[train_size:]
    return train_data, test_data
