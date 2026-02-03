# 広告事業取引監査テスト用ダミーデータセット
# Ad Business Transaction Audit Test Data Set

## 概要 / Overview

本データセットは、広告事業における取引監査システムのテストを目的として作成されたダミーデータです。正常取引と検知すべき不整合取引の両方を含み、監査システムの検出精度を検証するために使用できます。

This dataset contains dummy data for testing advertising business transaction audit systems. It includes both normal transactions and transactions with discrepancies that should be detected.

## ディレクトリ構成 / Directory Structure

```
ad_audit_test_data/
├── purchase_orders/           # 発注書PDF（10件）/ Purchase Order PDFs
├── quotations/                # 見積書PDF（10件）/ Quotation PDFs
├── order_invoice_data/        # 社内システム出力データ / Order & Invoice Data (Excel)
├── acceptance_docs/           # 検収用資料 / Acceptance Documents
│   ├── pdf/                   # PDF形式の検収資料
│   ├── excel/                 # Excel形式の検収資料
│   ├── powerpoint/            # PowerPoint形式の検収資料
│   └── images/                # 画像形式の検収資料
├── README.md                  # 本ファイル / This file
├── 不整合一覧.md              # 検知すべき不整合の一覧 / Discrepancy List
└── 取引シナリオ設計.md        # 取引シナリオの詳細設計 / Transaction Scenario Design
```

## ファイル命名規則 / File Naming Convention

| ファイル種別 | 命名パターン | 例 |
|-------------|-------------|-----|
| 発注書 | TX-XXX_purchase_order.pdf | TX-001_purchase_order.pdf |
| 見積書 | TX-XXX_quotation.pdf | TX-001_quotation.pdf |
| 検収資料 | TX-XXX_[内容].pdf/xlsx/pptx/png | TX-001_banner_delivery_report.pdf |

## 取引一覧 / Transaction List

| 取引ID | 件名 | 発注先 | 金額 | 判定 |
|--------|------|--------|------|------|
| TX-001 | Web広告クリエイティブ制作 | 株式会社クリエイティブワークス | ¥500,000 | 正常 |
| TX-002 | SNS運用代行（3ヶ月） | 株式会社デジタルマーケティング | ¥900,000 | 正常 |
| TX-003 | 動画広告制作 | 映像制作株式会社メディアプロ | ¥1,500,000 | 正常 |
| TX-101 | ランディングページ制作 | 株式会社クリエイティブワークス | ¥800,000 | 要検知 |
| TX-102 | リスティング広告運用代行 | 個人事業主 山田太郎 | ¥1,500,000 | 要検知 |
| TX-103 | 市場調査レポート作成 | 株式会社建設コンサルタント | ¥2,000,000 | 要検知 |
| TX-104 | SEOコンテンツ制作（50本） | 株式会社コンテンツファクトリー | ¥2,500,000 | 要検知 |
| TX-105 | ブランディング戦略策定 | 株式会社ストラテジーパートナーズ | ¥3,000,000 | 要検知 |
| TX-106 | インフルエンサーマーケティング | 株式会社インフルエンスラボ | ¥3,000,000 | 要検知 |
| TX-107 | 広告効果測定システム開発 | システム開発株式会社テクノソリューション | ¥5,000,000 | 要検知 |

## 検収資料の形式 / Acceptance Document Formats

| 取引ID | 形式 | ファイル名 |
|--------|------|------------|
| TX-001 | PDF + PNG | TX-001_banner_delivery_report.pdf, TX-001_banner_*.png |
| TX-002 | Excel | TX-002_sns_operation_report.xlsx |
| TX-003 | PDF | TX-003_video_ad_spec.pdf |
| TX-101 | PDF | TX-101_lp_delivery_report.pdf |
| TX-102 | Excel | TX-102_ad_operation_report.xlsx |
| TX-103 | PDF | TX-103_market_research_report.pdf |
| TX-104 | Excel | TX-104_seo_article_list.xlsx |
| TX-105 | PowerPoint | TX-105_branding_strategy.pptx |
| TX-106 | Excel | TX-106_influencer_post_list.xlsx |
| TX-107 | PDF | TX-107_system_spec.pdf |

## テスト観点 / Test Perspectives

本データセットは以下の監査観点をテストするために設計されています：

1. **資料間の不整合検出** - 発注書、見積書、請求データ間の金額・数量・日付の不一致
2. **日付不整合** - 発注日より前の見積日、納品日より後の検収日など
3. **発注先属性と内容の不整合** - 業種と発注内容のミスマッチ
4. **金額と内容の不整合** - 作業量・成果物に対して不相応な金額
5. **検収物の独自性欠如** - 汎用テンプレートそのままの成果物

## 注意事項 / Notes

- 本データセットはテスト目的で作成された架空のデータです
- 実在の企業・個人とは一切関係ありません
- 金額・日付・内容はすべてフィクションです
