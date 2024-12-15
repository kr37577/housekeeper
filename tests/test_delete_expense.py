def test_delete_expense_success(client):
    data = {
        'date': '2024-12-15',
        'category': '食費',
        'amount': '500',
        'note': '削除テスト用'
    }
    res = client.post('/add', data=data, follow_redirects=False)
    assert res.status_code == 302

    list_res = client.get('/list')
    html = list_res.data.decode('utf-8')
    assert '削除テスト用' in html

    import re
    match = re.search(r'<td>(\d+)</td>\s*<td>2024-12-15</td>\s*<td>食費</td>', html, re.DOTALL)
    assert match is not None
    expense_id = match.group(1)

    # 削除実行
    delete_url = f'/delete/{expense_id}'
    del_res = client.post(delete_url, follow_redirects=False)
    assert del_res.status_code == 302

    list_res_after = client.get('/list')
    html_after = list_res_after.data.decode('utf-8')
