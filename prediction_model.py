"""
系统模块二：冰川指标预测模型与类型判断模块
功能：
1. 基于历史数据构建多种回归预测模型（线性回归、多项式回归、指数回归）
2. 预测未来年份的6个指标值（ela, Pa, T20, Ta, Ts, v）
3. 根据5个指标值（除ELA外）和阈值判断冰川类型（EXT/SUB/MAR）
4. 计算转型指数，评估冰川类型转型程度
"""

import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import PolynomialFeatures
from sklearn.metrics import r2_score, mean_squared_error
import warnings
warnings.filterwarnings('ignore')

# 冰川类型阈值定义
THRESHOLDS = {
    'EXT': {
        'Ta': (-20, -10),
        'Ts': (-15, -1),
        'Pa': (200, 500),
        'T20': (-20, -10),
        'v': (30, 50)
    },
    'SUB': {
        'Ta': (-12, -6),
        'Ts': (0, 3),
        'Pa': (500, 1000),
        'T20': (-10, -1),
        'v': (50, 100)
    },
    'MAR': {
        'Ta': (-6, 10),
        'Ts': (1, 5),
        'Pa': (1000, 3000),
        'T20': (-1, 0),
        'v': (100, 500)
    }
}

class GlacierPredictionModel:
    """冰川指标预测模型类"""
    
    def __init__(self):
        self.models = {}
        self.model_types = ['linear', 'polynomial', 'exponential']
    
    def prepare_data(self, data):
        """
        准备训练数据
        参数:
            data: 列表，包含 {'year': int, 'ela': float, ...} 的字典
        返回:
            X: 年份数组
            y_dict: 各指标值的字典
        """
        years = []
        indicators = {
            'ela': [],
            'Pa': [],
            'T20': [],
            'Ta': [],
            'Ts': [],
            'v': []
        }
        
        # 过滤掉空值
        for item in data:
            if item['year'] is not None:
                years.append(item['year'])
                for key in indicators.keys():
                    value = item.get(key)
                    # 确保值是数值类型
                    if value is not None:
                        try:
                            value = float(value)
                            indicators[key].append(value)
                        except (TypeError, ValueError):
                            indicators[key].append(np.nan)
                    else:
                        indicators[key].append(np.nan)
        
        X = np.array(years, dtype=np.float64).reshape(-1, 1)
        
        # 将indicators转换为numpy数组
        for key in indicators.keys():
            indicators[key] = np.array(indicators[key], dtype=np.float64)
        
        return X, indicators
    
    def fit_linear_model(self, X, y):
        """拟合线性回归模型"""
        # 确保y是numpy数组
        if not isinstance(y, np.ndarray):
            y = np.array(y, dtype=np.float64)
        else:
            y = y.astype(np.float64)
        
        # 过滤NaN值
        mask = ~np.isnan(y)
        if np.sum(mask) < 2:
            return None
        
        X_clean = X[mask]
        y_clean = y[mask]
        
        try:
            model = LinearRegression()
            model.fit(X_clean, y_clean)
            return model
        except Exception as e:
            print(f"线性模型拟合错误: {e}")
            return None
    
    def fit_polynomial_model(self, X, y, degree=2):
        """拟合多项式回归模型"""
        # 确保y是numpy数组
        if not isinstance(y, np.ndarray):
            y = np.array(y, dtype=np.float64)
        else:
            y = y.astype(np.float64)
        
        # 过滤NaN值
        mask = ~np.isnan(y)
        if np.sum(mask) < degree + 1:
            return None
        
        X_clean = X[mask]
        y_clean = y[mask]
        
        try:
            poly_features = PolynomialFeatures(degree=degree)
            X_poly = poly_features.fit_transform(X_clean)
            
            model = LinearRegression()
            model.fit(X_poly, y_clean)
            return {'model': model, 'poly_features': poly_features}
        except Exception as e:
            print(f"多项式模型拟合错误: {e}")
            return None
    
    def fit_exponential_model(self, X, y):
        """拟合指数回归模型（通过对数变换转为线性）"""
        # 确保y是numpy数组
        if not isinstance(y, np.ndarray):
            y = np.array(y, dtype=np.float64)
        else:
            y = y.astype(np.float64)
        
        # 过滤NaN值和负值/零值
        mask = ~np.isnan(y) & (y > 0)
        if np.sum(mask) < 2:
            return None
        
        X_clean = X[mask]
        y_clean = y[mask]
        
        # 对数变换
        try:
            y_log = np.log(y_clean)
            model = LinearRegression()
            model.fit(X_clean, y_log)
            return model
        except Exception as e:
            print(f"指数模型拟合错误: {e}")
            return None
    
    def predict_linear(self, model, X):
        """线性模型预测"""
        if model is None:
            return None
        try:
            pred = model.predict(X)
            # 确保返回numpy数组
            return np.array(pred, dtype=np.float64)
        except Exception as e:
            print(f"线性预测错误: {e}")
            return None
    
    def predict_polynomial(self, model_dict, X):
        """多项式模型预测"""
        if model_dict is None:
            return None
        try:
            X_poly = model_dict['poly_features'].transform(X)
            pred = model_dict['model'].predict(X_poly)
            # 确保返回numpy数组
            return np.array(pred, dtype=np.float64)
        except Exception as e:
            print(f"多项式预测错误: {e}")
            return None
    
    def predict_exponential(self, model, X):
        """指数模型预测"""
        if model is None:
            return None
        try:
            y_log = model.predict(X)
            pred = np.exp(y_log)
            # 确保返回numpy数组
            return np.array(pred, dtype=np.float64)
        except Exception as e:
            print(f"指数预测错误: {e}")
            return None
    
    def train_models(self, data):
        """
        训练所有模型
        参数:
            data: 历史数据列表
        返回:
            dict: 包含各指标各模型的训练结果
        """
        X, indicators = self.prepare_data(data)
        
        if len(X) < 2:
            return None
        
        results = {}
        
        for indicator_name, y_values in indicators.items():
            # y_values已经是numpy数组，但确保类型正确
            if isinstance(y_values, np.ndarray):
                y = y_values.astype(np.float64)
            else:
                y = np.array(y_values, dtype=np.float64)
            
            # 训练三种模型
            linear_model = self.fit_linear_model(X, y)
            poly_model = self.fit_polynomial_model(X, y, degree=2)
            exp_model = self.fit_exponential_model(X, y)
            
            # 计算模型评估指标
            models_info = {}
            
            if linear_model is not None:
                y_pred = self.predict_linear(linear_model, X)
                mask = ~np.isnan(y)
                if np.sum(mask) > 0:
                    r2 = r2_score(y[mask], y_pred[mask])
                    mse = mean_squared_error(y[mask], y_pred[mask])
                    models_info['linear'] = {
                        'model': linear_model,
                        'r2': float(r2),
                        'mse': float(mse)
                    }
            
            if poly_model is not None:
                y_pred = self.predict_polynomial(poly_model, X)
                mask = ~np.isnan(y)
                if np.sum(mask) > 0:
                    r2 = r2_score(y[mask], y_pred[mask])
                    mse = mean_squared_error(y[mask], y_pred[mask])
                    models_info['polynomial'] = {
                        'model': poly_model,
                        'r2': float(r2),
                        'mse': float(mse)
                    }
            
            if exp_model is not None:
                y_pred = self.predict_exponential(exp_model, X)
                mask = ~np.isnan(y) & (y > 0)
                if np.sum(mask) > 0:
                    r2 = r2_score(y[mask], y_pred[mask])
                    mse = mean_squared_error(y[mask], y_pred[mask])
                    models_info['exponential'] = {
                        'model': exp_model,
                        'r2': float(r2),
                        'mse': float(mse)
                    }
            
            results[indicator_name] = models_info
        
        return results
    
    def predict_future(self, trained_models, future_years):
        """
        预测未来年份的指标值
        参数:
            trained_models: train_models返回的结果
            future_years: 未来年份列表
        返回:
            dict: 包含各指标各模型的预测结果
        """
        if trained_models is None:
            return None
        
        X_future = np.array(future_years).reshape(-1, 1)
        predictions = {}
        
        for indicator_name, models_info in trained_models.items():
            indicator_predictions = {}
            
            for model_type, model_data in models_info.items():
                model = model_data['model']
                
                if model_type == 'linear':
                    pred = self.predict_linear(model, X_future)
                elif model_type == 'polynomial':
                    pred = self.predict_polynomial(model, X_future)
                elif model_type == 'exponential':
                    pred = self.predict_exponential(model, X_future)
                else:
                    pred = None
                
                if pred is not None:
                    try:
                        # 确保pred是numpy数组
                        if not isinstance(pred, np.ndarray):
                            pred = np.array(pred, dtype=np.float64)
                        else:
                            pred = pred.astype(np.float64)
                        
                        # 处理异常值：将NaN和inf替换为None
                        pred_list = []
                        for val in pred:
                            try:
                                # 检查是否为NaN或inf
                                if np.isnan(val) or np.isinf(val):
                                    pred_list.append(None)
                                else:
                                    pred_list.append(float(val))
                            except (TypeError, ValueError):
                                pred_list.append(None)
                        indicator_predictions[model_type] = pred_list
                    except Exception as e:
                        print(f"处理预测结果错误 ({indicator_name}, {model_type}): {e}")
                        # 如果处理失败，跳过该模型
                        continue
            
            predictions[indicator_name] = indicator_predictions
        
        return predictions


def classify_glacier_type(indicators):
    """
    根据5个指标值判断冰川类型
    参数:
        indicators: dict，包含 'Pa', 'T20', 'Ta', 'Ts', 'v' 的值
    返回:
        str: 冰川类型 ('EXT', 'SUB', 'MAR') 或 'UNKNOWN'
    """
    scores = {'EXT': 0, 'SUB': 0, 'MAR': 0}
    
    for type_name, thresholds in THRESHOLDS.items():
        for indicator_name, (min_val, max_val) in thresholds.items():
            value = indicators.get(indicator_name)
            if value is not None:
                if min_val <= value <= max_val:
                    scores[type_name] += 1
    
    # 找到得分最高的类型
    max_score = max(scores.values())
    if max_score == 0:
        return 'UNKNOWN'
    
    for type_name, score in scores.items():
        if score == max_score:
            return type_name
    
    return 'UNKNOWN'


def calculate_transition_index(predicted_indicators, base_type):
    """
    计算转型指数
    参数:
        predicted_indicators: dict，包含未来年份的5个指标值（除ELA外）
        base_type: str，当前冰川类型
    返回:
        int: 转型指数（5个指标值的分数相加，每个指标：高于阈值上限+1，低于下限-1，在范围内0）
    """
    if base_type not in THRESHOLDS:
        return 0
    
    transition_index = 0
    base_thresholds = THRESHOLDS[base_type]
    
    # 需要判断的5个指标
    indicator_names = ['Pa', 'T20', 'Ta', 'Ts', 'v']
    
    for indicator_name in indicator_names:
        value = predicted_indicators.get(indicator_name)
        if value is None:
            continue
        
        min_val, max_val = base_thresholds[indicator_name]
        
        # 高于阈值上限计+1，低于阈值下限计-1，在阈值内计0
        if value > max_val:
            transition_index += 1
        elif value < min_val:
            transition_index -= 1
        # else: 在阈值范围内，计为0（不需要操作）
    
    return transition_index


def predict_and_analyze(data, future_years_list):
    """
    预测并分析冰川类型转型
    参数:
        data: 历史数据列表
        future_years_list: 未来年份列表，如 [2035, 2050, 2075, 2100, 2125]
    返回:
        dict: 包含预测结果和转型分析
    """
    # 获取当前类型（使用最新年份的数据）
    if not data:
        return None
    
    latest_data = max(data, key=lambda x: x.get('year', 0))
    current_indicators = {
        'Pa': latest_data.get('Pa'),
        'T20': latest_data.get('T20'),
        'Ta': latest_data.get('Ta'),
        'Ts': latest_data.get('Ts'),
        'v': latest_data.get('v')
    }
    current_type = classify_glacier_type(current_indicators)
    
    # 训练模型
    predictor = GlacierPredictionModel()
    trained_models = predictor.train_models(data)
    
    if trained_models is None:
        return None
    
    # 预测所有未来年份
    all_future_years = sorted(set(future_years_list))
    predictions = predictor.predict_future(trained_models, all_future_years)
    
    # 分析每个未来年份的转型指数
    transition_analysis = {}
    
    for year in all_future_years:
        year_index = all_future_years.index(year)
        
        # 获取该年份的预测值（使用线性模型作为默认，如果不存在则尝试其他模型）
        predicted_indicators = {}
        for indicator_name in ['Pa', 'T20', 'Ta', 'Ts', 'v']:
            if indicator_name in predictions:
                # 优先使用线性模型
                if 'linear' in predictions[indicator_name] and \
                   predictions[indicator_name]['linear'][year_index] is not None:
                    predicted_indicators[indicator_name] = predictions[indicator_name]['linear'][year_index]
                elif 'polynomial' in predictions[indicator_name] and \
                     predictions[indicator_name]['polynomial'][year_index] is not None:
                    predicted_indicators[indicator_name] = predictions[indicator_name]['polynomial'][year_index]
                elif 'exponential' in predictions[indicator_name] and \
                     predictions[indicator_name]['exponential'][year_index] is not None:
                    predicted_indicators[indicator_name] = predictions[indicator_name]['exponential'][year_index]
        
        # 计算转型指数（5个指标值的分数相加）
        transition_index = calculate_transition_index(predicted_indicators, current_type)
        
        # 判断预测类型
        predicted_type = classify_glacier_type(predicted_indicators)
        
        transition_analysis[year] = {
            'indicators': predicted_indicators,
            'transition_index': transition_index,
            'predicted_type': predicted_type
        }
    
    return {
        'current_type': current_type,
        'predictions': predictions,
        'transition_analysis': transition_analysis,
        'model_metrics': {
            indicator: {
                model_type: {
                    'r2': model_data['r2'],
                    'mse': model_data['mse']
                }
                for model_type, model_data in models_info.items()
            }
            for indicator, models_info in trained_models.items()
        }
    }

