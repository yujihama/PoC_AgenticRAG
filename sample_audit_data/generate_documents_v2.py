#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
広告事業取引監査用ダミーデータ生成スクリプト
発注書・見積書のPDF生成（WeasyPrint版）
"""

from weasyprint import HTML, CSS
import os

def create_estimate_html(data):
    """見積書HTMLを生成"""
    items_html = ""
    for item in data['items']:
        items_html += f"""
        <tr>
            <td>{item['name']}</td>
            <td class="center">{item['quantity']}</td>
            <td class="center">{item['unit']}</td>
            <td class="right">¥{item['unit_price']:,}</td>
            <td class="right">¥{item['amount']:,}</td>
        </tr>
        """
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            @page {{
                size: A4;
                margin: 20mm;
            }}
            body {{
                font-family: 'Noto Sans CJK JP', 'Noto Sans JP', sans-serif;
                font-size: 10pt;
                line-height: 1.5;
            }}
            .title {{
                text-align: center;
                font-size: 24pt;
                font-weight: bold;
                margin-bottom: 20px;
                letter-spacing: 0.5em;
            }}
            .header-info {{
                text-align: right;
                margin-bottom: 20px;
            }}
            .client {{
                font-size: 14pt;
                font-weight: bold;
                margin-bottom: 10px;
            }}
            .amount-section {{
                margin: 15px 0;
            }}
            .amount-label {{
                display: inline-block;
                width: 80px;
            }}
            .amount-value {{
                font-size: 16pt;
                font-weight: bold;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
                margin: 20px 0;
            }}
            th {{
                background-color: #e6e6e6;
                border: 1px solid #333;
                padding: 8px;
                text-align: center;
            }}
            td {{
                border: 1px solid #333;
                padding: 6px 8px;
            }}
            .center {{ text-align: center; }}
            .right {{ text-align: right; }}
            .total-row {{
                background-color: #f5f5f5;
            }}
            .vendor-info {{
                margin-top: 30px;
            }}
            .vendor-name {{
                font-size: 12pt;
                font-weight: bold;
            }}
            .notes {{
                margin-top: 20px;
                padding: 10px;
                background-color: #f9f9f9;
                border: 1px solid #ddd;
            }}
            .summary-table {{
                width: 50%;
                margin-left: auto;
            }}
        </style>
    </head>
    <body>
        <div class="title">見 積 書</div>
        
        <div class="header-info">
            <div>見積番号: EST-{data['id']}</div>
            <div>見積日: {data['estimate_date']}</div>
            <div>有効期限: {data['valid_until']}</div>
        </div>
        
        <div class="client">{data['client_name']} 御中</div>
        
        <div class="amount-section">
            <span class="amount-label">見積金額:</span>
            <span class="amount-value">¥{data['amount']:,}</span>
            <span>（税込: ¥{int(data['amount'] * 1.1):,}）</span>
        </div>
        
        <div class="amount-section">
            <span class="amount-label">件名:</span>
            <span>{data['subject']}</span>
        </div>
        
        <table>
            <thead>
                <tr>
                    <th style="width: 40%;">項目</th>
                    <th style="width: 12%;">数量</th>
                    <th style="width: 12%;">単位</th>
                    <th style="width: 18%;">単価</th>
                    <th style="width: 18%;">金額</th>
                </tr>
            </thead>
            <tbody>
                {items_html}
            </tbody>
        </table>
        
        <table class="summary-table">
            <tr>
                <td class="center">小計</td>
                <td class="right">¥{data['amount']:,}</td>
            </tr>
            <tr>
                <td class="center">消費税(10%)</td>
                <td class="right">¥{int(data['amount'] * 0.1):,}</td>
            </tr>
            <tr class="total-row">
                <td class="center"><strong>合計</strong></td>
                <td class="right"><strong>¥{int(data['amount'] * 1.1):,}</strong></td>
            </tr>
        </table>
        
        <div class="vendor-info">
            <div class="vendor-name">{data['vendor_name']}</div>
            <div>〒{data['vendor_zip']} {data['vendor_address']}</div>
            <div>TEL: {data['vendor_tel']} / FAX: {data['vendor_fax']}</div>
            <div>担当: {data['vendor_contact']}</div>
        </div>
        
        {f'<div class="notes"><strong>【備考】</strong><br>{data["notes"].replace(chr(10), "<br>")}</div>' if data.get('notes') else ''}
    </body>
    </html>
    """
    return html

def create_order_html(data):
    """発注書HTMLを生成"""
    items_html = ""
    for item in data['items']:
        items_html += f"""
        <tr>
            <td>{item['name']}</td>
            <td class="center">{item['quantity']}</td>
            <td class="center">{item['unit']}</td>
            <td class="right">¥{item['unit_price']:,}</td>
            <td class="right">¥{item['amount']:,}</td>
        </tr>
        """
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            @page {{
                size: A4;
                margin: 20mm;
            }}
            body {{
                font-family: 'Noto Sans CJK JP', 'Noto Sans JP', sans-serif;
                font-size: 10pt;
                line-height: 1.5;
            }}
            .title {{
                text-align: center;
                font-size: 24pt;
                font-weight: bold;
                margin-bottom: 20px;
                letter-spacing: 0.5em;
                color: #003366;
            }}
            .header-info {{
                text-align: right;
                margin-bottom: 20px;
            }}
            .vendor {{
                font-size: 14pt;
                font-weight: bold;
                margin-bottom: 5px;
            }}
            .vendor-contact {{
                margin-bottom: 10px;
            }}
            .amount-section {{
                margin: 15px 0;
            }}
            .amount-label {{
                display: inline-block;
                width: 80px;
            }}
            .amount-value {{
                font-size: 16pt;
                font-weight: bold;
                color: #003366;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
                margin: 20px 0;
            }}
            th {{
                background-color: #c8dcff;
                border: 1px solid #333;
                padding: 8px;
                text-align: center;
            }}
            td {{
                border: 1px solid #333;
                padding: 6px 8px;
            }}
            .center {{ text-align: center; }}
            .right {{ text-align: right; }}
            .total-row {{
                background-color: #e8f0ff;
            }}
            .orderer-info {{
                margin-top: 30px;
                padding: 15px;
                background-color: #f5f8ff;
                border: 1px solid #003366;
            }}
            .orderer-name {{
                font-size: 12pt;
                font-weight: bold;
            }}
            .notes {{
                margin-top: 20px;
                padding: 10px;
                background-color: #f9f9f9;
                border: 1px solid #ddd;
            }}
            .summary-table {{
                width: 50%;
                margin-left: auto;
            }}
            .payment-terms {{
                margin-top: 15px;
                padding: 10px;
                background-color: #fff8e6;
                border: 1px solid #e6c200;
            }}
        </style>
    </head>
    <body>
        <div class="title">発 注 書</div>
        
        <div class="header-info">
            <div>発注番号: PO-{data['id']}</div>
            <div>発注日: {data['order_date']}</div>
            <div>納期: {data['delivery_date']}</div>
        </div>
        
        <div class="vendor">{data['vendor_name']} 御中</div>
        <div class="vendor-contact">担当: {data['vendor_contact']} 様</div>
        
        <div class="amount-section">
            <span class="amount-label">発注金額:</span>
            <span class="amount-value">¥{data['amount']:,}</span>
            <span>（税込: ¥{int(data['amount'] * 1.1):,}）</span>
        </div>
        
        <div class="amount-section">
            <span class="amount-label">件名:</span>
            <span>{data['subject']}</span>
        </div>
        
        <table>
            <thead>
                <tr>
                    <th style="width: 40%;">項目</th>
                    <th style="width: 12%;">数量</th>
                    <th style="width: 12%;">単位</th>
                    <th style="width: 18%;">単価</th>
                    <th style="width: 18%;">金額</th>
                </tr>
            </thead>
            <tbody>
                {items_html}
            </tbody>
        </table>
        
        <table class="summary-table">
            <tr>
                <td class="center">小計</td>
                <td class="right">¥{data['amount']:,}</td>
            </tr>
            <tr>
                <td class="center">消費税(10%)</td>
                <td class="right">¥{int(data['amount'] * 0.1):,}</td>
            </tr>
            <tr class="total-row">
                <td class="center"><strong>合計</strong></td>
                <td class="right"><strong>¥{int(data['amount'] * 1.1):,}</strong></td>
            </tr>
        </table>
        
        <div class="orderer-info">
            <div class="orderer-name">株式会社サンプル広告</div>
            <div>〒100-0001 東京都千代田区千代田1-1-1 サンプルビル5F</div>
            <div>TEL: 03-1234-5678 / FAX: 03-1234-5679</div>
            <div>担当: {data['orderer_contact']}</div>
        </div>
        
        <div class="payment-terms">
            <strong>【支払条件】</strong><br>
            {data['payment_terms']}
        </div>
        
        {f'<div class="notes"><strong>【備考】</strong><br>{data["notes"].replace(chr(10), "<br>")}</div>' if data.get('notes') else ''}
    </body>
    </html>
    """
    return html

def save_pdf(html_content, output_path):
    """HTMLをPDFに変換して保存"""
    HTML(string=html_content).write_pdf(output_path)
    print(f"生成完了: {output_path}")


# 取引データ定義
transactions = [
    # TX-001: 正常取引 - Web広告クリエイティブ制作
    {
        'id': '001',
        'subject': 'Web広告クリエイティブ制作',
        'client_name': '株式会社サンプル広告',
        'vendor_name': '株式会社クリエイティブワークス',
        'vendor_zip': '150-0001',
        'vendor_address': '東京都渋谷区神宮前3-2-1 クリエイティブビル8F',
        'vendor_tel': '03-5555-1234',
        'vendor_fax': '03-5555-1235',
        'vendor_contact': '佐藤 花子',
        'orderer_contact': '田中 一郎',
        'estimate_date': '2025年7月25日',
        'valid_until': '2025年8月25日',
        'order_date': '2025年8月1日',
        'delivery_date': '2025年8月31日',
        'estimate_amount': 500000,
        'order_amount': 500000,
        'amount': 500000,
        'items': [
            {'name': 'バナー広告デザイン制作', 'quantity': 10, 'unit': '点', 'unit_price': 50000, 'amount': 500000}
        ],
        'payment_terms': '納品月末締め翌月末払い',
        'notes': '・サイズ: 300x250, 728x90, 160x600 各種\n・リサイズ対応含む',
        'status': '正常'
    },
    # TX-002: 正常取引 - SNS運用代行
    {
        'id': '002',
        'subject': 'SNS運用代行業務（3ヶ月）',
        'client_name': '株式会社サンプル広告',
        'vendor_name': 'デジタルマーケティング合同会社',
        'vendor_zip': '106-0032',
        'vendor_address': '東京都港区六本木4-5-6 DMビル3F',
        'vendor_tel': '03-6666-7890',
        'vendor_fax': '03-6666-7891',
        'vendor_contact': '鈴木 太郎',
        'orderer_contact': '山本 美咲',
        'estimate_date': '2025年6月20日',
        'valid_until': '2025年7月20日',
        'order_date': '2025年7月1日',
        'delivery_date': '2025年9月30日',
        'estimate_amount': 900000,
        'order_amount': 900000,
        'amount': 900000,
        'items': [
            {'name': 'Instagram運用代行', 'quantity': 3, 'unit': 'ヶ月', 'unit_price': 200000, 'amount': 600000},
            {'name': 'Twitter運用代行', 'quantity': 3, 'unit': 'ヶ月', 'unit_price': 100000, 'amount': 300000}
        ],
        'payment_terms': '月末締め翌月末払い（月額請求）',
        'notes': '・投稿頻度: Instagram週5回、Twitter週10回\n・レポート: 月次提出',
        'status': '正常'
    },
    # TX-003: 正常取引 - 動画広告制作
    {
        'id': '003',
        'subject': '動画広告制作（15秒CM）',
        'client_name': '株式会社サンプル広告',
        'vendor_name': '映像制作株式会社メディアプロ',
        'vendor_zip': '153-0064',
        'vendor_address': '東京都目黒区下目黒2-3-4 メディアタワー10F',
        'vendor_tel': '03-7777-2345',
        'vendor_fax': '03-7777-2346',
        'vendor_contact': '高橋 健一',
        'orderer_contact': '伊藤 直樹',
        'estimate_date': '2025年6月10日',
        'valid_until': '2025年7月10日',
        'order_date': '2025年6月15日',
        'delivery_date': '2025年7月31日',
        'estimate_amount': 1200000,
        'order_amount': 1200000,
        'amount': 1200000,
        'items': [
            {'name': '企画・構成', 'quantity': 1, 'unit': '式', 'unit_price': 200000, 'amount': 200000},
            {'name': '撮影', 'quantity': 1, 'unit': '日', 'unit_price': 400000, 'amount': 400000},
            {'name': '編集・MA', 'quantity': 1, 'unit': '式', 'unit_price': 400000, 'amount': 400000},
            {'name': 'ナレーション収録', 'quantity': 1, 'unit': '式', 'unit_price': 200000, 'amount': 200000}
        ],
        'payment_terms': '納品月末締め翌月末払い',
        'notes': '・尺: 15秒\n・納品形式: MP4, MOV\n・修正: 2回まで含む',
        'status': '正常'
    },
    # TX-101: 金額不整合 - LP制作
    {
        'id': '101',
        'subject': 'ランディングページ制作',
        'client_name': '株式会社サンプル広告',
        'vendor_name': '株式会社クリエイティブワークス',
        'vendor_zip': '150-0001',
        'vendor_address': '東京都渋谷区神宮前3-2-1 クリエイティブビル8F',
        'vendor_tel': '03-5555-1234',
        'vendor_fax': '03-5555-1235',
        'vendor_contact': '佐藤 花子',
        'orderer_contact': '田中 一郎',
        'estimate_date': '2025年8月25日',
        'valid_until': '2025年9月25日',
        'order_date': '2025年9月1日',
        'delivery_date': '2025年9月30日',
        'estimate_amount': 500000,  # 見積: 50万円
        'order_amount': 480000,     # 発注: 48万円（不整合）
        'amount': 480000,
        'items': [
            {'name': 'LP企画・設計', 'quantity': 1, 'unit': '式', 'unit_price': 100000, 'amount': 100000},
            {'name': 'デザイン制作', 'quantity': 1, 'unit': '式', 'unit_price': 200000, 'amount': 200000},
            {'name': 'コーディング', 'quantity': 1, 'unit': '式', 'unit_price': 180000, 'amount': 180000}
        ],
        'payment_terms': '納品月末締め翌月末払い',
        'notes': '・レスポンシブ対応\n・フォーム設置含む',
        'status': '金額不整合'
    },
    # TX-102: 日付不整合 - リスティング広告運用
    {
        'id': '102',
        'subject': 'リスティング広告運用代行（3ヶ月）',
        'client_name': '株式会社サンプル広告',
        'vendor_name': '個人事業主 山田太郎',
        'vendor_zip': '160-0022',
        'vendor_address': '東京都新宿区新宿5-6-7',
        'vendor_tel': '090-1234-5678',
        'vendor_fax': '-',
        'vendor_contact': '山田 太郎',
        'orderer_contact': '中村 雅人',
        'estimate_date': '2025年10月15日',  # 発注日より後（不整合）
        'valid_until': '2025年11月15日',
        'order_date': '2025年10月1日',
        'delivery_date': '2025年12月31日',
        'estimate_amount': 1500000,
        'order_amount': 1500000,
        'amount': 1500000,
        'items': [
            {'name': 'Google広告運用', 'quantity': 3, 'unit': 'ヶ月', 'unit_price': 350000, 'amount': 1050000},
            {'name': 'Yahoo!広告運用', 'quantity': 3, 'unit': 'ヶ月', 'unit_price': 150000, 'amount': 450000}
        ],
        'payment_terms': '月末締め翌月末払い（月額請求）',
        'notes': '・月間広告費: 別途実費\n・レポート: 週次提出',
        'status': '日付不整合'
    },
    # TX-103: 発注先属性不整合 - 市場調査レポート
    {
        'id': '103',
        'subject': '広告効果分析・市場調査レポート作成',
        'client_name': '株式会社サンプル広告',
        'vendor_name': '株式会社建設コンサルタント',  # 建設業（不整合）
        'vendor_zip': '104-0061',
        'vendor_address': '東京都中央区銀座7-8-9 建設ビル6F',
        'vendor_tel': '03-8888-3456',
        'vendor_fax': '03-8888-3457',
        'vendor_contact': '渡辺 誠',
        'orderer_contact': '小林 裕子',
        'estimate_date': '2025年8月10日',
        'valid_until': '2025年9月10日',
        'order_date': '2025年8月15日',
        'delivery_date': '2025年9月15日',
        'estimate_amount': 800000,
        'order_amount': 800000,
        'amount': 800000,
        'items': [
            {'name': '競合分析', 'quantity': 1, 'unit': '式', 'unit_price': 300000, 'amount': 300000},
            {'name': '市場動向調査', 'quantity': 1, 'unit': '式', 'unit_price': 300000, 'amount': 300000},
            {'name': 'レポート作成', 'quantity': 1, 'unit': '式', 'unit_price': 200000, 'amount': 200000}
        ],
        'payment_terms': '納品月末締め翌月末払い',
        'notes': '・調査対象: デジタル広告市場\n・納品形式: PDF',
        'status': '発注先属性不整合'
    },
    # TX-104: 金額と内容不整合 - コンテンツ記事作成
    {
        'id': '104',
        'subject': 'SEOコンテンツ記事作成',
        'client_name': '株式会社サンプル広告',
        'vendor_name': 'ライティングプロ株式会社',
        'vendor_zip': '141-0031',
        'vendor_address': '東京都品川区西五反田1-2-3 ライターズビル4F',
        'vendor_tel': '03-9999-4567',
        'vendor_fax': '03-9999-4568',
        'vendor_contact': '加藤 美穂',
        'orderer_contact': '吉田 浩二',
        'estimate_date': '2025年7月15日',
        'valid_until': '2025年8月15日',
        'order_date': '2025年7月20日',
        'delivery_date': '2025年8月31日',
        'estimate_amount': 5000000,
        'order_amount': 5000000,
        'amount': 5000000,  # 50本で500万円 = 1本10万円（高額すぎる）
        'items': [
            {'name': 'SEO記事作成（3000字）', 'quantity': 50, 'unit': '本', 'unit_price': 100000, 'amount': 5000000}
        ],
        'payment_terms': '納品月末締め翌月末払い',
        'notes': '・文字数: 3000字/本\n・キーワード選定含む',
        'status': '金額と内容不整合'
    },
    # TX-105: 検収物独自性欠如 - ブランディング戦略策定
    {
        'id': '105',
        'subject': 'ブランディング戦略策定',
        'client_name': '株式会社サンプル広告',
        'vendor_name': '株式会社ストラテジーパートナーズ',
        'vendor_zip': '107-0062',
        'vendor_address': '東京都港区南青山4-5-6 ストラテジービル9F',
        'vendor_tel': '03-1111-5678',
        'vendor_fax': '03-1111-5679',
        'vendor_contact': '松本 大輔',
        'orderer_contact': '井上 真理',
        'estimate_date': '2025年9月5日',
        'valid_until': '2025年10月5日',
        'order_date': '2025年9月10日',
        'delivery_date': '2025年10月31日',
        'estimate_amount': 2000000,
        'order_amount': 2000000,
        'amount': 2000000,
        'items': [
            {'name': '現状分析', 'quantity': 1, 'unit': '式', 'unit_price': 500000, 'amount': 500000},
            {'name': 'ブランド戦略立案', 'quantity': 1, 'unit': '式', 'unit_price': 1000000, 'amount': 1000000},
            {'name': '実行計画策定', 'quantity': 1, 'unit': '式', 'unit_price': 500000, 'amount': 500000}
        ],
        'payment_terms': '納品月末締め翌月末払い',
        'notes': '・ワークショップ2回含む\n・最終報告会実施',
        'status': '検収物独自性欠如'
    },
    # TX-106: 複合不整合 - インフルエンサー施策
    {
        'id': '106',
        'subject': 'インフルエンサーマーケティング施策',
        'client_name': '株式会社サンプル広告',
        'vendor_name': 'インフルエンスマーケティング株式会社',
        'vendor_zip': '150-0043',
        'vendor_address': '東京都渋谷区道玄坂2-3-4 インフルエンサービル7F',
        'vendor_tel': '03-2222-6789',
        'vendor_fax': '03-2222-6790',
        'vendor_contact': '木村 拓也',
        'orderer_contact': '斎藤 恵',
        'estimate_date': '2025年7月25日',
        'valid_until': '2025年8月25日',
        'order_date': '2025年8月1日',
        'delivery_date': '2025年9月30日',
        'estimate_amount': 2400000,  # 8名×30万円
        'order_amount': 3000000,     # 10名×30万円（数量不整合）
        'amount': 3000000,
        'estimate_items': [
            {'name': 'インフルエンサー起用', 'quantity': 8, 'unit': '名', 'unit_price': 300000, 'amount': 2400000}
        ],
        'items': [
            {'name': 'インフルエンサー起用', 'quantity': 10, 'unit': '名', 'unit_price': 300000, 'amount': 3000000}
        ],
        'payment_terms': '納品月末締め翌月末払い',
        'notes': '・フォロワー数: 10万人以上\n・投稿: Instagram 1投稿/人',
        'status': '複合不整合（数量）'
    },
    # TX-107: 日付不整合 - 広告効果測定ツール導入
    {
        'id': '107',
        'subject': '広告効果測定ダッシュボード構築',
        'client_name': '株式会社サンプル広告',
        'vendor_name': 'システム開発株式会社テクノソリューション',
        'vendor_zip': '108-0075',
        'vendor_address': '東京都港区港南3-4-5 テクノタワー12F',
        'vendor_tel': '03-3333-7890',
        'vendor_fax': '03-3333-7891',
        'vendor_contact': '清水 健太',
        'orderer_contact': '森田 優子',
        'estimate_date': '2025年6月25日',
        'valid_until': '2025年7月25日',
        'order_date': '2025年7月1日',
        'delivery_date': '2025年10月15日',  # 検収日より後（不整合）
        'acceptance_date': '2025年9月30日',  # 納品日より前（不整合）
        'estimate_amount': 4500000,
        'order_amount': 4500000,
        'amount': 4500000,
        'items': [
            {'name': '要件定義', 'quantity': 1, 'unit': '式', 'unit_price': 500000, 'amount': 500000},
            {'name': '設計', 'quantity': 1, 'unit': '式', 'unit_price': 1000000, 'amount': 1000000},
            {'name': '開発', 'quantity': 1, 'unit': '式', 'unit_price': 2000000, 'amount': 2000000},
            {'name': 'テスト・導入', 'quantity': 1, 'unit': '式', 'unit_price': 1000000, 'amount': 1000000}
        ],
        'payment_terms': '検収月末締め翌月末払い',
        'notes': '・対応広告媒体: Google, Yahoo!, Meta\n・保守: 別途契約',
        'status': '日付不整合（検収日）'
    }
]

# 出力ディレクトリ
estimate_dir = '/home/ubuntu/ad_audit_test_data/見積書'
order_dir = '/home/ubuntu/ad_audit_test_data/発注書'

# 各取引の見積書・発注書を生成
for tx in transactions:
    # 見積書用データ（TX-106は見積と発注で数量が異なる）
    estimate_data = tx.copy()
    if tx['id'] == '106':
        estimate_data['items'] = tx['estimate_items']
        estimate_data['amount'] = tx['estimate_amount']
    else:
        estimate_data['amount'] = tx.get('estimate_amount', tx['amount'])
    
    estimate_html = create_estimate_html(estimate_data)
    save_pdf(estimate_html, f"{estimate_dir}/TX-{tx['id']}_見積書.pdf")
    
    # 発注書用データ
    order_data = tx.copy()
    order_data['amount'] = tx.get('order_amount', tx['amount'])
    order_html = create_order_html(order_data)
    save_pdf(order_html, f"{order_dir}/TX-{tx['id']}_発注書.pdf")

print("\n全ての発注書・見積書の生成が完了しました。")
