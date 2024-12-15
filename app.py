import os
import sqlite3
from flask import Flask, request, redirect, url_for, render_template
from datetime import datetime, timedelta
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

app = Flask(__name__)

DB_PATH = "db/expenses.db"
ALLOWED_CATEGORIES = ["食費", "交通費", "娯楽費", "雑費"]
MAX_AMOUNT = 10_000_000  # 金額上限

def init_db():
    """
    DB初期化関数。
    schema.sqlを実行してIF NOT EXISTSテーブル作成を試みる。
    """
    conn = sqlite3.connect(DB_PATH)
    with open("db/schema.sql", "r", encoding="utf-8") as f:
        conn.executescript(f.read())
    conn.close()

def get_db_connection():
    """SQLiteコネクション取得"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def is_valid_ym_format(ym_str):
    """YYYY-MM形式が有効な日付フォーマットかチェック"""
    try:
        datetime.strptime(ym_str, "%Y-%m")
        return True
    except ValueError:
        return False

def parse_date(date_str):
    """YYYY-MM-DD形式の日付文字列をdatetimeオブジェクトに変換。失敗時None"""
    try:
        return datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        return None

def fetch_expenses_by_ym(year_month):
    """指定年月(YYYY-MM)の支出データをDataFrameで取得"""
    conn = get_db_connection()
    query = "SELECT date, category, amount, note FROM expenses WHERE date LIKE ?"
    df = pd.read_sql_query(query, conn, params=(year_month+'%',))
    conn.close()
    return df

def fetch_expenses_filtered(start_date=None, end_date=None, category=None):
    """
    start_date, end_date, category でフィルタした支出一覧を取得。
    categoryがALLOWED_CATEGORIES外またはNoneなら全カテゴリ対象。
    """
    conn = get_db_connection()
    base_query = "SELECT id, date, category, amount, note FROM expenses"
    params = []
    conditions = []
    if start_date:
        conditions.append("date >= ?")
        params.append(start_date)
    if end_date:
        conditions.append("date <= ?")
        params.append(end_date)
    if category and category in ALLOWED_CATEGORIES:
        conditions.append("category = ?")
        params.append(category)

    if conditions:
        base_query += " WHERE " + " AND ".join(conditions)
    base_query += " ORDER BY date ASC"

    expenses = conn.execute(base_query, params).fetchall()
    conn.close()
    return expenses

@app.route('/')
def index():
    """トップページ：支出追加ページへリダイレクト"""
    return redirect(url_for('add_expense'))

@app.route('/add', methods=['GET', 'POST'])
def add_expense():
    """支出追加エンドポイント：GETでフォーム表示、POSTでDB登録"""
    if request.method == 'POST':
        date_str = request.form.get('date')
        category = request.form.get('category')
        amount_str = request.form.get('amount')
        note = request.form.get('note', '')

        # バリデーション
        if parse_date(date_str) is None:
            return "日付が不正です。YYYY-MM-DD形式で入力してください。<br><a href='/add'>戻る</a>"

        if category not in ALLOWED_CATEGORIES:
            return f"カテゴリが不正です。{ALLOWED_CATEGORIES}から選択してください。<br><a href='/add'>戻る</a>"

        try:
            amount = int(amount_str)
        except ValueError:
            return "金額は整数で入力してください。<br><a href='/add'>戻る</a>"

        if amount <= 0:
            return "金額は1以上の整数で入力してください。<br><a href='/add'>戻る</a>"
        if amount > MAX_AMOUNT:
            return f"金額が大きすぎます。(上限:{MAX_AMOUNT}円)<br><a href='/add'>戻る</a>"

        conn = get_db_connection()
        conn.execute("INSERT INTO expenses (date, category, amount, note) VALUES (?, ?, ?, ?)",
                     (date_str, category, amount, note))
        conn.commit()
        conn.close()

        return redirect(url_for('list_expenses'))

    today = datetime.now().strftime("%Y-%m-%d")
    return render_template("add.html", today=today, categories=ALLOWED_CATEGORIES)

@app.route('/delete/<int:id>', methods=['POST'])
def delete_expense(id):
    """指定IDの支出を削除するエンドポイント"""
    conn = get_db_connection()
    # レコードが存在するかチェック(省略可能、なければDELETEしても問題ないが安全対策として)
    expense = conn.execute("SELECT id FROM expenses WHERE id = ?", (id,)).fetchone()
    if expense is None:
        conn.close()
        return "該当する支出がありません。<br><a href='/list'>戻る</a>"

    conn.execute("DELETE FROM expenses WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('list_expenses'))

@app.route('/list', methods=['GET', 'POST'])
def list_expenses():
    """支出一覧表示：日付範囲およびカテゴリでフィルタ可能"""
    if request.method == 'POST':
        start_date_str = request.form.get('start_date')
        end_date_str = request.form.get('end_date')
        selected_category = request.form.get('filter_category')

        start_dt = parse_date(start_date_str) if start_date_str else None
        end_dt = parse_date(end_date_str) if end_date_str else None

        if start_dt and end_dt and start_dt > end_dt:
            return "開始日が終了日より後になっています。<br><a href='/list'>戻る</a>"

        if (start_date_str and start_dt is None) or (end_date_str and end_dt is None):
            return "日付形式が不正です。(YYYY-MM-DD形式)<br><a href='/list'>戻る</a>"

        start_sql = start_dt.strftime("%Y-%m-%d") if start_dt else None
        end_sql = end_dt.strftime("%Y-%m-%d") if end_dt else None
        category_filter = selected_category if selected_category != "all" else None

        expenses = fetch_expenses_filtered(start_sql, end_sql, category_filter)
    else:
        expenses = fetch_expenses_filtered()

    return render_template("list.html", expenses=expenses, categories=ALLOWED_CATEGORIES)

@app.route('/analysis', methods=['GET', 'POST'])
def analysis():
    """分析ページ：指定年月(YYYY-MM)で支出集計およびグラフ表示"""
    if request.method == 'POST':
        ym_str = request.form.get('year_month')
        if not ym_str or not is_valid_ym_format(ym_str):
            return "指定された年月が不正です。(YYYY-MM形式)<br><a href='/analysis'>戻る</a>"
        current_month = ym_str
    else:
        current_month = datetime.now().strftime("%Y-%m")

    # 前月計算
    year, month = map(int, current_month.split('-'))
    first_day_of_this_month = datetime(year, month, 1)
    last_month_end = first_day_of_this_month - timedelta(days=1)
    last_month = last_month_end.strftime("%Y-%m")

    df_current = fetch_expenses_by_ym(current_month)
    df_last = fetch_expenses_by_ym(last_month)

    current_total = df_current['amount'].sum() if not df_current.empty else 0
    category_sum = df_current.groupby('category')['amount'].sum() if not df_current.empty else pd.Series(dtype='int')
    last_total = df_last['amount'].sum() if not df_last.empty else 0

    diff_rate = (current_total - last_total) / last_total * 100 if last_total > 0 else None

    category_pie_path = None
    if not category_sum.empty:
        fig, ax = plt.subplots(figsize=(4,4))
        ax.pie(category_sum, labels=category_sum.index, autopct='%1.1f%%', startangle=90)
        ax.set_title(f"{current_month} カテゴリ比率")
        plt.tight_layout()
        output_path = "static/images/category_pie.png"
        plt.savefig(output_path)
        plt.close(fig)
        category_pie_path = "/static/images/category_pie.png"

    return render_template("analysis.html",
                           current_month=current_month,
                           current_total=current_total,
                           category_sum=category_sum,
                           last_month=last_month,
                           diff_rate=diff_rate,
                           category_pie_path=category_pie_path)

init_db()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
