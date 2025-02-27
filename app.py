import datetime
from flask import Blueprint, Flask, request, jsonify, render_template
import pandas as pd
import dmPython
from flask_cors import CORS
import sqlite3
import socket

app = Flask(__name__)
CORS(app)  # 应用CORS到你的Flask应用上

# 配置数据库连接参数
db_config = {
    'user': 'SYSDBA',
    'password': 'SYSDBA',
    'server': 'localhost',
    'port': 5236,
    'local_code': 1
}

# 创建数据库连接
def get_db_connection():
    conn = dmPython.connect(**db_config)
    return conn

# 注册蓝图
bp_input_teamId = Blueprint('team_award', __name__, url_prefix='/team_ward')  # 为高级检索注册蓝图，并分配url
bp_team_detail = Blueprint('team_details', __name__, url_prefix='/team_details')  # 为初级检索注册蓝图，并分配url
bp_generate = Blueprint('generate', __name__, url_prefix='/generate')
bp_operation_input = Blueprint('operation_input', __name__, url_prefix='/operation_input')

def init_db():
    c = conn.cursor()
    # 更新 users 表结构，添加 register_time 和 register_ip 字段
    c.execute('''
CREATE TABLE IF NOT EXISTS users (
    username VARCHAR(255) PRIMARY KEY,
    password VARCHAR(255),
    register_ip VARCHAR(255)
);
        )''')
    c.execute('''
CREATE TABLE IF NOT EXISTS managers (
username VARCHAR(255) PRIMARY KEY,
password VARCHAR(255)
);
              ''')
    # 创建管理员账号
    username = 'system_manager'
    password = '001'
    c.execute("SELECT * FROM managers WHERE username=?", (username,))
    manager = c.fetchone()
    # conn.close()
    if not manager:
        c.execute("INSERT INTO managers (username, password) VALUES (?, ?)", (username, password))
    conn.commit()

@bp_input_teamId.route('/index')  # 给高级检索分配路由，高级检索的输入框架，使用模板渲染，url为映射到本机的端口/advanced/index
def input_teamId_index():
    return render_template('team_award.html', error='')

@bp_team_detail.route('/index')  
def team_detail_index():
    return render_template('team_details.html', error='')

@bp_generate.route('/index')  
def generate_index():
    return render_template('generate.html', error='')

@bp_operation_input.route('/index')  
def operation_input_index():
    return render_template('operation_input.html', error='')


app.register_blueprint(bp_input_teamId)  # 登记初级检索的蓝图，保证可以使用
app.register_blueprint(bp_team_detail) 
app.register_blueprint(bp_generate)
app.register_blueprint(bp_operation_input)

@app.route('/')
def main():
    return render_template('login.html')


@app.route('/adminLogin', methods=['POST', 'GET'])
def admin_login():
    username = request.form['managerName']
    password = request.form['managerPassword']
    c = conn.cursor()
    manager = c.execute("SELECT * FROM managers WHERE username=? AND password=?", (username, password)).fetchone()
    if manager:
        response = {'error': 2, 'message': '管理员登录成功', 'data': {'username': username, 'password': password}}
        return render_template('index_manager.html')
    else:
        response = {'error': 400, 'message': '用户名或密码错误', 'data': {}}
        return jsonify(response)


# 普通用户登录路由
@app.route('/userLogin', methods=['POST', 'GET'])
def user_login():
    username = request.form['commonName']
    password = request.form['commonPassword']
    c = conn.cursor()
    user = c.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password)).fetchone()
    c.close()
    if user:
        return render_template('index.html')
    else:
        return jsonify({'error': 400, 'message': '用户名或密码错误', 'data': {}})


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        c = conn.cursor()
        try:
            c.execute("INSERT INTO users (username, password) VALUES (?, ?)",
                      (username, password))
            conn.commit()
            response = {
                'error': 0,
                'data': {'username': username},
                'message': '注册成功。'
            }
        except dmPython.IntegrityError:
            response = {

                'error': 400,
                'data': {},
                'message': '注册失败，用户名已存在。'
            }
        return jsonify(response)

    # GET 方法，返回注册表单页面
    return render_template('register.html')

@app.route('/home')
def home():
    # return render_template('index.html')
    return render_template('index.html')

# 管理员路由：导入 Excel 数据
@app.route('/admin/import_excel', methods=['POST'])
def import_excel():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    if file:
        # 使用 pandas 读取 Excel 文件
        df = pd.read_excel(file)
        
        # 在这里添加将数据导入数据库的逻辑
        # ...
        
        return jsonify({'message': 'Data imported successfully'}), 200
    
    return jsonify({'error': 'Failed to import data'}), 500

@app.route('/admin/operation', methods=['GET', 'POST'])
def operate():
    if request.method == 'POST':
        operation = request.form['operation']
        try:
            if cursor.execute(operation):
                return jsonify({'message': 'Operation completed successfully'}), 200
        except Exception as e:
            return jsonify({'error': 'Failed to complete operation'}), 500
    return


# 普通用户路由：查看团队获奖等级
@app.route('/user/team_award', methods=['GET', 'POST'])
def team_award():
    team_id = request.form["teamId"] 
    if not team_id:
        return jsonify({'error': 'Team ID is required'}), 400

    # 查看团队获奖等级
    cursor.execute(f"SELECT TeamID, Award, TeamName FROM Team WHERE TeamID = {team_id}")
    result = cursor.fetchone()
    
    if result:
        # return jsonify({'队伍号': result[0], '获奖情况': result[1]}), 200
        return render_template('team_award_output.html', team_id=result[0], award=result[1], team_name=result[2])
    else:
        return jsonify({'error': 'No award found for the given Team ID'}), 404
    

# 普通用户路由：查询各团队最终得分
@app.route('/user/team_score', methods=['GET', 'POST'])
def team_score():
    cursor.execute("""
    SELECT TeamID, TeamName, ProblemName, SCORE FROM Team 
    WHERE SCORE IS NOT NULL
    ORDER BY score DESC;
    """)
    data = cursor.fetchall()
    return render_template('team_score_output.html', data=data)

# 普通用户路由：查询获奖团队详情信息
@app.route('/user/team_details', methods=['GET', 'POST'])
def team_details():
    team_id = request.form['teamId']
    if not team_id:
        return jsonify({'error': 'Team ID is required'}), 400
    
    # 查询团队详情信息
    cursor.execute(f"""
    SELECT 
        Team.TeamID AS 团队编号, 
        Team.TeamName AS 团队名称, 
        Team.SCORE as 得分,
        Team.Award AS 所获奖项, 
        Team.Category AS 赛题类别, 
        Team.ProblemName AS 赛题名称, 
        Team.School AS 所属院校, 
        LISTAGG(Member.Name, ';') WITHIN GROUP (ORDER BY Member.Role) AS 团队成员姓名,
        Advisor.Name AS 指导教师姓名, 
        Advisor.Department AS 指导教师院校
    FROM 
        Team
    JOIN 
        Member ON Team.TeamID = Member.TeamID
    JOIN 
        Advisor ON Team.School = Advisor.Department
    WHERE 
        team.TeamID = {team_id}
    GROUP BY 
        Team.TeamID, Team.TeamName, Team.SCORE, Team.Award, Team.Category, Team.ProblemName, Team.School, Advisor.Name, Advisor.Department
             """)
    data = cursor.fetchone()
    team_memeber = data[7].split(';')
    team_memeber = ','.join(list(set(team_memeber)))
    if data:
        return render_template('team_details_output.html', data={'队伍号': data[0], '队伍名': data[1], '得分':data[2],
                        '获奖情况': data[3], '赛题类别' : data[4], '赛题名':data[5],
                        '所属学校':data[6], '团队成员':team_memeber, '指导老师':data[8]})
    else:
        return jsonify({'error': 'No award found for the given Team ID'}), 404

# 普通用户路由：生成电子证书信息表
@app.route('/user/generate_certificate', methods=['GET', 'POST'])
def generate_certificate():
    team_id = request.form['teamId']
    if not team_id:
        return jsonify({'error': 'Team ID is required'}), 400
    
    # 查询团队详情信息
    cursor.execute(f"""
    SELECT 
        Team.TeamID AS 团队编号, 
        Team.TeamName AS 团队名称, 
        Team.SCORE as 得分,
        Team.Award AS 所获奖项, 
        Team.Category AS 赛题类别, 
        Team.ProblemName AS 赛题名称, 
        Team.School AS 所属院校, 
        LISTAGG(Member.Name, ';') WITHIN GROUP (ORDER BY Member.Role) AS 团队成员姓名,
        Advisor.Name AS 指导教师姓名, 
        Advisor.Department AS 指导教师院校
    FROM 
        Team
    JOIN 
        Member ON Team.TeamID = Member.TeamID
    JOIN 
        Advisor ON Team.School = Advisor.Department
    WHERE 
        team.TeamID = {team_id}
    GROUP BY 
        Team.TeamID, Team.TeamName, Team.SCORE, Team.Award, Team.Category, Team.ProblemName, Team.School, Advisor.Name, Advisor.Department
             """)
    data = cursor.fetchone()
    team_memeber = data[7].split(';')
    team_memeber = ','.join(list(set(team_memeber)))
    if data:
        return render_template('generate_output.html', data={'队伍号': data[0], '队伍名': data[1], '得分':data[2],
                        '获奖情况': data[3], '赛题类别' : data[4], '赛题名':data[5],
                        '所属学校':data[6], '团队成员':team_memeber, '指导老师':data[8]})
    else:
        return jsonify({'error': 'No award found for the given Team ID'}), 404



if __name__ == '__main__':
    conn = get_db_connection()
    cursor = conn.cursor()
    # 获取局域网内可用的IP地址
    host = '0.0.0.0'
    port = 15000

    # 运行Flask应用
    app.run(host=host, port=port)