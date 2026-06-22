import os
import io
import csv
import sqlite3
from datetime import timedelta
from flask import Flask, render_template, request, redirect, url_for, session, make_response

app = Flask(__name__)

# 安全金鑰與會話生命週期控管
app.secret_key = os.environ.get('SECRET_KEY', 'netcred-secret-key-12345')
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=30)  # 🌟 核心修正：30分鐘不活動自動過期
app.config['SESSION_REFRESH_EACH_REQUEST'] = True                # 每次讀取自動刷新計時，確保連續使用不斷線

DB_PATH = '/app/data/connection_vault_v6.db' if os.path.exists('/.dockerenv') else './data/connection_vault_v6.db'

LOCALES = {
    'zh-TW': {
        'sys_title': '連線資訊庫',
        'nav_brand': '🛡️ Connection Vault',
        'login_title': '系統管理員登入',
        'login_error': '帳號或密碼錯誤，請重試！',
        'btn_login': '登入',
        'btn_logout': '登出',
        'btn_export': '導出資料',
        'export_title': '匯出選項',
        'export_select': '請選擇要匯出的範圍：',
        'export_all': '全部群組 (完整備份)',
        'btn_confirm': '確認',
        'btn_template': '下載範例',
        'btn_import': '匯入',
        'btn_browse': '選擇檔案',
        'no_file_chosen': '尚未選擇檔案',
        'sidebar_title': '🏢 群組目錄',
        'add_group_title': '建立主群組',
        'add_group_placeholder': '群組名稱...',
        'btn_add_group': '建立',
        'no_group_selected': '👈 請從左側選擇一個群組以檢視或新增設備。',
        'btn_add_device': '新增設備',
        'btn_add_subgroup': '新增子群組',
        'btn_batch_move': '批次移動',
        'btn_edit': '編輯',
        'btn_delete': '刪除',
        'field_name': '名稱',
        'field_remark': '備註',
        'field_device_name': '設備名稱',
        'field_ip': 'IP 位址',
        'field_method': '連線方式',
        'field_username': '帳號',
        'field_password': '密碼',
        'field_target_group': '選擇目標群組',
        'confirm_delete_group': '確定要刪除此群組嗎？\n⚠️ 警告：這將會連帶刪除底下「所有的子群組」與「設備」！',
        'confirm_delete_device': '確定要刪除此設備連線資訊嗎？',
        'toggle_show': '[顯示]',
        'toggle_hide': '[隱藏]',
        'msg_required': '請填寫此欄位！',
        'edit_group_title': '編輯群組',
        'edit_device_title': '編輯設備資訊',
        'move_device_title': '移動已選設備'
    },
    'zh-CN': {
        'sys_title': '连线信息库',
        'nav_brand': '🛡️ Connection Vault',
        'login_title': '系统管理员登录',
        'login_error': '账号或密码错误，请重试！',
        'btn_login': '登录',
        'btn_logout': '登出',
        'btn_export': '导出数据',
        'export_title': '导出选项',
        'export_select': '请选择要导出的范围：',
        'export_all': '所有分组 (完整备份)',
        'btn_confirm': '确认',
        'btn_template': '下载范例',
        'btn_import': '导入',
        'btn_browse': '选择文件',
        'no_file_chosen': '未选择文件',
        'sidebar_title': '🏢 分组目录',
        'add_group_title': '建立主分组',
        'add_group_placeholder': '分组名称...',
        'btn_add_group': '建立',
        'no_group_selected': '👈 请从左侧选择一个分组以查看或新增设备。',
        'btn_add_device': '新增设备',
        'btn_add_subgroup': '新增子分组',
        'btn_batch_move': '批量移动',
        'btn_edit': '编辑',
        'btn_delete': '删除',
        'field_name': '名称',
        'field_remark': '备注',
        'field_device_name': '设备名称',
        'field_ip': 'IP 地址',
        'field_method': '连线方式',
        'field_username': '账号',
        'field_password': '密码',
        'field_target_group': '选择目标分组',
        'confirm_delete_group': '确定要删除此分组吗？\n⚠️ 警告：这将会连带删除底下「所有的子分组」与「设备」！',
        'confirm_delete_device': '确定要删除此设备连线信息吗？',
        'toggle_show': '[显示]',
        'toggle_hide': '[隐藏]',
        'msg_required': '请填写此字段！',
        'edit_group_title': '编辑分组',
        'edit_device_title': '编辑设备信息',
        'move_device_title': '移动已选设备'
    },
    'en': {
        'sys_title': 'Connection Vault',
        'nav_brand': '🛡️ Connection Vault',
        'login_title': 'Administrator Login',
        'login_error': 'Invalid credentials, please try again.',
        'btn_login': 'Login',
        'btn_logout': 'Logout',
        'btn_export': 'Export',
        'export_title': 'Export Options',
        'export_select': 'Select scope to export:',
        'export_all': 'All Groups (Full Backup)',
        'btn_confirm': 'Confirm',
        'btn_template': 'Template',
        'btn_import': 'Import CSV',
        'btn_browse': 'Browse...',
        'no_file_chosen': 'No file chosen',
        'sidebar_title': '🏢 Directory',
        'add_group_title': 'Add Root Group',
        'add_group_placeholder': 'Group Name...',
        'btn_add_group': 'Create',
        'no_group_selected': '👈 Select a group from the left menu to view or add devices.',
        'btn_add_device': 'Add Device',
        'btn_add_subgroup': 'Add Sub-group',
        'btn_batch_move': 'Move Selected',
        'btn_edit': 'Edit',
        'btn_delete': 'Delete',
        'field_name': 'Name',
        'field_remark': 'Remark',
        'field_device_name': 'Device Name',
        'field_ip': 'IP Address',
        'field_method': 'Method',
        'field_username': 'Username',
        'field_password': 'Password',
        'field_target_group': 'Target Group',
        'confirm_delete_group': 'Delete this group?\n⚠️ WARNING: This will cascade delete ALL sub-groups and devices within it!',
        'confirm_delete_device': 'Delete this device?',
        'toggle_show': '[Show]',
        'toggle_hide': '[Hide]',
        'msg_required': 'This field is required!',
        'edit_group_title': 'Edit Group',
        'edit_device_title': 'Edit Device',
        'move_device_title': 'Move Selected Devices'
    }
}

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS groups (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            parent_id INTEGER DEFAULT NULL,
            name TEXT NOT NULL,
            remark TEXT DEFAULT '',
            FOREIGN KEY (parent_id) REFERENCES groups (id) ON DELETE CASCADE
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS devices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            group_id INTEGER,
            name TEXT NOT NULL,
            ip TEXT DEFAULT '',
            method TEXT DEFAULT '',
            username TEXT DEFAULT '',
            password TEXT DEFAULT '',
            remark TEXT DEFAULT '',
            FOREIGN KEY (group_id) REFERENCES groups (id) ON DELETE CASCADE
        )
    ''')
    conn.commit()
    conn.close()

init_db()

def get_full_group_path(group_id, group_dict):
    path_parts = []
    curr = group_dict.get(group_id)
    while curr:
        path_parts.append(curr['name'])
        curr = group_dict.get(curr['parent_id'])
    path_parts.reverse()
    return ' / '.join(path_parts)

@app.context_processor
def inject_locale():
    lang = request.cookies.get('lang', 'zh-TW')
    if lang not in LOCALES: lang = 'zh-TW'
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
        if username == os.environ.get('ADMIN_USER', 'admin') and password == os.environ.get('ADMIN_PASS', 'admin123'):
            session.permanent = True  # 🌟 核心修正：啟用自定義的安全超時生命週期
            session['logged_in'] = True
            return redirect(url_for('index'))
        return render_template('login.html', error=True)
    return render_template('login.html', error=False)

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login'))

@app.route('/')
def index():
    if not session.get('logged_in'): return redirect(url_for('login'))
    
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('SELECT id, parent_id, name, remark FROM groups ORDER BY name ASC')
    all_groups = cursor.fetchall()
    
    group_dict = {g[0]: {'id': g[0], 'parent_id': g[1], 'name': g[2], 'remark': g[3], 'children': []} for g in all_groups}
    root_groups = []
    
    for g_id, g in group_dict.items():
        if g['parent_id'] and g['parent_id'] in group_dict:
            group_dict[g['parent_id']]['children'].append(g)
        else:
            root_groups.append(g)
            
    selected_group_id = request.args.get('group_id')
    selected_group = None
    devices = []
    
    if selected_group_id and int(selected_group_id) in group_dict:
        selected_group = group_dict[int(selected_group_id)]
        cursor.execute('''
            SELECT id, name, ip, method, username, password, remark 
            FROM devices WHERE group_id = ? ORDER BY name ASC
        ''', (selected_group['id'],))
        devices_rows = cursor.fetchall()
        for d in devices_rows:
            devices.append({'id': d[0], 'name': d[1], 'ip': d[2], 'method': d[3], 'username': d[4], 'password': d[5], 'remark': d[6]})
            
    conn.close()
    return render_template('index.html', root_groups=root_groups, all_groups=all_groups, selected_group=selected_group, devices=devices)

@app.route('/add_group', methods=['POST'])
def add_group():
    if not session.get('logged_in'): return redirect(url_for('login'))
    name = request.form.get('group_name', '').strip()
    remark = request.form.get('remark', '').strip()
    parent_id = request.form.get('parent_id')
    
    if name:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('INSERT INTO groups (name, remark, parent_id) VALUES (?, ?, ?)', 
                       (name, remark, parent_id if parent_id else None))
        new_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return redirect(url_for('index', group_id=new_id))
    return redirect(url_for('index'))

@app.route('/edit_group/<int:group_id>', methods=['POST'])
def edit_group(group_id):
    if not session.get('logged_in'): return redirect(url_for('login'))
    name = request.form.get('group_name', '').strip()
    remark = request.form.get('remark', '').strip()
    if name:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('UPDATE groups SET name = ?, remark = ? WHERE id = ?', (name, remark, group_id))
        conn.commit()
        conn.close()
    return redirect(url_for('index', group_id=group_id))

@app.route('/delete_group/<int:group_id>', methods=['POST'])
def delete_group(group_id):
    if not session.get('logged_in'): return redirect(url_for('login'))
    conn = get_db()
    cursor = conn.cursor()
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
    remark = request.form.get('remark', '').strip()
    
    if name:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO devices (group_id, name, ip, method, username, password, remark)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (group_id, name, ip, method, username, password, remark))
        conn.commit()
        conn.close()
    return redirect(url_for('index', group_id=group_id))

@app.route('/edit_device/<int:device_id>', methods=['POST'])
def edit_device(device_id):
    if not session.get('logged_in'): return redirect(url_for('login'))
    name = request.form.get('device_name', '').strip()
    ip = request.form.get('ip', '').strip()
    method = request.form.get('method', '').strip()
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '').strip()
    remark = request.form.get('remark', '').strip()
    group_id = request.args.get('return_group_id')
    
    if name:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE devices SET name=?, ip=?, method=?, username=?, password=?, remark=? WHERE id=?
        ''', (name, ip, method, username, password, remark, device_id))
        conn.commit()
        conn.close()
    return redirect(url_for('index', group_id=group_id))

@app.route('/delete_device/<int:device_id>', methods=['POST'])
def delete_device(device_id):
    if not session.get('logged_in'): return redirect(url_for('login'))
    group_id = request.args.get('return_group_id')
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM devices WHERE id = ?', (device_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('index', group_id=group_id))

@app.route('/batch_move', methods=['POST'])
def batch_move():
    if not session.get('logged_in'): return redirect(url_for('login'))
    target_group_id = request.form.get('target_group_id')
    device_ids_str = request.form.get('device_ids', '')
    current_group_id = request.form.get('current_group_id')
    
    if target_group_id and device_ids_str:
        d_ids = [int(x) for x in device_ids_str.split(',') if x.isdigit()]
        if d_ids:
            conn = get_db()
            cursor = conn.cursor()
            placeholders = ','.join('?' * len(d_ids))
            query = f'UPDATE devices SET group_id = ? WHERE id IN ({placeholders})'
            cursor.execute(query, [target_group_id] + d_ids)
            conn.commit()
            conn.close()
            return redirect(url_for('index', group_id=target_group_id))
    return redirect(url_for('index', group_id=current_group_id))

@app.route('/download_template')
def download_template():
    if not session.get('logged_in'): return redirect(url_for('login'))
    output = io.StringIO()
    writer = csv.writer(output)
    lang = request.cookies.get('lang', 'zh-TW')
    
    if lang == 'en':
        writer.writerow(['Group Path', 'Group Remark', 'Device Name', 'IP Address', 'Connection Method', 'Username', 'Password', 'Device Remark'])
        writer.writerow(['Headquarters / Server Room A', 'Main Office', 'Core_Switch_01', '192.168.1.254', 'SSH', 'admin', 'Pass123', 'Core Network'])
    elif lang == 'zh-CN':
        writer.writerow(['分组路径', '分组备注', '设备名称', 'IP地址', '连线方式', '账号', '密码', '设备备注'])
        writer.writerow(['台北总部 / 机房A', '主干网段', '核心交换机', '192.168.1.254', 'SSH', 'admin', 'Pass123', '核心网络'])
    else:
        writer.writerow(['群組路徑', '群組備註', '設備名稱', 'IP位址', '連線方式', '帳號', '密碼', '設備備註'])
        writer.writerow(['台北總部 / 機房A', '主幹網段', '核心交換機', '192.168.1.254', 'SSH', 'admin', 'Pass123', '核心網路'])
        
    response = make_response("\ufeff" + output.getvalue())
    response.headers["Content-Disposition"] = "attachment; filename=connection_vault_template.csv"
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
        writer.writerow(['Group Path', 'Group Remark', 'Device Name', 'IP Address', 'Connection Method', 'Username', 'Password', 'Device Remark'])
    elif lang == 'zh-CN':
        writer.writerow(['分组路径', '分组备注', '设备名称', 'IP地址', '连线方式', '账号', '密码', '设备备注'])
    else:
        writer.writerow(['群組路徑', '群組備註', '設備名稱', 'IP位址', '連線方式', '帳號', '密碼', '設備備註'])
        
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('SELECT id, parent_id, name, remark FROM groups')
    group_dict = {r[0]: {'id': r[0], 'parent_id': r[1], 'name': r[2], 'remark': r[3]} for r in cursor.fetchall()}
    
    if group_id != 'all' and group_id.isdigit():
        cursor.execute('''
            SELECT group_id, name, ip, method, username, password, remark 
            FROM devices WHERE group_id = ? ORDER BY name ASC
        ''', (int(group_id),))
    else:
        cursor.execute('''
            SELECT group_id, name, ip, method, username, password, remark 
            FROM devices ORDER BY group_id ASC, name ASC
        ''')
        
    for row in cursor.fetchall():
        g_id, d_name, d_ip, d_method, d_user, d_pass, d_remark = row
        if g_id in group_dict:
            full_path = get_full_group_path(g_id, group_dict)
            g_remark = group_dict[g_id]['remark']
            writer.writerow([full_path, g_remark, d_name, d_ip, d_method, d_user, d_pass, d_remark])
            
    conn.close()
    response = make_response("\ufeff" + output.getvalue())
    response.headers["Content-Disposition"] = "attachment; filename=connection_vault_export.csv"
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
        if not headers: return redirect(url_for('index'))
        
        is_old_format = len(headers) < 8
        conn = get_db()
        cursor = conn.cursor()
        
        for row in csv_reader:
            if not row or len(row) < 2: continue
            
            if is_old_format:
                g_path_str = row[0].strip()
                g_remark = ''
                d_name = row[1].strip()
                d_ip = row[2].strip() if len(row) > 2 else ''
                d_method = row[3].strip() if len(row) > 3 else ''
                d_user = row[4].strip() if len(row) > 4 else ''
                d_pass = row[5].strip() if len(row) > 5 else ''
                d_remark = ''
            else:
                g_path_str = row[0].strip()
                g_remark = row[1].strip() if len(row) > 1 else ''
                d_name = row[2].strip() if len(row) > 2 else ''
                d_ip = row[3].strip() if len(row) > 3 else ''
                d_method = row[4].strip() if len(row) > 4 else ''
                d_user = row[5].strip() if len(row) > 5 else ''
                d_pass = row[6].strip() if len(row) > 6 else ''
                d_remark = row[7].strip() if len(row) > 7 else ''
            
            if not g_path_str or not d_name: continue
            
            path_parts = [p.strip() for p in g_path_str.split('/') if p.strip()]
            if not path_parts: continue
            
            parent_id = None
            for i, part in enumerate(path_parts):
                is_last_leaf = (i == len(path_parts) - 1)
                
                if parent_id is None:
                    cursor.execute('SELECT id FROM groups WHERE name = ? AND parent_id IS NULL', (part,))
                else:
                    cursor.execute('SELECT id FROM groups WHERE name = ? AND parent_id = ?', (part, parent_id))
                
                g_row = cursor.fetchone()
                if g_row:
                    group_id = g_row[0]
                    if is_last_leaf and not is_old_format and g_remark:
                        cursor.execute('UPDATE groups SET remark=? WHERE id=?', (g_remark, group_id))
                else:
                    cursor.execute('INSERT INTO groups (name, remark, parent_id) VALUES (?, ?, ?)', 
                                   (part, g_remark if is_last_leaf else '', parent_id))
                    group_id = cursor.lastrowid
                
                parent_id = group_id
            
            cursor.execute('SELECT id FROM devices WHERE group_id = ? AND name = ?', (group_id, d_name))
            d_row = cursor.fetchone()
            if d_row:
                cursor.execute('''
                    UPDATE devices SET ip=?, method=?, username=?, password=?, remark=? WHERE id=?
                ''', (d_ip, d_method, d_user, d_pass, d_remark, d_row[0]))
            else:
                cursor.execute('''
                    INSERT INTO devices (group_id, name, ip, method, username, password, remark)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (group_id, d_name, d_ip, d_method, d_user, d_pass, d_remark))
            
        conn.commit()
        conn.close()
    except Exception as e:
        print("Import Closed Loop Error:", e)
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)