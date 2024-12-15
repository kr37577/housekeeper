def test_add_expense_success(client):
    # 正常な支出追加
    data = {
        'date': '2024-12-15',
        'category': '食費',
        'amount': '1000',
        'note': 'テスト用ランチ'
    }
    res = client.post('/add', data=data, follow_redirects=False)
    # 正常時、/addはデータ登録後 /list へリダイレクト(302)
    assert res.status_code == 302

    # リダイレクト先の /list で追加した支出が表示されるか確認
    list_res = client.get('/list')
    assert list_res.status_code == 200
    html = list_res.data.decode('utf-8')
    assert 'テスト用ランチ' in html
    assert '1000' in html

def test_add_expense_invalid_date(client):
    # 不正な日付
    data = {
        'date': '2024-13-15',  # 存在しない13月
        'category': '食費',
        'amount': '1000',
        'note': '不正日付テスト'
    }
    res = client.post('/add', data=data)
    # エラーメッセージが返される想定（/addをもう一度表示かメッセージ表示）
    assert res.status_code == 200
    html = res.data.decode('utf-8')
    assert '日付が不正です' in html

def test_add_expense_negative_amount(client):
    # マイナス金額テスト
    data = {
        'date': '2024-12-15',
        'category': '食費',
        'amount': '-100',
        'note': '不正金額テスト'
    }
    res = client.post('/add', data=data)
    assert res.status_code == 200
    html = res.data.decode('utf-8')
    assert '金額は1以上の整数で入力してください' in html
