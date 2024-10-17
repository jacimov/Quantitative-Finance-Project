# optimization.py
import numpy as np
from itertools import product
import multiprocessing as mp
from tqdm import tqdm
from backtesting_runner import run_single_backtest
from utils import calculate_sharpe_ratio

def run_backtest_with_params(args):
    params, train_data, test_data, optimization_target = args
    bt_train_result = run_single_backtest(train_data, params)
    bt_test_result = run_single_backtest(test_data, params)

    train_equity_curve = bt_train_result['_equity_curve']['Equity'].values
    test_equity_curve = bt_test_result['_equity_curve']['Equity'].values
    if optimization_target == 'sharpe':
        train_metric = calculate_sharpe_ratio(train_equity_curve, 0.02)
        test_metric = calculate_sharpe_ratio(test_equity_curve, 0.02)
    elif optimization_target == 'return':
        train_metric = bt_train_result['Return [%]']
        test_metric = bt_test_result['Return [%]']

    return params, train_metric, test_metric

def optimize_strategy(train_data, test_data, param_ranges, optimization_target):
    best_train_metric = -np.inf
    best_params = None
    results = []

    param_combinations = list(product(*param_ranges.values()))
    total_iterations = len(param_combinations)

    with mp.Pool(processes=mp.cpu_count()) as pool:
        with tqdm(total=total_iterations, desc=f"Optimizing {optimization_target}") as pbar:
            for result in pool.imap_unordered(run_backtest_with_params, [(dict(zip(param_ranges.keys(), p)), train_data, test_data, optimization_target) for p in param_combinations]):
                params, train_metric, test_metric = result
                results.append({**params, optimization_target: train_metric})
                if train_metric > best_train_metric:
                    best_train_metric = train_metric
                    best_params = params

                pbar.update()

    best_test_metric = [r[optimization_target] for r in results if all(r[k] == v for k, v in best_params.items())][0]

    return best_params, best_train_metric, best_test_metric, results
