"""見積書・請求書・納品書のサンプル PDF を生成する。

実行: nix-shell -p python3Packages.reportlab --run "python3 src/generate_samples.py"
出力: src/samples/ に 30 枚の PDF を生成
"""

import os
import random
from datetime import date, timedelta

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    TableStyle,
    Paragraph,
    Spacer,
)
from reportlab.lib.styles import ParagraphStyle

import platform

# OSや環境に応じたフォント候補パス
FONT_PATHS = []
if platform.system() == "Darwin":
    FONT_PATHS = [
        "/Library/Fonts/Arial Unicode.ttf",
        "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
        "/System/Library/Fonts/PingFang.ttc",
        "/System/Library/Fonts/Hiragino Sans GB.ttc",
    ]
else:
    FONT_PATHS = [
        "/run/current-system/sw/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
        "/run/current-system/sw/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/run/current-system/sw/share/fonts/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/fonts-japanese-gothic.ttf",
        "/usr/share/fonts/opentype/ipafont/ipag.ttf",
    ]

font_path = None
for path in FONT_PATHS:
    if os.path.exists(path):
        font_path = path
        break

if font_path:
    pdfmetrics.registerFont(TTFont("ArialUni", font_path))
else:
    print("Warning: No Japanese font found. Falling back to default Helvetica.")
    try:
        # reportlabのコアフォントであるHelveticaで登録（クラッシュ回避）
        pdfmetrics.registerFont(TTFont("ArialUni", "Helvetica"))
    except Exception:
        pass

FONT = "ArialUni"

OUTDIR = os.path.join(os.path.dirname(__file__), "samples")

# ---------------------------------------------------------------------------
# データ定義
# ---------------------------------------------------------------------------

# DB に存在する取引先・商品（order-system-migration のシードデータ準拠）
CUSTOMERS_IN_DB = [
    {"name": "株式会社東京商事", "zip": "100-0001", "addr": "東京都千代田区丸の内1-1-1"},
    {"name": "大阪物産株式会社", "zip": "530-0001", "addr": "大阪府大阪市北区梅田2-2-2"},
    {"name": "株式会社札幌オフィス", "zip": "060-0001", "addr": "北海道札幌市中央区北1条西3-3"},
    {"name": "仙台ビジネス株式会社", "zip": "980-0021", "addr": "宮城県仙台市青葉区中央1-4-4"},
    {"name": "名古屋産業株式会社", "zip": "450-0002", "addr": "愛知県名古屋市中村区名駅5-5-5"},
    {"name": "横浜トレーディング株式会社", "zip": "220-0012", "addr": "神奈川県横浜市西区みなとみらい6-6"},
    {"name": "広島商工株式会社", "zip": "730-0011", "addr": "広島県広島市中区基町7-7-7"},
    {"name": "福岡商事株式会社", "zip": "810-0001", "addr": "福岡県福岡市中央区天神8-8-8"},
]

ITEMS_IN_DB = [
    {"name": "高性能オフィスチェア", "price": 85000},
    {"name": "デスクライト", "price": 12000},
    {"name": "ホワイトボード", "price": 28000},
    {"name": "シュレッダー", "price": 35000},
    {"name": "スタンディングデスク", "price": 120000},
    {"name": "会議用テーブル", "price": 95000},
    {"name": "ロッカー", "price": 45000},
    {"name": "パーテーション", "price": 38000},
    {"name": "コピー用紙(500枚)", "price": 1500},
    {"name": "ボールペン(10本セット)", "price": 800},
    {"name": "クリアファイル(10枚)", "price": 600},
    {"name": "トナーカートリッジ", "price": 8500},
]

# DB に存在しない取引先・商品（突合で不一致になるテストデータ）
CUSTOMERS_NOT_IN_DB = [
    {"name": "四国文具株式会社", "zip": "760-0023", "addr": "香川県高松市寿町1-2-3"},
    {"name": "株式会社沖縄オフィスサプライ", "zip": "900-0015", "addr": "沖縄県那覇市久茂地3-4-5"},
]

ITEMS_NOT_IN_DB = [
    {"name": "A3レーザープリンター", "price": 198000},
    {"name": "電動昇降デスク", "price": 156000},
    {"name": "防音パネル(4枚セット)", "price": 72000},
    {"name": "ケーブルトレイ", "price": 4500},
]

TAX_RATE = 0.10

# 自社情報（帳票の宛先 = 架空の会社）
OWN_COMPANY = "中央オフィス機器株式会社"
OWN_ZIP = "100-0005"
OWN_ADDR = "東京都千代田区丸の内1-9-1"


def _fmt(n):
    return f"{int(n):,}"


def _date_str(d):
    return f"{d.year}年{d.month}月{d.day}日"


# ---------------------------------------------------------------------------
# 共通描画
# ---------------------------------------------------------------------------

def _title_style(size=18):
    return ParagraphStyle("title", fontName=FONT, fontSize=size, leading=size + 6,
                          alignment=1, spaceAfter=4 * mm)


def _normal_style(size=9):
    return ParagraphStyle("normal", fontName=FONT, fontSize=size, leading=size + 4)


def _small_style(size=8):
    return ParagraphStyle("small", fontName=FONT, fontSize=size, leading=size + 3)


def _header_block(elements, doc_type, doc_no, doc_date, customer, issuer):
    """帳票上部（タイトル・宛先・発行元）を共通で描画。"""
    ns = _normal_style()
    ss = _small_style()

    elements.append(Paragraph(doc_type, _title_style()))
    elements.append(Spacer(1, 2 * mm))

    header_data = [
        [Paragraph(f"{customer['name']}　御中", _normal_style(11)), "",
         Paragraph(f"{doc_type[0]}No. {doc_no}", ss)],
        [Paragraph(f"〒{customer['zip']}", ss), "",
         Paragraph(f"発行日　{_date_str(doc_date)}", ss)],
        [Paragraph(customer["addr"], ss), "", ""],
        ["", "", ""],
        ["", "", Paragraph(f"{issuer['name']}", _normal_style(10))],
        ["", "", Paragraph(f"〒{issuer['zip']}", ss)],
        ["", "", Paragraph(issuer["addr"], ss)],
        ["", "", Paragraph(f"TEL: {issuer['tel']}", ss)],
    ]
    ht = Table(header_data, colWidths=[75 * mm, 20 * mm, 75 * mm])
    ht.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LINEBELOW", (0, 0), (0, 0), 0.8, colors.black),
    ]))
    elements.append(ht)
    elements.append(Spacer(1, 5 * mm))


def _items_table(elements, items, show_remarks=False):
    """明細テーブルを描画。"""
    ss = _small_style()
    cols = ["No.", "品　名", "数量", "単価", "金額"]
    if show_remarks:
        cols.append("摘要")

    header = [Paragraph(c, _small_style(8)) for c in cols]
    rows = [header]

    subtotal = 0
    for i, item in enumerate(items, 1):
        amt = item["price"] * item["qty"]
        subtotal += amt
        row = [
            str(i),
            Paragraph(item["name"], ss),
            _fmt(item["qty"]),
            _fmt(item["price"]),
            _fmt(amt),
        ]
        if show_remarks:
            row.append(Paragraph(item.get("remark", ""), ss))
        rows.append(row)

    # 空行で埋める（帳票らしく）
    blank_count = max(0, 8 - len(items))
    for _ in range(blank_count):
        row = ["", "", "", "", ""]
        if show_remarks:
            row.append("")
        rows.append(row)

    tax = int(subtotal * TAX_RATE)
    total = subtotal + tax

    footer_rows = [
        ["", "", "", Paragraph("小　計", ss), _fmt(subtotal)],
        ["", "", "", Paragraph("消費税(10%)", ss), _fmt(tax)],
        ["", "", "", Paragraph("合　計", ss), _fmt(total)],
    ]
    if show_remarks:
        for r in footer_rows:
            r.append("")

    rows.extend(footer_rows)

    if show_remarks:
        col_widths = [12 * mm, 55 * mm, 18 * mm, 25 * mm, 28 * mm, 30 * mm]
    else:
        col_widths = [12 * mm, 65 * mm, 20 * mm, 28 * mm, 33 * mm]

    t = Table(rows, colWidths=col_widths)
    style_cmds = [
        ("FONT", (0, 0), (-1, -1), FONT, 8),
        ("ALIGN", (0, 0), (0, -1), "CENTER"),
        ("ALIGN", (2, 0), (4, -1), "RIGHT"),
        ("GRID", (0, 0), (-1, len(items)), 0.5, colors.black),
        ("BACKGROUND", (0, 0), (-1, 0), colors.Color(0.9, 0.9, 0.9)),
        ("LINEABOVE", (-2, -3), (-1, -3), 0.8, colors.black),
        ("LINEBELOW", (-2, -1), (-1, -1), 1.2, colors.black),
        ("FONT", (-2, -1), (-1, -1), FONT, 10),
    ]
    t.setStyle(TableStyle(style_cmds))
    elements.append(t)

    return total


def _total_banner(elements, total, label="御請求金額"):
    ns = _normal_style(12)
    banner = Table(
        [[Paragraph(label, ns), Paragraph(f"¥{_fmt(total)}-（税込）", _normal_style(14))]],
        colWidths=[45 * mm, 80 * mm],
    )
    banner.setStyle(TableStyle([
        ("LINEBELOW", (0, 0), (-1, 0), 1.5, colors.black),
        ("LINEABOVE", (0, 0), (-1, 0), 1.5, colors.black),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3 * mm),
        ("TOPPADDING", (0, 0), (-1, -1), 3 * mm),
    ]))
    elements.append(banner)
    elements.append(Spacer(1, 5 * mm))


# ---------------------------------------------------------------------------
# 帳票別の生成
# ---------------------------------------------------------------------------

def generate_quotation(path, doc_no, doc_date, customer, issuer, items, payment_terms, valid_days):
    doc = SimpleDocTemplate(path, pagesize=A4,
                            topMargin=20 * mm, bottomMargin=15 * mm,
                            leftMargin=18 * mm, rightMargin=18 * mm)
    elems = []
    _header_block(elems, "御 見 積 書", doc_no, doc_date, customer, issuer)

    ss = _small_style()
    meta = Table([
        [Paragraph("件名", ss), Paragraph("オフィス用品納入", ss),
         Paragraph(f"納期: 受注後 {random.choice([7,10,14])} 営業日", ss)],
        [Paragraph("支払条件", ss), Paragraph(payment_terms, ss),
         Paragraph(f"有効期限: 発行日より {valid_days} 日間", ss)],
    ], colWidths=[20 * mm, 60 * mm, 80 * mm])
    meta.setStyle(TableStyle([
        ("FONT", (0, 0), (-1, -1), FONT, 8),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.black),
        ("INNERGRID", (0, 0), (-1, -1), 0.3, colors.grey),
        ("BACKGROUND", (0, 0), (0, -1), colors.Color(0.92, 0.95, 1.0)),
    ]))
    elems.append(meta)
    elems.append(Spacer(1, 5 * mm))

    total = _items_table(elems, items)
    elems.insert(4, Spacer(1, 2 * mm))
    _total_banner(elems, total, "御見積金額")
    # move banner before items table — rebuild
    # (simpler: just append note)
    elems.append(Spacer(1, 8 * mm))
    elems.append(Paragraph("備考：", _small_style()))
    elems.append(Paragraph("　上記金額には消費税(10%)を含みます。", _small_style()))

    doc.build(elems)


def generate_invoice(path, doc_no, doc_date, customer, issuer, items, due_date, bank_info):
    doc = SimpleDocTemplate(path, pagesize=A4,
                            topMargin=20 * mm, bottomMargin=15 * mm,
                            leftMargin=18 * mm, rightMargin=18 * mm)
    elems = []
    _header_block(elems, "請 求 書", doc_no, doc_date, customer, issuer)

    ss = _small_style()
    elems.append(Paragraph(f"下記のとおりご請求いたします。", _normal_style()))
    elems.append(Spacer(1, 3 * mm))

    total = _items_table(elems, items)
    _total_banner(elems, total, "御請求金額")

    elems.append(Spacer(1, 5 * mm))
    bank = Table([
        [Paragraph("（振込先）", ss), ""],
        [Paragraph(f"{bank_info['bank']}　{bank_info['branch']}", ss), ""],
        [Paragraph(f"預金種別：普通", ss),
         Paragraph(f"お支払期限：{_date_str(due_date)}", ss)],
        [Paragraph(f"口座番号：{bank_info['account']}", ss), ""],
        [Paragraph(f"口座名義：{issuer['name']}", ss), ""],
    ], colWidths=[90 * mm, 70 * mm])
    bank.setStyle(TableStyle([
        ("FONT", (0, 0), (-1, -1), FONT, 8),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.grey),
    ]))
    elems.append(bank)

    elems.append(Spacer(1, 8 * mm))
    elems.append(Paragraph("備考：", ss))

    doc.build(elems)


def generate_delivery_slip(path, doc_no, doc_date, customer, issuer, items, order_no):
    doc = SimpleDocTemplate(path, pagesize=A4,
                            topMargin=20 * mm, bottomMargin=15 * mm,
                            leftMargin=18 * mm, rightMargin=18 * mm)
    elems = []
    _header_block(elems, "納 品 書", doc_no, doc_date, customer, issuer)

    ss = _small_style()
    elems.append(Paragraph("下記のとおり納品いたします。", _normal_style()))
    elems.append(Spacer(1, 2 * mm))

    meta = Table([
        [Paragraph(f"注文番号：{order_no}", ss),
         Paragraph(f"納品日：{_date_str(doc_date)}", ss)],
    ], colWidths=[90 * mm, 70 * mm])
    meta.setStyle(TableStyle([
        ("FONT", (0, 0), (-1, -1), FONT, 8),
    ]))
    elems.append(meta)
    elems.append(Spacer(1, 3 * mm))

    total = _items_table(elems, items, show_remarks=True)
    _total_banner(elems, total, "納品合計金額")

    elems.append(Spacer(1, 10 * mm))
    stamp_table = Table(
        [["", "", Paragraph("検　印", ss), Paragraph("受領印", ss)]],
        colWidths=[80 * mm, 30 * mm, 30 * mm, 30 * mm],
    )
    stamp_table.setStyle(TableStyle([
        ("BOX", (2, 0), (2, 0), 0.5, colors.black),
        ("BOX", (3, 0), (3, 0), 0.5, colors.black),
        ("FONT", (0, 0), (-1, -1), FONT, 8),
        ("ALIGN", (2, 0), (-1, -1), "CENTER"),
        ("BOTTOMPADDING", (2, 0), (-1, -1), 12 * mm),
    ]))
    elems.append(stamp_table)

    doc.build(elems)


# ---------------------------------------------------------------------------
# データ生成・実行
# ---------------------------------------------------------------------------

def _pick_items(count, allow_unknown=False):
    pool = list(ITEMS_IN_DB)
    if allow_unknown:
        pool.extend(ITEMS_NOT_IN_DB)
    selected = random.sample(pool, min(count, len(pool)))
    result = []
    for item in selected:
        qty = random.randint(1, 30)
        price = item["price"]
        if allow_unknown and random.random() < 0.3:
            price = int(price * random.uniform(0.85, 1.15))
        result.append({"name": item["name"], "price": price, "qty": qty, "remark": ""})
    return result


def _pick_customer(idx, allow_unknown=False):
    if allow_unknown and idx >= 8:
        return CUSTOMERS_NOT_IN_DB[idx - 8]
    return CUSTOMERS_IN_DB[idx % len(CUSTOMERS_IN_DB)]


PAYMENT_TERMS = ["月末締め翌月末払い", "納品後30日以内", "月末締め翌々月10日払い"]
BANKS = [
    {"bank": "三菱UFJ銀行", "branch": "京都支店", "account": "1234567"},
    {"bank": "みずほ銀行", "branch": "大阪支店", "account": "2345678"},
    {"bank": "三井住友銀行", "branch": "名古屋支店", "account": "3456789"},
    {"bank": "京都銀行", "branch": "本店営業部", "account": "4567890"},
]


def main():
    os.makedirs(OUTDIR, exist_ok=True)
    random.seed(42)
    base_date = date(2026, 4, 1)

    for i in range(10):
        # 8割は DB にいる取引先、2割は DB にいない取引先
        allow_unknown = i >= 8
        customer = _pick_customer(i, allow_unknown)

        issuer = {"name": customer["name"], "zip": customer["zip"],
                  "addr": customer["addr"], "tel": f"0{random.randint(3,99):02d}-{random.randint(100,999)}-{random.randint(1000,9999)}"}
        recipient = {"name": OWN_COMPANY, "zip": OWN_ZIP, "addr": OWN_ADDR}

        d = base_date + timedelta(days=random.randint(0, 60))
        items = _pick_items(random.randint(1, 5), allow_unknown)

        # 見積書
        q_no = f"Q-2026-{i+1:04d}"
        generate_quotation(
            os.path.join(OUTDIR, f"quotation_{i+1:02d}.pdf"),
            q_no, d, recipient, issuer, items,
            random.choice(PAYMENT_TERMS), random.choice([30, 60, 90]),
        )

        # 請求書
        inv_date = d + timedelta(days=random.randint(14, 45))
        inv_no = f"INV-2026-{i+1:04d}"
        due_date = inv_date + timedelta(days=30)
        generate_invoice(
            os.path.join(OUTDIR, f"invoice_{i+1:02d}.pdf"),
            inv_no, inv_date, recipient, issuer, items,
            due_date, random.choice(BANKS),
        )

        # 納品書
        del_date = d + timedelta(days=random.randint(7, 21))
        del_no = f"D-2026-{i+1:04d}"
        order_no = f"20260{random.randint(1,5)}{random.randint(10,28):02d}-{random.randint(1,3):03d}"
        generate_delivery_slip(
            os.path.join(OUTDIR, f"delivery_{i+1:02d}.pdf"),
            del_no, del_date, recipient, issuer, items,
            order_no,
        )

    print(f"Generated 30 PDFs in {OUTDIR}/")


if __name__ == "__main__":
    main()
