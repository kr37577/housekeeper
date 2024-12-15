import os
import tempfile
import pytest
from app.app import app, init_db, DB_PATH
import sqlite3

@pytest.fixture
def app_fixture():
    # テスト用にメモリDBを使用
    # DB_PATHはapp.pyで定義されていると想定
    # app起動前にDB_PATHを上書きすることでinit_dbが:memory:上で実行可能にする
    original_db_path = DB_PATH
    test_db_path = ":memory:"
    # DB_PATH を更新するにはapp自体で定義された場所を修正するか、
    # 環境変数やapp.configを使う方法を検討できる。
    # ここでは簡易的にapp.py側でDB_PATH = "db/expenses.db" としているなら、
    # app起動後にapp.configで書き換えるなども可能:
    # 例: app.config['DB_PATH'] = ":memory:"
    # ただし、app.py内のDB_PATH参照ロジックを見直す必要あり。

    # 簡易例として、もしapp.py内でDB_PATHをグローバル変数として参照しているなら、
    # import app後にapp.DB_PATH = ":memory:"とすることで書き換えられる:
    import app.app as app_module
    app_module.DB_PATH = ":memory:"

    # DB初期化
    init_db()

    yield app

    # ここでテスト後のクリーンアップ（:memory:の場合は不要だが、ファイルDBなら削除処理が必要）

@pytest.fixture
def client(app_fixture):
    # Flaskのテストクライアント取得
    with app.test_client() as client:
        yield client
