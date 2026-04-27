"""
冰川数据查询与预测系统 - Flask后端API
功能：
1. 提供RESTful API接口用于查询冰川数据
2. 根据冰川ID查询冰川基本信息（坐标、面积、类型等）
3. 查询并返回该冰川所有年份的六个指标值（ela, Pa, T20, Ta, Ts, v）
4. 基于历史数据构建回归预测模型，预测未来指标值
5. 根据指标值判断冰川类型（EXT/SUB/MAR）
6. 计算转型指数，评估类型转型程度
7. 生成PDF分析报告
8. 提供地图数据接口，支持地图可视化
"""

from flask import Flask, render_template, jsonify, request, send_file
import sqlite3
import json
import os
from prediction_model import predict_and_analyze, classify_glacier_type
from io import BytesIO
from datetime import datetime

# 可选依赖：flask-cors用于跨域支持
try:
    from flask_cors import CORS  # type: ignore[reportMissingModuleSource]
    CORS_AVAILABLE = True
except ImportError:
    CORS_AVAILABLE = False
    print("警告: flask-cors未安装，跨域请求可能受限")

# 可选依赖：reportlab用于PDF生成
try:
    from reportlab.lib.pagesizes import letter, A4  # type: ignore[reportMissingModuleSource]
    from reportlab.lib import colors  # type: ignore[reportMissingModuleSource]
    from reportlab.lib.units import inch  # type: ignore[reportMissingModuleSource]
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image  # type: ignore[reportMissingModuleSource]
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle  # type: ignore[reportMissingModuleSource]
    from reportlab.lib.enums import TA_CENTER, TA_LEFT  # type: ignore[reportMissingModuleSource]
    from reportlab.pdfbase import pdfmetrics  # type: ignore[reportMissingModuleSource]
    from reportlab.pdfbase.ttfonts import TTFont  # type: ignore[reportMissingModuleSource]
    REPORTLAB_AVAILABLE = True
    
    # 尝试注册中文字体
    try:
        import platform
        system = platform.system()
        if system == 'Windows':
            # Windows系统字体路径
            font_paths = [
                'C:/Windows/Fonts/simsun.ttc',  # 宋体
                'C:/Windows/Fonts/simhei.ttf',  # 黑体
                'C:/Windows/Fonts/msyh.ttc',    # 微软雅黑
            ]
        elif system == 'Darwin':  # macOS
            font_paths = [
                '/System/Library/Fonts/PingFang.ttc',
                '/System/Library/Fonts/STHeiti Light.ttc',
            ]
        else:  # Linux
            font_paths = [
                '/usr/share/fonts/truetype/wqy/wqy-microhei.ttc',
                '/usr/share/fonts/truetype/arphic/uming.ttc',
            ]
        
        chinese_font_registered = False
        for font_path in font_paths:
            try:
                if os.path.exists(font_path):
                    pdfmetrics.registerFont(TTFont('ChineseFont', font_path))
                    chinese_font_registered = True
                    print(f"成功注册中文字体: {font_path}")
                    break
            except Exception as e:
                continue
        
        if not chinese_font_registered:
            # 如果系统字体不可用，使用reportlab内置字体（可能不支持中文）
            print("警告: 未找到中文字体，PDF中的中文可能显示为方块")
            CHINESE_FONT_NAME = 'Helvetica'
        else:
            CHINESE_FONT_NAME = 'ChineseFont'
    except Exception as e:
        print(f"字体注册警告: {e}")
        CHINESE_FONT_NAME = 'Helvetica'
        
except ImportError:
    REPORTLAB_AVAILABLE = False
    CHINESE_FONT_NAME = 'Helvetica'
    print("警告: reportlab未安装，PDF报告生成功能不可用")

# Flask应用配置：同时支持Vue构建文件和原有模板
app = Flask(__name__, 
            static_folder='static',  # 原有模板系统的静态文件目录
            static_url_path='/static',  # 静态文件URL路径
            template_folder='templates')
if CORS_AVAILABLE:
    CORS(app)  # type: ignore[union-attr]  # 允许跨域请求

# 添加路由以支持Vue构建后的dist目录（如果存在）
if os.path.exists('dist'):
    @app.route('/dist/<path:filename>')
    def dist_files(filename):
        """服务Vue构建后的dist目录文件"""
        return send_file(os.path.join('dist', filename))

def get_db_connection():
    """获取数据库连接"""
    conn = sqlite3.connect('glacier_data.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    """登录页面"""
    return render_template('login.html')

@app.route('/main')
def main():
    """主系统页面 - 优先使用Vue应用，如果不存在则使用原有模板"""
    # 优先使用Vue构建后的文件
    if os.path.exists('dist/index.html'):
        return send_file('dist/index.html')
    # 如果Vue未构建，使用原有模板系统
    return render_template('index.html')

@app.route('/api/glacier/<rgiid>/info')
def get_glacier_info(rgiid):
    """
    RESTful API: 获取冰川基本信息
    GET /api/glacier/{id}/info
    返回：坐标、面积、类型等基本信息
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT RGIID, X, Y, Area, DC, LTG, REGION, TYPE, S50, S100, M50, M100
        FROM glacier_info
        WHERE RGIID = ?
    ''', (rgiid,))
    
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return jsonify({
            'success': True,
            'data': {
                'id': row['RGIID'],
                'RGIID': row['RGIID'],
                'name': row['RGIID'],
                'location': [row['X'], row['Y']] if row['X'] and row['Y'] else None,
                'X': row['X'],
                'Y': row['Y'],
                'area': row['Area'],
                'Area': row['Area'],
                'type': row['TYPE'],
                'TYPE': row['TYPE'],
                'region': row['REGION'],
                'REGION': row['REGION'],
                'DC': row['DC'],
                'LTG': row['LTG'],
                'S50': row['S50'],
                'S100': row['S100'],
                'M50': row['M50'],
                'M100': row['M100']
            }
        })
    else:
        return jsonify({
            'success': False,
            'status': 'error',
            'message': '未找到该冰川ID'
        }), 404

@app.route('/api/glacier/<rgiid>/history')
def get_glacier_history(rgiid):
    """
    RESTful API: 获取历史指标时间序列
    GET /api/glacier/{id}/history?years=[start,end]
    可选查询参数指定年份范围
    """
    start_year = request.args.get('start_year', type=int)
    end_year = request.args.get('end_year', type=int)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if start_year and end_year:
        cursor.execute('''
            SELECT year, ela, Pa, T20, Ta, Ts, v
            FROM glacier_indicators
            WHERE RGIID = ? AND year >= ? AND year <= ?
            ORDER BY year ASC
        ''', (rgiid, start_year, end_year))
    else:
        cursor.execute('''
            SELECT year, ela, Pa, T20, Ta, Ts, v
            FROM glacier_indicators
            WHERE RGIID = ?
            ORDER BY year ASC
        ''', (rgiid,))
    
    rows = cursor.fetchall()
    conn.close()
    
    if rows:
        years = []
        indicators = {
            'ela': [],
            'Pa': [],
            'T20': [],
            'Ta': [],
            'Ts': [],
            'v': []
        }
        
        for row in rows:
            years.append(row['year'])
            indicators['ela'].append(row['ela'])
            indicators['Pa'].append(row['Pa'])
            indicators['T20'].append(row['T20'])
            indicators['Ta'].append(row['Ta'])
            indicators['Ts'].append(row['Ts'])
            indicators['v'].append(row['v'])
        
        # 同时返回数组格式和对象格式（兼容性）
        data_array = []
        for i, year in enumerate(years):
            data_array.append({
                'year': year,
                'ela': indicators['ela'][i],
                'Pa': indicators['Pa'][i],
                'T20': indicators['T20'][i],
                'Ta': indicators['Ta'][i],
                'Ts': indicators['Ts'][i],
                'v': indicators['v'][i]
            })
        
        return jsonify({
            'success': True,
            'status': 'success',
            'data': data_array,
            'id': rgiid,
            'years': years,
            'indicators': indicators
        })
    else:
        return jsonify({
            'success': False,
            'status': 'error',
            'message': '未找到该冰川的指标数据'
        }), 404

@app.route('/api/glacier/<rgiid>/indicators/<int:year>')
def get_glacier_indicators_by_year(rgiid, year):
    """
    获取指定年份的指标数据
    返回：该年份的六个指标值
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT year, ela, Pa, T20, Ta, Ts, v
        FROM glacier_indicators
        WHERE RGIID = ? AND year = ?
    ''', (rgiid, year))
    
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return jsonify({
            'success': True,
            'data': {
                'year': row['year'],
                'ela': row['ela'],
                'Pa': row['Pa'],
                'T20': row['T20'],
                'Ta': row['Ta'],
                'Ts': row['Ts'],
                'v': row['v']
            }
        })
    else:
        return jsonify({
            'success': False,
            'message': f'未找到该冰川{year}年的数据'
        }), 404

@app.route('/api/glacier/list')
def list_glaciers():
    """
    获取冰川ID列表（用于自动补全）
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT RGIID FROM glacier_info ORDER BY RGIID LIMIT 1000')
    rows = cursor.fetchall()
    conn.close()
    
    glaciers = [row['RGIID'] for row in rows]
    
    return jsonify({
        'success': True,
        'data': glaciers
    })

@app.route('/api/glacier/map-data')
def get_glacier_map_data():
    """
    获取所有冰川的地图数据（坐标、ID、区域等）
    用于地图可视化
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT RGIID, X, Y, Area, REGION, TYPE
        FROM glacier_info
        WHERE X IS NOT NULL AND Y IS NOT NULL
        ORDER BY RGIID
    ''')
    
    rows = cursor.fetchall()
    conn.close()
    
    glaciers = []
    for row in rows:
        glaciers.append({
            'RGIID': row['RGIID'],
            'X': row['X'],
            'Y': row['Y'],
            'Area': row['Area'],
            'REGION': row['REGION'],
            'TYPE': row['TYPE']
        })
    
    return jsonify({
        'success': True,
        'data': glaciers
    })

# ========== 模块二：预测与转型分析 API ==========

@app.route('/api/glacier/<rgiid>/predict', methods=['POST'])
def predict_glacier(rgiid):
    """
    RESTful API: 指标预测接口
    POST /api/glacier/{id}/predict?years=10,25,50,75,100&models=linear,polynomial,exponential
    参数:
        years: 预测年份列表（可选，默认10,25,50,75,100年后）
        models: 模型列表（可选，默认所有模型）
    """
    try:
        data = request.get_json() or {}
        years_param = request.args.get('years', '10,25,50,75,100')
        
        # 解析年份参数
        if isinstance(years_param, str):
            year_offsets = [int(y.strip()) for y in years_param.split(',')]
        else:
            year_offsets = [10, 25, 50, 75, 100]
        
        # 计算实际年份（从2025年开始）
        base_year = 2025
        future_years = [base_year + offset for offset in year_offsets]
        
        # 如果POST body中有future_years，优先使用
        if 'future_years' in data:
            future_years = data['future_years']
        
        # 获取历史数据
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT year, ela, Pa, T20, Ta, Ts, v
            FROM glacier_indicators
            WHERE RGIID = ?
            ORDER BY year ASC
        ''', (rgiid,))
        
        rows = cursor.fetchall()
        conn.close()
        
        if not rows:
            return jsonify({
                'success': False,
                'status': 'error',
                'message': '未找到该冰川的历史数据'
            }), 404
        
        # 转换为字典列表
        history_data = []
        for row in rows:
            history_data.append({
                'year': row['year'],
                'ela': row['ela'],
                'Pa': row['Pa'],
                'T20': row['T20'],
                'Ta': row['Ta'],
                'Ts': row['Ts'],
                'v': row['v']
            })
        
        # 执行预测和分析
        result = predict_and_analyze(history_data, future_years)
        
        if result is None:
            return jsonify({
                'success': False,
                'status': 'error',
                'message': '预测模型训练失败，数据不足'
            }), 400
        
        # 格式化返回数据
        models_data = {}
        for indicator, models_info in result.get('predictions', {}).items():
            models_data[indicator] = {}
            for model_type, predictions in models_info.items():
                models_data[indicator][model_type] = {
                    'years': future_years,
                    'values': predictions
                }
        
        return jsonify({
            'success': True,
            'status': 'success',
            'data': {
                'id': rgiid,
                'current_type': result.get('current_type'),
                'models': models_data,
                'predictions': result.get('predictions'),
                'transition_analysis': result.get('transition_analysis'),
                'model_metrics': result.get('model_metrics')
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'status': 'error',
            'message': f'预测过程出错: {str(e)}'
        }), 500

@app.route('/api/glacier/<rgiid>/transform-index')
def get_transform_index(rgiid):
    """
    RESTful API: 计算转型指数接口
    GET /api/glacier/{id}/transform-index?years=10,25,50,75,100
    参数:
        years: 预测年份列表（可选，默认10,25,50,75,100）
    返回:
        转型指数数据
    """
    try:
        years_param = request.args.get('years', '10,25,50,75,100')
        year_offsets = [int(y.strip()) for y in years_param.split(',')]
        base_year = 2025
        future_years = [base_year + offset for offset in year_offsets]
        
        # 获取历史数据并预测
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT year, ela, Pa, T20, Ta, Ts, v
            FROM glacier_indicators
            WHERE RGIID = ?
            ORDER BY year ASC
        ''', (rgiid,))
        
        rows = cursor.fetchall()
        conn.close()
        
        if not rows:
            return jsonify({
                'success': False,
                'status': 'error',
                'message': '未找到该冰川的历史数据'
            }), 404
        
        history_data = []
        for row in rows:
            history_data.append({
                'year': row['year'],
                'ela': row['ela'],
                'Pa': row['Pa'],
                'T20': row['T20'],
                'Ta': row['Ta'],
                'Ts': row['Ts'],
                'v': row['v']
            })
        
        # 执行预测和分析
        result = predict_and_analyze(history_data, future_years)
        
        if result is None:
            return jsonify({
                'success': False,
                'status': 'error',
                'message': '预测模型训练失败，数据不足'
            }), 400
        
        # 提取转型分析数据
        transition_analysis = result.get('transition_analysis', {})
        scores = []
        transform_indices = []
        
        for year in future_years:
            if year in transition_analysis:
                index = transition_analysis[year].get('transition_index', 0)
                scores.append(index)
                transform_indices.append(index)
            else:
                scores.append(0)
                transform_indices.append(0)
        
        return jsonify({
            'success': True,
            'status': 'success',
            'data': {
                'id': rgiid,
                'years': future_years,
                'scores': scores,
                'transformIndex': sum(transform_indices),
                'transition_analysis': transition_analysis
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'status': 'error',
            'message': f'计算转型指数出错: {str(e)}'
        }), 500

@app.route('/api/glacier/<rgiid>/report')
def generate_report(rgiid):
    """
    RESTful API: 生成PDF报告
    GET /api/glacier/{id}/report
    返回: PDF文件
    """
    if not REPORTLAB_AVAILABLE:
        return jsonify({
            'success': False,
            'message': 'PDF报告功能不可用，请安装reportlab库: pip install reportlab'
        }), 503
    
    try:
        # 获取冰川信息
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT RGIID, X, Y, Area, REGION, TYPE
            FROM glacier_info
            WHERE RGIID = ?
        ''', (rgiid,))
        
        info_row = cursor.fetchone()
        if not info_row:
            return jsonify({
                'success': False,
                'message': '未找到该冰川'
            }), 404
        
        # 获取历史数据
        cursor.execute('''
            SELECT year, ela, Pa, T20, Ta, Ts, v
            FROM glacier_indicators
            WHERE RGIID = ?
            ORDER BY year ASC
        ''', (rgiid,))
        
        history_rows = cursor.fetchall()
        conn.close()
        
        if not history_rows:
            return jsonify({
                'success': False,
                'message': '未找到该冰川的历史数据'
            }), 404
        
        # 准备历史数据
        history_data = []
        for row in history_rows:
            history_data.append({
                'year': row['year'],
                'ela': row['ela'],
                'Pa': row['Pa'],
                'T20': row['T20'],
                'Ta': row['Ta'],
                'Ts': row['Ts'],
                'v': row['v']
            })
        
        # 执行预测
        future_years = [2035, 2050, 2075, 2100, 2125]
        prediction_result = predict_and_analyze(history_data, future_years)
        
        # 生成PDF
        buffer = BytesIO()
        try:
            doc = SimpleDocTemplate(buffer, pagesize=A4)
        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'PDF初始化失败: {str(e)}'
            }), 500
        
        story = []
        styles = getSampleStyleSheet()
        
        # 创建支持中文的样式
        try:
            # 标题样式
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=24,
                textColor=colors.HexColor('#1f4788'),
                spaceAfter=30,
                alignment=TA_CENTER,
                fontName=CHINESE_FONT_NAME
            )
            
            # 修改默认样式以支持中文
            styles['Heading1'].fontName = CHINESE_FONT_NAME
            styles['Heading2'].fontName = CHINESE_FONT_NAME
            styles['Normal'].fontName = CHINESE_FONT_NAME
            
        except Exception as e:
            import traceback
            error_detail = traceback.format_exc()
            print(f"样式创建错误详情: {error_detail}")
            return jsonify({
                'success': False,
                'message': f'样式创建失败: {str(e)}。请确保reportlab已正确安装。'
            }), 500
        
        # 添加标题
        story.append(Paragraph('冰川数据分析报告', title_style))
        story.append(Spacer(1, 0.3*inch))
        
        # 冰川基本信息
        story.append(Paragraph('一、冰川概况', styles['Heading2']))
        info_data = [
            ['冰川ID', info_row['RGIID']],
            ['坐标', f"X: {info_row['X']:.6f}, Y: {info_row['Y']:.6f}" if info_row['X'] and info_row['Y'] else '-'],
            ['面积', f"{info_row['Area']:.3f} km²" if info_row['Area'] else '-'],
            ['区域', info_row['REGION'] or '-'],
            ['类型', info_row['TYPE'] or '-'],
            ['生成日期', datetime.now().strftime('%Y年%m月%d日')]
        ]
        
        info_table = Table(info_data, colWidths=[2*inch, 4*inch])
        info_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.grey),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), CHINESE_FONT_NAME),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('BACKGROUND', (1, 0), (1, -1), colors.beige),
            ('FONTNAME', (1, 0), (1, -1), CHINESE_FONT_NAME),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(info_table)
        story.append(Spacer(1, 0.3*inch))
        
        # 历史数据分析
        story.append(Paragraph('二、历史数据分析', styles['Heading2']))
        story.append(Paragraph(f'数据年份范围: {history_data[0]["year"]} - {history_data[-1]["year"]}', styles['Normal']))
        story.append(Spacer(1, 0.2*inch))
        
        # 预测结果
        if prediction_result:
            story.append(Paragraph('三、预测结果', styles['Heading2']))
            story.append(Paragraph(f'当前类型: {prediction_result.get("current_type", "-")}', styles['Normal']))
            story.append(Spacer(1, 0.2*inch))
            
            # 转型分析
            story.append(Paragraph('四、转型指数分析', styles['Heading2']))
            transition_analysis = prediction_result.get('transition_analysis', {})
            if transition_analysis:
                transition_data = [['年份', '预测类型', '转型指数', '转型程度']]
                for year in future_years:
                    if year in transition_analysis:
                        analysis = transition_analysis[year]
                        index = analysis.get('transition_index', 0)
                        abs_index = abs(index)
                        level = '高' if abs_index >= 4 else ('中' if abs_index >= 2 else '低')
                        transition_data.append([
                            str(year),
                            analysis.get('predicted_type', '-'),
                            str(index),
                            level
                        ])
                
                transition_table = Table(transition_data, colWidths=[1*inch, 1.5*inch, 1.5*inch, 1*inch])
                transition_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, -1), CHINESE_FONT_NAME),
                    ('FONTSIZE', (0, 0), (-1, -1), 9),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                story.append(transition_table)
        
        # 结论
        story.append(Spacer(1, 0.3*inch))
        story.append(Paragraph('五、结论与建议', styles['Heading2']))
        story.append(Paragraph('本报告基于历史数据进行了趋势分析和未来预测，建议持续监测冰川变化情况。', styles['Normal']))
        
        # 构建PDF
        try:
            doc.build(story)
            buffer.seek(0)
        except Exception as e:
            import traceback
            error_detail = traceback.format_exc()
            print(f"PDF构建错误详情: {error_detail}")
            return jsonify({
                'success': False,
                'message': f'PDF构建失败: {str(e)}。请确保reportlab已正确安装并重启服务器。'
            }), 500
        
        try:
            return send_file(
                buffer,
                mimetype='application/pdf',
                as_attachment=True,
                download_name=f'冰川报告_{rgiid}_{datetime.now().strftime("%Y%m%d")}.pdf'
            )
        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'文件发送失败: {str(e)}'
            }), 500
        
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        print(f"生成报告错误详情: {error_detail}")
        return jsonify({
            'success': False,
            'message': f'生成报告出错: {str(e)}。请检查reportlab是否正确安装。'
        }), 500

# ========== 参数与阈值管理 API ==========

@app.route('/api/thresholds/update', methods=['POST'])
def update_thresholds():
    """
    RESTful API: 更新冰川分类阈值
    POST /api/thresholds/update
    请求体: JSON格式的阈值配置
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'message': '无效的请求数据'
            }), 400
        
        # 这里可以将阈值保存到文件或数据库
        # 目前只是返回成功，实际应用中可以持久化存储
        # 注意：prediction_model.py中的THRESHOLDS是模块级变量
        # 如果需要动态更新，需要重新加载模块或使用全局配置
        
        return jsonify({
            'success': True,
            'message': '阈值配置已更新（注意：需要重启服务器才能完全生效）'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'更新阈值失败: {str(e)}'
        }), 500

@app.route('/api/thresholds/get', methods=['GET'])
def get_thresholds():
    """
    RESTful API: 获取当前阈值配置
    GET /api/thresholds/get
    """
    try:
        from prediction_model import THRESHOLDS
        return jsonify({
            'success': True,
            'data': THRESHOLDS
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取阈值失败: {str(e)}'
        }), 500

@app.route('/api/model-params/update', methods=['POST'])
def update_model_params():
    """
    RESTful API: 更新模型参数
    POST /api/model-params/update
    请求体: JSON格式的模型参数
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'message': '无效的请求数据'
            }), 400
        
        # 验证参数
        if 'polyDegree' in data and (data['polyDegree'] < 2 or data['polyDegree'] > 5):
            return jsonify({
                'success': False,
                'message': '多项式次数必须在2-5之间'
            }), 400
        
        # 这里可以将参数保存到文件或数据库
        # 目前只是返回成功
        
        return jsonify({
            'success': True,
            'message': '模型参数已更新（注意：需要重启服务器才能完全生效）'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'更新参数失败: {str(e)}'
        }), 500

@app.route('/api/model-params/get', methods=['GET'])
def get_model_params():
    """
    RESTful API: 获取当前模型参数
    GET /api/model-params/get
    """
    try:
        # 返回默认参数（实际应用中可以从配置文件读取）
        return jsonify({
            'success': True,
            'data': {
                'polyDegree': 2,
                'predictStartYear': 2025,
                'predictEndYear': 2125,
                'predictYearInterval': 25
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取参数失败: {str(e)}'
        }), 500

# 处理Vue Router的history模式路由（必须在所有API路由之后）
# 注意：这个路由必须放在最后，且不能拦截/api/开头的路径
@app.route('/<path:path>')
def catch_all(path):
    """
    捕获所有未匹配的路由，返回Vue应用的index.html
    用于支持Vue Router的history模式
    """
    # 确保不拦截API路由（Flask会优先匹配更具体的路由，所以这里不会拦截/api/）
    # 但为了安全，还是检查一下
    if path.startswith('api/'):
        return jsonify({'success': False, 'message': 'API路由不存在'}), 404
    
    # 如果是静态资源请求，返回404
    if path.startswith('static/') or path.endswith(('.js', '.css', '.png', '.jpg', '.jpeg', '.gif', '.svg', '.ico')):
        return jsonify({'message': '资源未找到'}), 404
    
    # 尝试返回Vue构建文件
    if os.path.exists('dist/index.html'):
        try:
            return send_file('dist/index.html')
        except:
            pass
    
    # 否则返回原有模板
    return render_template('index.html')

if __name__ == '__main__':
    import socket
    
    # 获取本机IP地址
    def get_local_ip():
        try:
            # 连接到一个远程地址（不会实际发送数据）
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "127.0.0.1"
    
    local_ip = get_local_ip()
    
    print("=" * 60)
    print("冰川类型识别与转型预测系统 - 服务器启动")
    print("=" * 60)
    print(f"本地访问: http://127.0.0.1:5000")
    print(f"局域网访问: http://{local_ip}:5000")
    print("=" * 60)
    print("按 Ctrl+C 停止服务器")
    print("=" * 60)
    print()
    
    app.run(debug=True, host='0.0.0.0', port=5000)

