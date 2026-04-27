import pandas as pd
import sqlite3
import os
from datetime import datetime

# 定义指标文件映射
indicator_files = {
    'ela': 'sample_ela.xlsx',
    'Pa': 'sample_Pa.xlsx',
    'T20': 'sample_T20.xlsx',
    'Ta': 'sample_Ta.xlsx',
    'Ts': 'sample_Ts.xlsx',
    'v': 'sample_v.xlsx'
}

# 基本信息列（所有文件共有）
info_columns = ['RGIID', 'X', 'Y', 'Area', 'DC', 'LTG', 'REGION', 'TYPE', 'S50', 'S100', 'M50', 'M100']

def get_year_columns(df):
    """获取年份列（排除基本信息列）"""
    return [col for col in df.columns if col not in info_columns and isinstance(col, (int, float))]

def build_database():
    """构建数据库"""
    db_name = 'glacier_data.db'
    
    # 如果数据库已存在，删除它
    if os.path.exists(db_name):
        os.remove(db_name)
        print(f"已删除旧数据库: {db_name}")
    
    # 连接数据库
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    
    # 创建冰川基本信息表
    cursor.execute('''
        CREATE TABLE glacier_info (
            RGIID TEXT PRIMARY KEY,
            X REAL,
            Y REAL,
            Area REAL,
            DC TEXT,
            LTG TEXT,
            REGION TEXT,
            TYPE TEXT,
            S50 TEXT,
            S100 TEXT,
            M50 TEXT,
            M100 TEXT
        )
    ''')
    
    # 创建指标数据表
    cursor.execute('''
        CREATE TABLE glacier_indicators (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            RGIID TEXT NOT NULL,
            year INTEGER NOT NULL,
            ela REAL,
            Pa REAL,
            T20 REAL,
            Ta REAL,
            Ts REAL,
            v REAL,
            FOREIGN KEY (RGIID) REFERENCES glacier_info(RGIID),
            UNIQUE(RGIID, year)
        )
    ''')
    
    # 创建索引以提高查询性能
    cursor.execute('CREATE INDEX idx_rgiid_year ON glacier_indicators(RGIID, year)')
    cursor.execute('CREATE INDEX idx_rgiid ON glacier_indicators(RGIID)')
    cursor.execute('CREATE INDEX idx_year ON glacier_indicators(year)')
    
    print("数据库表结构创建完成")
    
    # 读取第一个文件获取冰川基本信息（所有文件应该有相同的RGIID）
    first_file = list(indicator_files.values())[0]
    first_df = pd.read_excel(first_file)
    glacier_info = first_df[info_columns].drop_duplicates(subset=['RGIID'])
    
    # 插入冰川基本信息
    glacier_info.to_sql('glacier_info', conn, if_exists='append', index=False)
    print(f"已插入 {len(glacier_info)} 条冰川基本信息")
    
    # 处理每个指标文件
    all_data = {}
    
    for indicator_name, filename in indicator_files.items():
        print(f"\n处理指标: {indicator_name} ({filename})")
        df = pd.read_excel(filename)
        
        # 获取年份列
        year_cols = get_year_columns(df)
        print(f"  年份范围: {min(year_cols)} - {max(year_cols)}")
        
        # 将数据从宽格式转换为长格式
        for _, row in df.iterrows():
            rgiid = row['RGIID']
            if rgiid not in all_data:
                all_data[rgiid] = {}
            
            for year in year_cols:
                if year not in all_data[rgiid]:
                    all_data[rgiid][year] = {}
                
                value = row[year]
                # 只存储非空值
                if pd.notna(value):
                    all_data[rgiid][year][indicator_name] = float(value)
    
    # 将数据插入数据库
    print("\n正在插入指标数据...")
    records = []
    for rgiid, years_data in all_data.items():
        for year, indicators in years_data.items():
            record = {
                'RGIID': rgiid,
                'year': int(year),
                'ela': indicators.get('ela'),
                'Pa': indicators.get('Pa'),
                'T20': indicators.get('T20'),
                'Ta': indicators.get('Ta'),
                'Ts': indicators.get('Ts'),
                'v': indicators.get('v')
            }
            records.append(record)
    
    # 批量插入
    if records:
        records_df = pd.DataFrame(records)
        records_df.to_sql('glacier_indicators', conn, if_exists='append', index=False)
        print(f"已插入 {len(records)} 条指标数据记录")
    
    # 提交并关闭
    conn.commit()
    conn.close()
    
    print(f"\n数据库构建完成: {db_name}")
    
    # 验证数据
    verify_database(db_name)

def verify_database(db_name):
    """验证数据库数据"""
    conn = sqlite3.connect(db_name)
    
    # 统计信息
    cursor = conn.cursor()
    
    # 冰川数量
    cursor.execute('SELECT COUNT(*) FROM glacier_info')
    glacier_count = cursor.fetchone()[0]
    print(f"\n数据库统计:")
    print(f"  冰川数量: {glacier_count}")
    
    # 记录数量
    cursor.execute('SELECT COUNT(*) FROM glacier_indicators')
    record_count = cursor.fetchone()[0]
    print(f"  指标记录数: {record_count}")
    
    # 年份范围
    cursor.execute('SELECT MIN(year), MAX(year) FROM glacier_indicators')
    min_year, max_year = cursor.fetchone()
    print(f"  年份范围: {min_year} - {max_year}")
    
    # 每个指标的覆盖情况
    print(f"\n各指标数据覆盖情况:")
    for indicator in ['ela', 'Pa', 'T20', 'Ta', 'Ts', 'v']:
        cursor.execute(f'SELECT COUNT(*) FROM glacier_indicators WHERE {indicator} IS NOT NULL')
        count = cursor.fetchone()[0]
        print(f"  {indicator}: {count} 条记录")
    
    # 示例查询：显示某个冰川的所有年份数据
    print(f"\n示例数据（前5条记录）:")
    cursor.execute('''
        SELECT RGIID, year, ela, Pa, T20, Ta, Ts, v 
        FROM glacier_indicators 
        ORDER BY RGIID, year 
        LIMIT 5
    ''')
    for row in cursor.fetchall():
        print(f"  {row}")
    
    conn.close()

if __name__ == '__main__':
    print("开始构建冰川数据库...")
    print("=" * 80)
    build_database()
    print("=" * 80)
    print("完成！")

