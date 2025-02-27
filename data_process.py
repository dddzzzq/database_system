import pandas as pd

def determine_award(score):
    if score >= 90:
        return "一等奖"
    elif 85 <= score < 90:
        return "二等奖"
    elif 78 <= score < 85:
        return "三等奖"
    else:
        return "没有获奖"


# Mapping of Excel sheet names to SQL table names and primary keysdef escape_string(value):
    # 转义字符串值，以防止SQL注入
def escape_string(value):
    # 转义字符串值，以防止SQL注入
    if value is None:
        return "NULL"
    # 替换单引号
    escaped_value = str(value).replace("'", "''")
    return f"'{escaped_value}'"

def generate_insert_statements(df, table_name, primary_key=0):
    statements = []
    for index, row in df.iterrows():
        columns = ", ".join(["NUM"] + list(row.index))
        values = ", ".join([str(index+1+primary_key)] + [escape_string(x) for x in row])
        statement = f"INSERT INTO {table_name} ({columns}) VALUES ({values});"
        statements.append(statement)
    
    return statements





# Paths to the uploaded Excel files
file_paths = {
    "A类赛题信息": "database/data/14届A类赛题信息.xlsx",
    "A类作品成绩明细": "database/data/14届A类作品成绩明细.xlsx",
    "B类作品成绩明细": "database/data/14届B类作品成绩明细.xlsx",
    "参赛团队": "database/data/14届参赛团队.xlsx",
    "参赛团队成员": "database/data/14届参赛团队成员.xlsx",
    "参赛指导老师": "database/data/14届参赛指导老师.xlsx",
    "评审专家": "database/data/14届评审专家.xlsx",
    "团队选题": "database/data/14届团队选题.xlsx"
}

# Read the content of each Excel file
dataframes = {}
for key, path in file_paths.items():
    dataframes[key] = pd.read_excel(path)

# 重新为每个表生成插入语句
sql_statements = []

# AProblem
Aproblem_df = dataframes["A类赛题信息"]
Aproblem_df.rename(columns={"赛题号": "ProblemID", "赛题名": "ProblemName", "出题企业": "Company"}, inplace=True)
sql_statements.extend(generate_insert_statements(Aproblem_df, "AProblem"))

# Expert
Expert_df = dataframes["评审专家"]
Expert_df.rename(columns={"专家编号": "ExpertID", "姓名": "Name", "单位": "Department"}, inplace=True)
sql_statements.extend(generate_insert_statements(Expert_df, "Expert"))

# Team
team_df = dataframes["参赛团队"]
team_df.rename(columns={"团队编号": "TeamID", "团队名称": "TeamName", "参赛报名院校": "School"}, inplace=True)
sql_statements.extend(generate_insert_statements(team_df, "Team"))

# Advisor
advisor_df = dataframes["参赛指导老师"]
advisor_df.rename(columns={"指导团队编号": "AdvisorID", "指导老师": "Name", "单位": "Department"}, inplace=True)
sql_statements.extend(generate_insert_statements(advisor_df, "Advisor"))

# Member
member_df = dataframes["参赛团队成员"]
member_df.rename(columns={"编号": "TeamID", "姓名": "Name", "性别": "Gender", "电话": "Phone", "就读大学": "University", "角色": "Role"}, inplace=True)
sql_statements.extend(generate_insert_statements(member_df, "Member"))

# ReviewInfo
review_info_a_df = dataframes["A类作品成绩明细"]
review_info_a_df.rename(columns={"评审ID": "ReviewID", "专家编号": "ExpertID", "赛题类型": "Category", "团队编号": "TeamID", "总分": "Score"}, inplace=True)
review_info_b_df = dataframes["B类作品成绩明细"]
review_info_b_df.rename(columns={"评审ID": "ReviewID", "专家编号": "ExpertID", "赛题类型": "Category", "团队编号": "TeamID", "总分": "Score"}, inplace=True)

sql_statements.extend(generate_insert_statements(review_info_a_df, "ReviewInfo"))
sql_statements.extend(generate_insert_statements(review_info_b_df, "ReviewInfo", primary_key=len(review_info_a_df)))

# 使用pd.concat来合并两个DataFrame
review_info_df = pd.concat([dataframes["A类作品成绩明细"], dataframes["B类作品成绩明细"]])

# 确保Score列是数值类型
review_info_df["Score"] = pd.to_numeric(review_info_df["Score"])

# 计算每个团队的平均分数
average_scores = review_info_df.groupby("TeamID")["Score"].mean().round(2)

# 应用函数来确定每个团队的获奖情况
awards = average_scores.apply(determine_award)

# 将所有的SQL语句保存到一个字符串中
sql_content = "\n".join(sql_statements)

# 合并平均分数和获奖情况为一个DataFrame
team_updates = pd.DataFrame({
    "TeamID": average_scores.index,
    "Score": average_scores.values,
    "Award": awards.values
})
# 生成更新Team表的SQL语句
update_statements = []

for _, row in team_updates.iterrows():
    update_statement = f"""
    UPDATE Team
    SET Score = {row['Score']}, Award = '{row['Award']}'
    WHERE TeamID = '{row['TeamID']}';
    """
    update_statements.append(update_statement)

# 将更新语句添加到之前的SQL语句中
sql_content = sql_content + "\n" + "\n".join(update_statements)


# 团队选题
team_selection_df = dataframes["团队选题"]
team_selection_df.rename(columns={"团队编号": "TeamID", "赛题名称": "ProblemName", "分类": "Category"}, inplace=True)

update_statements = []

for index, row in team_selection_df.iterrows():
    sql = f"UPDATE Team\n    SET ProblemName = '{row['ProblemName']}', Category = '{row['Category']}'\n    WHERE TeamID = '{row['TeamID']}';"
    update_statements.append(sql)

# 将更新语句添加到之前的SQL语句中
sql_content = sql_content + "\n" + "\n".join(update_statements)

# 定义SQL文件的保存路径
sql_file_path = "competition_management_system_data.sql"

# 将SQL内容写入文件
with open(sql_file_path, "w", encoding="utf-8") as file:
    file.write(sql_content)





