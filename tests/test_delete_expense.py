def test_delete_expense_success(client):
    # まず支出を追加
    data = {
        'date': '2024-12-15',
        'category': '食費',
        'amount': '500',
        'note': '削除テスト用'
    }
    res = client.post('/add', data=data, follow_redirects=False)
    assert res.status_code == 302  # 成功時リダイレクト

    # /list で追加を確認
    list_res = client.get('/list')
    html = list_res.data.decode('utf-8')
    assert '削除テスト用' in html

    # HTMLからIDを抽出(簡易な正規表現等を使用)
    # 例: <td>1</td><td>2024-12-15</td><td>食費</td>...
    # といった形式でIDが表に出ていると仮定し、一番最初の一致を使う
    import re
    match = re.search(r'<td>(\d+)</td><td>2024-12-15</td><td>食費</td>', html)
    assert match is not None
    expense_id = match.group(1)

    # 削除実行
    delete_url = f'/delete/{expense_id}'
    del_res = client.post(delete_url, follow_redirects=False)
    # 削除成功で/listへリダイレクト想定
    assert del_res.status_code == 302

    # 再度/listで"削除テスト用"が消えていることを確認
    list_res_after = client.get('/list')
    html_after = list_res_after.data.decode('utf-8')
    assert '削除テスト用' not in html_after

def test_delete_expense_not_found(client):
    # 存在しないIDを削除しようとするとエラー表示（想定）
    del_res = client.post('/delete/9999')
    assert del_res.status_code == 200
    html = del_res.data.decode('utf-8')
    assert '該当する支出がありません' in html
