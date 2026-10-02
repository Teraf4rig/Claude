# 旅ナビ(Tabi Navi)— 開発ガイド

名古屋(NGO)発の行き先・航空券価格・JALマイルを1画面で見る、RIKI個人用のWebページ。
Claude の Artifact として公開している(非公開・本人のみ閲覧)。

- 公開先: https://claude.ai/artifact/SEfzwX1ntCXSMGgBURQrLE (現在 Version 7)
- このフォルダは V7 と同じ内容をビルドできるソース一式(`python3 build.py` の出力は公開中の V7 とバイト単位で一致することを確認済み)

## フォルダ構成

```
src/page.tpl.html   本体。HTML + CSS + JS を1ファイルに書いたテンプレート(編集するのはここ)
data/               ビルド時に埋め込むデータ
  land.txt grat.txt sphere.txt proj.json   平面地図(Equal Earth 図法、中心 東経155度)のSVGパスと投影係数
  globe.txt         地球儀用の陸地ドット(緯度経度を base36 4文字で連結、約7,000点)
  airports.txt      空港マスタ(code|日本語名|英語名|国|経度|緯度|地域)
build.py            テンプレートに data/ を差し込んで dist/tabinavi.html を作る
fixtures/           ローカル確認用のデータ(2026-09-23 時点の本番DBの写し)
tools/              data/ を作り直すときだけ使う Node スクリプト(gen-map.mjs, gen-globe.mjs)
dist/               ビルド結果(tabinavi.html = 公開用、preview.html = 仮データ入り確認用)
```

## よく使うコマンド

```
python3 build.py            # dist/tabinavi.html を作る(公開用)
python3 build.py --preview  # 上に加えて dist/preview.html を作る → ブラウザで直接開いて確認
```

`preview.html` は `window.claude` を偽物に差し替えて fixtures/ のデータを表示する。
編集操作(行き先追加・経路保存など)も動くが、メモリ上だけで保存はされない。

地図や地球儀のデータを作り直す場合のみ: `cd tools && npm install && node gen-map.mjs && node gen-globe.mjs`

## 公開のしかた

公開は Claude の **Artifact ツール**で行う(`url` に上の公開先を指定して `dist/tabinavi.html` を publish すると同じURLのまま新バージョンになる)。

- `capabilities` は**指定しない**(省略すると現在の設定 `db` + `user` が引き継がれる。`{}` を渡すと消えるので注意)
- Artifact ツールが使えない環境では公開できない。その場合は `dist/tabinavi.html` を Cowork(Claude アプリ)のチャットに渡して公開を頼む
- 公開ファイルは `<!doctype>` `<html>` `<head>` `<body>` を**書かない**(公開時に外枠が付く)。テンプレートは `<title>` と `<style>` から始まる

## 守る制約(破ると本番で黙って壊れる)

1. **1ファイル完結**。外部から読めるのは Google Fonts のCSSと、cdnjs / jsdelivr のスクリプトだけ。画像・他ホストへの fetch・別ファイルのCSS/JSは不可
2. `alert / confirm / prompt` は使えない(確認は画面内のUIで行う。削除ボタンの2度押し確認が例)
3. `<a download>` や `window.print()` は効かない
4. `localStorage` は try/catch 必須、消えても動くこと(検索条件 `tabinavi.search` の保存だけに使用)
5. ページ本体は横スクロールさせない。スマホ幅(約390px)で必ず確認
6. 配色はトークン(`:root` の CSS変数)経由。ライトを `:root`、ダークを
   `@media (prefers-color-scheme:dark){:root:not([data-theme="light"])}` と `:root[data-theme="dark"]` の**両方**に書く
7. `prefers-reduced-motion` のとき、アニメーションは止めて静止状態で読めること

## データ(Artifact のデータベース)

ページは `await window.claude.use('db')` で DB を取り、`onSnapshot` で購読して描画する。
編集できるのはオーナーのみ(`claude.use('user')` の `canEdit()`)。

`dest/<id>` — 行き先1件(現在25件)
```
{ id, name, country, region, status:'wish'|'cand', lon, lat, iata,
  route:{via:[{code,lon,lat}], kind, duration, basis, note}, routes:[...同じ形],
  today:{ flight:{price, origin, airline, route, source, url, checkedAt, confidence, note},
          hotel:{price, name, area, ...} },
  spring:{ flight:{rec, low, high}, hotel:{price}, when, note },   // 春休み 2〜3月
  summer:{ ...同上 },                                              // 夏休み 8〜9月
  miles:{ ow, rt, cls, basis, source, url, checkedAt, chartDate, note },  // JAL特典 片道/往復
  memo, updatedAt, addedAt }
```
`meta/status` `{lastRunAt, summary, coverage}` / `meta/miles` `{balance, asOf, card}`

価格データは、毎朝のスケジュールタスク(Cowork 側で登録済み)が Trip.com の公開ページ
`https://jp.trip.com/flights/nagoya-to-<都市>/airfares-ngo-<code>/` を読んで `today` などを書き換える。
ページ側のコードは価格を取りに行かない(表示と編集だけ)。

**DBの形を変えるときは、このスケジュールタスクの指示文も合わせて直す必要がある。**

## テンプレートの中身(src/page.tpl.html)

上から CSS → HTML → JS の順。JS は1つの即時関数の中にあり、状態はモジュール内変数。

| 画面の部分 | CSS の目印 | 描画関数 |
|---|---|---|
| 上部の帯(ロゴ・最終更新) | `/* ---- masthead ---- */` | `renderMeta` |
| トップ(見出し・3つの数字・絞り込みキー・地球儀) | `/* v7: night hero + globe */` | `renderHeroKpi`, `renderKeys`, `Globe`(canvas) |
| 平面の世界地図 | `/* ---- atlas ---- */` | `renderMap`, `renderRings`, `declutter`, `renderLegend` |
| 搭乗券(右の縦長パネル) | `/* ---- boarding pass ---- */`, `/* v7: boarding pass */` | `renderPass`, `layoverEl`, `searchEl`, `editorEl`, `fareCards`, `barcodeEl` |
| 発着案内(一覧表) | `/* ---- board ---- */` | `renderBoard`, `renderCompare`, `toggleCmp` |
| 行き先を追加 | `/* ---- add ---- */` | `renderAdd`, `renderAddResults`, `addDest` |
| マイルで行ける範囲 | `/* ---- miles ---- */` | `renderMiles`(残高チケット), `renderMilesSec` |

- 全体の再描画は `render()`。状態を変えたら基本これを呼ぶ
- 主な状態: `mode`(today/spring/summer), `filt`, `boardQ`(検索語), `sortKey`, `sel`(選択中の行き先id), `cmp`(比較中 最大3), `optSel`, `edit`, `view`(地図のズーム)
- 要素は `h(tag, props, ...children)` で作る(`'svg:path'` のように書くとSVG要素)。`innerHTML` は使っていない。DBの文字列をそのままHTMLに入れないため、この方針を保つ
- 価格の色分けは `computeTiers` → `tierOf(price)` が返す `cheap/mid/high/none`(表示中の行き先の3分位)

## 見た目の決まりごと

- 世界観は「空港の発着案内板と搭乗券」+「運航管制の画面」。**計器(地図・地球儀・発着案内・トップ帯)は常に暗い画面、紙もの(搭乗券・マイル・追加フォーム)はテーマに従う**
- 暗い計器の色は `--m-*`(`--m-cheap` など)。テーマ追従の面では `--cheap` などを使う。混ぜない
- 文字: 見出し Shippori Mincho B1 / 本文 Inter + Zen Kaku Gothic New / 数字・コード IBM Plex Mono(`--serif` `--sans` `--dot`)。数字は等幅(tabular-nums)
- 影は `--e1` `--e2` `--e3` の3段階だけ。角丸・枠・影を全部の箱に一律で付けない
- 絵文字は使わない。紫グラデーション、すりガラス多用など「AIっぽいテンプレ」には寄せない

## 確認のしかた(公開前に毎回)

1. `python3 build.py --preview` → `dist/preview.html` を開く
2. 画面幅 1440 / 1200 / 390 の3つ、ライトとダークで見る(発着案内は 1320px と 820px で列数が変わる)
3. コンソールにエラーが出ていないこと
4. 触って確かめる: 行き先を選ぶ(地図・一覧・地球儀の点)/ 検索・並び替え / 比較3件 / 「残り13件を表示」/ 経路の編集 / 地図の拡大縮小 / マイル残高の更新

## 経緯と未着手のこと

- V5: 検索・並び替え・比較 / V6: 地図・発着案内・マイル欄を作り直し / V7: トップを暗い帯+回る地球儀に、搭乗券と時期カードを刷新
- V8(スマホ改善): 固定ヘッダー、横スクロールの絞り込みキー、地図の初期ズーム、搭乗券の乗継/検索を折りたたみ、選択時に搭乗券へ自動スクロール
- 未着手: ホテル価格の取得(信頼できる取得元が未確定で、現在はほぼ空)
- 商品化(副業向けの別バージョン)は**この個人用とは別のプロジェクトで進める**方針。ここでは個人用だけを扱う
