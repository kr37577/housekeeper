from datetime import datetime, timedelta

def test_analysis_basic(client):
    # 当月(2024-12)データを複数追加
    data1 = {'date': '2024-12-10', 'category': '食費', 'amount': '1000', 'note': '当月食費1'}
    data2 = {'date': '2024-12-20', 'category': '食費', 'amount': '500', 'note': '当月食費2'}
    data3 = {'date': '2024-12-15', 'category': '娯楽費', 'amount': '2000', 'note': '当月娯楽'}

    for d in [data1, data2, data3]:
        client.post('/add', data=d)

    # 前月データ(2024-11)
    # 2024-12-01の前日は2024-11-30なので前月は"2024-11"
    data4 = {'date': '2024-11-25', 'category': '食費', 'amount': '1000', 'note': '前月食費'}
    client.post('/add', data=data4)

    # /analysisアクセス
    analysis_res = client.get('/analysis')
    html = analysis_res.data.decode('utf-8')
    print(html)
    assert analysis_res.status_code == 200

    # 当月合計 = 食費(1000+500) + 娯楽費(2000) = 3500円
    assert '当月合計: 3500 円' in html
    # カテゴリ別合計: 食費(1500), 娯楽費(2000)
    assert '食費: 1500 円' in html
    assert '娯楽費: 2000 円' in html

    # 前月(2024-11)合計は1000円
    # 前月比: (3500 - 1000)/1000 * 100 = 250%
    # 小数点2桁くらいで表示される想定 (250.00%など)
    assert '前月(2024-11)比:' in html
    # 簡易的に"250"が含まれていればOKとする
    assert '250' in html

def test_analysis_invalid_ym_format(client):
    res = client.post('/analysis', data={'year_month': '2024-13'})
    # 不正な年月フォーマットエラー
    assert res.status_code == 200
    html = res.data.decode('utf-8')
    assert '指定された年月が不正です' in html

def test_analysis_no_last_month(client):
    # 当月だけデータ追加し、前月なし
    data = {'date': '2024-12-10', 'category': '食費', 'amount': '1000', 'note': '当月のみ'}
    client.post('/add', data=data)

    analysis_res = client.get('/analysis')
    html = analysis_res.data.decode('utf-8')
    # 前月比が表示不可メッセージが出る想定
    assert '前月(2024-11)データがないため比較不可' in html
