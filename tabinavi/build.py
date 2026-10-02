#!/usr/bin/env python3
"""旅ナビ: src/page.tpl.html + data/* -> dist/tabinavi.html (公開用の1ファイル)
   --preview を付けると、fixtures/ のデータを仮のDBとして埋め込んだ
   dist/preview.html も作る(ブラウザで直接開いて確認できる)。"""
import json, sys, glob, os
R = os.path.dirname(os.path.abspath(__file__))
rd = lambda p: open(os.path.join(R, p), encoding='utf8').read()
proj = json.loads(rd('data/proj.json'))
t = rd('src/page.tpl.html')
ap = rd('data/airports.txt').strip()
gl = rd('data/globe.txt').strip()
for s in (ap, gl):
    assert '`' not in s and '${' not in s and '\\' not in s
subs = {'%%SPHERE%%': rd('data/sphere.txt'), '%%GRAT%%': rd('data/grat.txt'), '%%LAND%%': rd('data/land.txt'),
        '%%K%%': repr(proj['k']), '%%TX%%': repr(proj['tx']), '%%TY%%': repr(proj['ty']),
        '%%AIRPORTS%%': ap, '%%GLOBE%%': gl}
for k, v in subs.items():
    assert k in t, k
    t = t.replace(k, v)
assert '%%' not in t.replace('100%%', ''), 'unreplaced placeholder'
os.makedirs(os.path.join(R, 'dist'), exist_ok=True)
open(os.path.join(R, 'dist/tabinavi.html'), 'w', encoding='utf8').write(t)
print('dist/tabinavi.html', len(t.encode('utf8')), 'bytes')

if '--preview' in sys.argv:
    docs = [json.loads(open(f, encoding='utf8').read()) for f in sorted(glob.glob(os.path.join(R, 'fixtures/dest/*.json')))]
    miles = json.loads(rd('fixtures/meta/miles.json')); status = json.loads(rd('fixtures/meta/status.json'))
    fake = """(function(){var store=new Map();var seed=%s;seed.forEach(function(d){store.set('dest/'+d.id,d);});
store.set('meta/miles',%s);store.set('meta/status',%s);
var ls=[];function notify(){ls.forEach(function(l){l();});}
function snap(p){var v=store.get(p);return {id:p.split('/').pop(),exists:!!v,data:function(){return v;}};}
function mk(){return {collection:function(c){return {onSnapshot:function(cb){var f=function(){var docs=[];store.forEach(function(v,k){if(k.indexOf(c+'/')===0)docs.push(snap(k));});cb({docs:docs});};ls.push(f);f();}};},
doc:function(p){return {onSnapshot:function(cb){var f=function(){cb(snap(p));};ls.push(f);f();},
set:async function(d){store.set(p,JSON.parse(JSON.stringify(d)));notify();},
update:async function(d){store.set(p,Object.assign({},store.get(p)||{},JSON.parse(JSON.stringify(d))));notify();},
delete:async function(){store.delete(p);notify();}};}};}
window.claude={use:async function(n){if(n==='db')return mk();if(n==='user')return {canEdit:function(){return true;}};return null;}};})();""" % (
        json.dumps(docs, ensure_ascii=False).replace('</', '<\\/'), json.dumps(miles, ensure_ascii=False), json.dumps(status, ensure_ascii=False))
    html = ('<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">'
            '<style>body{margin:0}img{max-width:100%}[hidden]{display:none!important}</style><script>' + fake + '</script></head><body>' + t + '</body></html>')
    open(os.path.join(R, 'dist/preview.html'), 'w', encoding='utf8').write(html)
    print('dist/preview.html (仮データ入り。編集は保存されません)')
