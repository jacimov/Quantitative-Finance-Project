# train_test_split.py
def split_data(data, train_ratio=3/4):
    train_size = int(len(data) * train_ratio)
    train_data = data.iloc[:train_size]
    test_data = data.iloc[train_size:]
    return train_data, test_data
