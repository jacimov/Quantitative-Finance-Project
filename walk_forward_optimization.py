# walk_forward_optimization.py
import numpy as np
from itertools import product
from tqdm import tqdm
from optimization import optimize_strategy
from collections import Counter

def walk_forward_optimization(data, param_ranges, optimization_target, train_ratio=0.6, test_ratio=0.2):
    total_length = len(data)
    train_window = int(total_length * train_ratio)
    test_window = int(total_length * test_ratio)
    step_size = test_window  # We'll move forward by the size of the test window each time

    results = []
    best_params_list = []
    
    for i in tqdm(range(0, total_length - train_window - test_window + 1, step_size)):
        train_data = data.iloc[i:i+train_window]
        test_data = data.iloc[i+train_window:i+train_window+test_window]
        
        best_params, best_train_metric, best_test_metric, _ = optimize_strategy(train_data, test_data, param_ranges, optimization_target)
        
        print(f"Debug: Best params: {best_params}")
        print(f"Debug: Best train metric: {best_train_metric}")
        print(f"Debug: Best test metric: {best_test_metric}")
        
        results.append({
            'start_date': train_data.index[0],
            'end_date': test_data.index[-1],
            'best_params': best_params,
            'train_metric': best_train_metric,
            'test_metric': best_test_metric
        })
        
        best_params_list.append(best_params)
    
    return results, best_params_list

def aggregate_walk_forward_results(results):
    all_params = [result['best_params'] for result in results]
    
    avg_params = {}
    for key in all_params[0].keys():
        values = [params[key] for params in all_params]
        if isinstance(values[0], dict):
            avg_params[key] = {}
            for subkey in values[0].keys():
                subvalues = [v[subkey] for v in values]
                if all(isinstance(v, (int, float)) for v in subvalues):
                    avg_params[key][subkey] = np.mean(subvalues)
                else:
                    avg_params[key][subkey] = max(set(subvalues), key=subvalues.count)
        elif all(isinstance(v, (int, float)) for v in values):
            avg_params[key] = np.mean(values)
        else:
            avg_params[key] = max(set(values), key=values.count)
    
    # Convert integer parameters back to int
    for key in ['atr_period', 'high_period', 'low_period']:
        if key in avg_params:
            avg_params[key] = int(round(avg_params[key]))
        elif isinstance(avg_params.get('position_size'), dict) and key in avg_params['position_size']:
            avg_params['position_size'][key] = int(round(avg_params['position_size'][key]))
    
    avg_train_metric = np.mean([result['train_metric'] for result in results])
    avg_test_metric = np.mean([result['test_metric'] for result in results])
    
    return avg_params, avg_train_metric, avg_test_metric
