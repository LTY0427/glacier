import sqlite3
import pandas as pd
import sys
import os

def query_glacier_data(rgiid=None, year=None, output_format='table'):
    """
    查询冰川指标数据
    
    参数:
        rgiid: 冰川ID，如果为None则查询所有冰川
        year: 年份，如果为None则查询所有年份
        output_format: 输出格式，'table'（表格）或'csv'（CSV文件）
    """
    conn = sqlite3.connect('glacier_data.db')
    
    # 构建查询SQL
    query = '''
        SELECT 
            gi.RGIID,
            gi.X,
            gi.Y,
            gi.Area,
            gi.REGION,
            gi.TYPE,
            gd.year,
            gd.ela,
            gd.Pa,
            gd.T20,
            gd.Ta,
            gd.Ts,
            gd.v
        FROM glacier_indicators gd
        JOIN glacier_info gi ON gd.RGIID = gi.RGIID
        WHERE 1=1
    '''
    
    params = []
    if rgiid:
        query += ' AND gd.RGIID = ?'
        params.append(rgiid)
    
    if year:
        query += ' AND gd.year = ?'
        params.append(year)
    
    query += ' ORDER BY gd.RGIID, gd.year'
    
    # 执行查询
    df = pd.read_sql_query(query, conn, params=params)
    
    conn.close()
    
    # 输出结果
    if output_format == 'csv':
        filename = f'glacier_data'
        if rgiid:
            filename += f'_{rgiid}'
        if year:
            filename += f'_{year}'
        filename += '.csv'
        df.to_csv(filename, index=False, encoding='utf-8-sig')
        print(f"数据已导出到: {filename}")
        print(f"共 {len(df)} 条记录")
    else:
        print(f"\n查询结果（共 {len(df)} 条记录）:")
        print("=" * 120)
        pd.set_option('display.max_columns', None)
        pd.set_option('display.width', None)
        pd.set_option('display.max_colwidth', 20)
        print(df.to_string(index=False))
        print("=" * 120)
    
    return df

def list_glaciers(limit=10):
    """列出所有冰川ID"""
    conn = sqlite3.connect('glacier_data.db')
    cursor = conn.cursor()
    cursor.execute('SELECT DISTINCT RGIID FROM glacier_info ORDER BY RGIID LIMIT ?', (limit,))
    glaciers = [row[0] for row in cursor.fetchall()]
    conn.close()
    return glaciers

def export_all_data(output_format='csv', filename=None):
    """
    导出数据库中的所有数据
    
    参数:
        output_format: 输出格式，'csv' 或 'excel'
        filename: 输出文件名，如果为None则自动生成
    """
    conn = sqlite3.connect('glacier_data.db')
    
    # 查询所有数据
    query = '''
        SELECT 
            gi.RGIID,
            gi.X,
            gi.Y,
            gi.Area,
            gi.DC,
            gi.LTG,
            gi.REGION,
            gi.TYPE,
            gi.S50,
            gi.S100,
            gi.M50,
            gi.M100,
            gd.year,
            gd.ela,
            gd.Pa,
            gd.T20,
            gd.Ta,
            gd.Ts,
            gd.v
        FROM glacier_indicators gd
        JOIN glacier_info gi ON gd.RGIID = gi.RGIID
        ORDER BY gd.RGIID, gd.year
    '''
    
    print("正在读取数据库...")
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    print(f"共读取 {len(df)} 条记录")
    
    # 生成文件名
    if filename is None:
        from datetime import datetime
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        if output_format == 'excel':
            filename = f'glacier_data_all_{timestamp}.xlsx'
        else:
            filename = f'glacier_data_all_{timestamp}.csv'
    
    # 导出数据
    print(f"正在导出到 {filename}...")
    if output_format == 'excel':
        df.to_excel(filename, index=False, engine='openpyxl')
    else:
        df.to_csv(filename, index=False, encoding='utf-8-sig')
    
    print(f"[成功] 数据已成功导出到: {filename}")
    print(f"  记录数: {len(df)}")
    print(f"  列数: {len(df.columns)}")
    print(f"  文件大小: {os.path.getsize(filename) / 1024 / 1024:.2f} MB")
    
    return filename

def get_statistics():
    """获取数据库统计信息"""
    conn = sqlite3.connect('glacier_data.db')
    cursor = conn.cursor()
    
    print("\n数据库统计信息:")
    print("=" * 80)
    
    # 冰川数量
    cursor.execute('SELECT COUNT(*) FROM glacier_info')
    glacier_count = cursor.fetchone()[0]
    print(f"冰川总数: {glacier_count}")
    
    # 记录数量
    cursor.execute('SELECT COUNT(*) FROM glacier_indicators')
    record_count = cursor.fetchone()[0]
    print(f"指标记录总数: {record_count}")
    
    # 年份范围
    cursor.execute('SELECT MIN(year), MAX(year) FROM glacier_indicators')
    min_year, max_year = cursor.fetchone()
    print(f"年份范围: {min_year} - {max_year}")
    
    # 每个指标的覆盖情况
    print(f"\n各指标数据覆盖情况:")
    for indicator in ['ela', 'Pa', 'T20', 'Ta', 'Ts', 'v']:
        cursor.execute(f'SELECT COUNT(*) FROM glacier_indicators WHERE {indicator} IS NOT NULL')
        count = cursor.fetchone()[0]
        cursor.execute(f'SELECT COUNT(DISTINCT RGIID) FROM glacier_indicators WHERE {indicator} IS NOT NULL')
        glacier_count_ind = cursor.fetchone()[0]
        print(f"  {indicator:4s}: {count:6d} 条记录, {glacier_count_ind:4d} 个冰川")
    
    conn.close()

if __name__ == '__main__':
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == 'stats':
            get_statistics()
        elif command == 'list':
            limit = int(sys.argv[2]) if len(sys.argv) > 2 else 10
            glaciers = list_glaciers(limit)
            print(f"\n前 {limit} 个冰川ID:")
            for g in glaciers:
                print(f"  {g}")
        elif command == 'query':
            rgiid = sys.argv[2] if len(sys.argv) > 2 else None
            year = int(sys.argv[3]) if len(sys.argv) > 3 else None
            output = sys.argv[4] if len(sys.argv) > 4 else 'table'
            query_glacier_data(rgiid, year, output)
        elif command == 'export':
            output_format = sys.argv[2] if len(sys.argv) > 2 else 'csv'
            filename = sys.argv[3] if len(sys.argv) > 3 else None
            export_all_data(output_format, filename)
        else:
            print("用法:")
            print("  python query_database.py stats                    # 显示统计信息")
            print("  python query_database.py list [数量]              # 列出冰川ID")
            print("  python query_database.py query [RGIID] [年份] [格式]  # 查询数据")
            print("  python query_database.py export [格式] [文件名]      # 导出所有数据")
            print("  格式: csv 或 excel")
    else:
        # 交互式查询
        print("冰川数据库查询工具")
        print("=" * 80)
        print("\n1. 查看统计信息")
        print("2. 列出冰川ID")
        print("3. 查询数据")
        print("4. 导出所有数据")
        print("5. 退出")
        
        while True:
            choice = input("\n请选择操作 (1-5): ").strip()
            
            if choice == '1':
                get_statistics()
            elif choice == '2':
                limit = input("显示数量 (默认10): ").strip()
                limit = int(limit) if limit else 10
                glaciers = list_glaciers(limit)
                print(f"\n前 {limit} 个冰川ID:")
                for g in glaciers:
                    print(f"  {g}")
            elif choice == '3':
                rgiid = input("输入冰川ID (留空查询所有): ").strip()
                rgiid = rgiid if rgiid else None
                year = input("输入年份 (留空查询所有): ").strip()
                year = int(year) if year else None
                output = input("输出格式 (table/csv, 默认table): ").strip()
                output = output if output else 'table'
                query_glacier_data(rgiid, year, output)
            elif choice == '4':
                output_format = input("输出格式 (csv/excel, 默认csv): ").strip()
                output_format = output_format if output_format else 'csv'
                filename = input("文件名 (留空自动生成): ").strip()
                filename = filename if filename else None
                export_all_data(output_format, filename)
            elif choice == '5':
                break
            else:
                print("无效选择，请重新输入")

