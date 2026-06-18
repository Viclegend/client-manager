import os
import io
import csv
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session, make_response, jsonify

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'netcred-secret-key-12345')

DB_PATH = '/app/data/system_v4.db' if os.path.exists('/.dockerenv') else './data/system_v4.db'

# 🌐 多語系字典檔 (i18n Dictionary)
LOCALES = {
    'zh-TW': {
        'sys_title': '連線資訊庫',
        'nav_brand': '🛡️ 連線資訊庫',
        'login_title': '系統管理員登入',
        'login_error': '帳號或密碼錯誤，請重試！',
        'btn_login': '登入',
        'btn_logout': '登出',
        'search_placeholder': '全域搜尋群組、設備、IP 或帳號...',
        'btn_export': '導出資料',
        'export_title': '匯出選項',
        'export_select': '請選擇要匯出的範圍：',
        'export_all': '全部群組 (完整備份)',
        'btn_confirm': '確認匯出',
        'btn_template': '下載範例',
        'btn_import': '匯入',
        'btn_browse': '選擇檔案',
        'no_file_chosen': '尚未選擇檔案',
        'sidebar_title': '群組與設備管理',
        'add_group_placeholder': '新群組 / 專案名稱...',
        'btn_add_group': '建立群組',
        'no_group_alert': '目前尚未建立任何設備群組。',
        'add_device_title': '新增設備至：',
        'field_device_name': '設備 / 節點名稱',
        'field_ip': 'IP 位址',
        'field_method': '連線方式',
        'field_username': '帳號',
        'field_password': '密碼',
        'btn_add_device': '新增設備',
        'btn_delete': '刪除',
        'confirm_delete_group': '確定要刪除整個群組及其底下的所有設備嗎？此動作無法復原！',
        'confirm_delete_device': '確定要刪除此設備連線資訊嗎？',
        'toggle_show': '[顯示]',
        'toggle_hide': '[隱藏]',
        'csv_header_error': '匯入失敗：CSV 標頭格式不符，請下載標準範例檔對照。',
        'csv_success': '成功匯入 {} 筆設備資料！',
        'msg_required': '請填寫此欄位！'
    },
    'zh-CN': {
        'sys_title': '连线信息库',
        'nav_brand': '🛡️ 连线信息库',
        'login_title': '系统管理员登录',
        'login_error': '账号或密码错误，请重试！',
        'btn_login': '登录',
        'btn_logout': '登出',
        'search_placeholder': '全局搜索分组、设备、IP 或账号...',
        'btn_export': '导出数据',
        'export_title': '导出选项',
        'export_select': '请选择要导出的范围：',
        'export_all': '所有分组 (完整备份)',
        'btn_confirm': '确认导出',
        'btn_template': '下载范例',
        'btn_import': '导入',
        'btn_browse': '选择文件',
        'no_file_chosen': '未选择文件',
        'sidebar_title': '分组与设备管理',
        'add_group_placeholder': '新分组 / 项目名称...',
        'btn_add_group': '建立分组',
        'no_group_alert': '目前尚未建立任何设备分组。',
        'add_device_title': '新增设备至：',
        'field_device_name': '设备 / 节点名称',
        'field_ip': 'IP 地址',
        'field_method': '连线方式',
        'field_username': '账号',
        'field_password': '密码',
        'btn_add_device': '新增设备',
        'btn_delete': '删除',
        'confirm_delete_group': '确定要删除整个分组及其底下的所有设备吗？此操作无法恢复！',
        'confirm_delete_device': '确定要删除此设备连线信息吗？',
        'toggle_show': '[显示]',
        'toggle_hide': '[隐藏]',
        'csv_header_error': '导入失败：CSV 表头格式不符，请下载标准范例档对照。',
        'csv_success': '成功导入 {} 条设备数据！',
        'msg_required': '请填写此字段！'
    },
    'en': {
        'sys_title': 'Connection Vault',
        'nav_brand': '🛡️ Connection Vault',
        'login_title': 'Administrator Login',
        'login_error': 'Invalid username or password, please try again.',
        'btn_login': 'Login',
        'btn_logout': 'Logout',
        'search_placeholder': 'Search groups, devices, IPs...',
        'btn_export': 'Export',
        'export_title': 'Export Options',
        'export_select': 'Select scope to export:',
        'export_all': 'All Groups (Full Backup)',
        'btn_confirm': 'Confirm Export',
        'btn_template': 'Template',
        'btn_import': 'Import CSV',
        'btn_browse': 'Browse...',
        'no_file_chosen': 'No file chosen',
        'sidebar_title': 'Groups & Devices',
        'add_group_placeholder': 'New Group / Project Name...',
        'btn_add_group': 'Create Group',
        'no_group_alert': 'No groups created yet.',
        'add_device_title': 'Add Device to: ',
        'field_device_name': 'Device / Node Name',
        'field_ip': 'IP Address',
        'field_method': 'Connection Method',
        'field_username': 'Username',
        'field_password': 'Password',
        'btn_add_device': 'Add Device',
        'btn_delete': 'Delete',
        'confirm_delete_group': 'Are you sure you want to delete this group and all its devices? This cannot be undone!',
        'confirm_delete_device': 'Are you sure you want to delete this device configuration?',
        'toggle_show': '[Show]',
        'toggle_hide': '[Hide]',
        'csv_header_error': 'Import Failed: Invalid CSV headers. Please use the official template.',
        'csv_success': 'Successfully imported {} device records!',
        'msg_required': 'Please fill out this field.'
    }
}

def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS groups (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS devices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            group_id INTEGER,
            name TEXT NOT NULL,
            ip TEXT,
            method TEXT,
            username TEXT,
            password TEXT,
            FOREIGN KEY (group_id) REFERENCES groups (id) ON DELETE CASCADE
        )
    ''')
    conn.commit()
    conn.close()

init_db()

@app.context_processor
def inject_locale():
    lang = request.cookies.get('lang', 'zh-TW')
    if lang not in LOCALES:
        lang = 'zh-TW'
    return {'lang': lang, 't': LOCALES[lang]}

@app.route('/set_lang/<lang_code>')
def set_lang(lang_code):
    redirect_to = request.args.get('next', url_for('index'))
    resp = redirect(redirect_to)
    if lang_code in LOCALES:
        resp.set_cookie('lang', lang_code, max_age=30*24*60*60)
    return resp

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        env_user = os.environ.get('ADMIN_USER', 'admin')
        env_pass = os.environ.get('ADMIN_PASS', 'admin123')
        
        if username == env_user and password == env_pass:
            session['logged_in'] = True
            return redirect(url_for('index'))
        else:
            return render_template('login.html', error=True)
    return render_template('login.html', error=False)

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login'))

@app.route('/')
def index():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
        
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('SELECT id, name FROM groups ORDER BY name ASC')
    groups_rows = cursor.fetchall()
    
    groups_data = []
    for g_id, g_name in groups_rows:
        cursor.execute('''
            SELECT id, name, ip, method, username, password 
            FROM devices WHERE group_id = ? ORDER BY name ASC
        ''', (g_id,))
        devices_rows = cursor.fetchall()
        devices = []
        for d_id, d_name, d_ip, d_method, d_user, d_pass in devices_rows:
            devices.append({
                'id': d_id, 'name': d_name, 'ip': d_ip,
                'method': d_method, 'username': d_user, 'password': d_pass
            })
        groups_data.append({'id': g_id, 'name': g_name, 'devices': devices})
        
    conn.close()
    return render_template('index.html', groups=groups_data)

@app.route('/add_group', methods=['POST'])
def add_group():
    if not session.get('logged_in'): return redirect(url_for('login'))
    name = request.form.get('group_name', '').strip()
    if name:
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute('INSERT INTO groups (name) VALUES (?)', (name,))
            conn.commit()
        except sqlite3.IntegrityError:
            pass
        finally:
            conn.close()
    return redirect(url_for('index'))

@app.route('/delete_group/<int:group_id>', methods=['POST'])
def delete_group(group_id):
    if not session.get('logged_in'): return redirect(url_for('login'))
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM devices WHERE group_id = ?', (group_id,))
    cursor.execute('DELETE FROM groups WHERE id = ?', (group_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

@app.route('/add_device/<int:group_id>', methods=['POST'])
def add_device(group_id):
    if not session.get('logged_in'): return redirect(url_for('login'))
    name = request.form.get('device_name', '').strip()
    ip = request.form.get('ip', '').strip()
    method = request.form.get('method', '').strip()
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '').strip()
    
    if name:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO devices (group_id, name, ip, method, username, password)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (group_id, name, ip, method, username, password))
        conn.commit()
        conn.close()
    return redirect(url_for('index'))

@app.route('/download_template')
def download_template():
    if not session.get('logged_in'): return redirect(url_for('login'))
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    lang = request.cookies.get('lang', 'zh-TW')
    if lang == 'en':
        writer.writerow(['Group Name', 'Device Name', 'IP Address', 'Connection Method', 'Username', 'Password'])
        writer.writerow(['Lab_Cluster', 'Core_Switch_01', '192.168.1.254', 'SSH', 'admin', 'SecuredPass123'])
    elif lang == 'zh-CN':
        writer.writerow(['群组名称', '设备名称', 'IP地址', '连线方式', '账号', '密码'])
        writer.writerow(['测试机房_A', '核心交换机', '192.168.1.254', 'SSH', 'admin', 'SecuredPass123'])
    else:
        writer.writerow(['群組名稱', '設備名稱', 'IP位址', '連線方式', '帳號', '密碼'])
        writer.writerow(['測試機房_A', '核心交換機', '192.168.1.254', 'SSH', 'admin', 'SecuredPass123'])
        
    csv_data = "\ufeff" + output.getvalue()
    
    response = make_response(csv_data)
    response.headers["Content-Disposition"] = "attachment; filename=netcred_template.csv"
    response.headers["Content-Type"] = "text/csv; charset=utf-8"
    return response

@app.route('/export_data')
def export_data():
    if not session.get('logged_in'): return redirect(url_for('login'))
    
    group_id = request.args.get('group_id', 'all')
    output = io.StringIO()
    writer = csv.writer(output)
    
    lang = request.cookies.get('lang', 'zh-TW')
    if lang == 'en':
        writer.writerow(['Group Name', 'Device Name', 'IP Address', 'Connection Method', 'Username', 'Password'])
    elif lang == 'zh-CN':
        writer.writerow(['群组名称', '设备名称', 'IP地址', '连线方式', '账号', '密码'])
    else:
        writer.writerow(['群組名稱', '設備名稱', 'IP位址', '連線方式', '帳號', '密碼'])
        
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    if group_id != 'all' and group_id.isdigit():
        cursor.execute('''
            SELECT g.name, d.name, d.ip, d.method, d.username, d.password
            FROM devices d
            JOIN groups g ON d.group_id = g.id
            WHERE g.id = ?
            ORDER BY g.name ASC, d.name ASC
        ''', (int(group_id),))
    else:
        cursor.execute('''
            SELECT g.name, d.name, d.ip, d.method, d.username, d.password
            FROM devices d
            JOIN groups g ON d.group_id = g.id
            ORDER BY g.name ASC, d.name ASC
        ''')
        
    rows = cursor.fetchall()
    for row in rows:
        writer.writerow(row)
    conn.close()
    
    csv_data = "\ufeff" + output.getvalue()
    response = make_response(csv_data)
    response.headers["Content-Disposition"] = "attachment; filename=netcred_export.csv"
    response.headers["Content-Type"] = "text/csv; charset=utf-8"
    return response

@app.route('/import_csv', methods=['POST'])
def import_csv():
    if not session.get('logged_in'): return redirect(url_for('login'))
    
    file = request.files.get('csv_file')
    if not file or file.filename == '':
        return redirect(url_for('index'))
        
    try:
        stream = io.StringIO(file.stream.read().decode("utf-8-sig"), newline=None)
        csv_reader = csv.reader(stream)
        
        headers = next(csv_reader, None)
        if not headers or len(headers) < 2:
            return render_template('index.html', error_msg=LOCALES[request.cookies.get('lang', 'zh-TW')]['csv_header_error'])
            
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        for row in csv_reader:
            if not row or len(row) < 2:
                continue
            
            g_name = row[0].strip()
            d_name = row[1].strip()
            d_ip = row[2].strip() if len(row) > 2 else ''
            d_method = row[3].strip() if len(row) > 3 else ''
            d_user = row[4].strip() if len(row) > 4 else ''
            d_pass = row[5].strip() if len(row) > 5 else ''
            
            if not g_name or not d_name:
                continue
                
            cursor.execute('SELECT id FROM groups WHERE name = ?', (g_name,))
            g_row = cursor.fetchone()
            if g_row:
                group_id = g_row[0]
            else:
                cursor.execute('INSERT INTO groups (name) VALUES (?)', (g_name,))
                group_id = cursor.lastrowid
                
            cursor.execute('SELECT id FROM devices WHERE group_id = ? AND name = ?', (group_id, d_name))
            d_row = cursor.fetchone()
            if d_row:
                cursor.execute('''
                    UPDATE devices SET ip = ?, method = ?, username = ?, password = ?
                    WHERE id = ?
                ''', (d_ip, d_method, d_user, d_pass, d_row[0]))
            else:
                cursor.execute('''
                    INSERT INTO devices (group_id, name, ip, method, username, password)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (group_id, d_name, d_ip, d_method, d_user, d_pass))
            
        conn.commit()
        conn.close()
        return redirect(url_for('index'))
    except Exception as e:
        return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)