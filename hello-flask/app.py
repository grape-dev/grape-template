"""心情追踪器 —— 极简 Flask Web 应用"""
from datetime import datetime
from flask import Flask, jsonify, request, render_template_string

app = Flask(__name__)

MOODS = [
    {"emoji": "\U0001f600", "label": "\u5f00\u5fc3", "score": 5},
    {"emoji": "\U0001f60a", "label": "\u6109\u60a6", "score": 4},
    {"emoji": "\U0001f610", "label": "\u5e73\u9759", "score": 3},
    {"emoji": "\U0001f61f", "label": "\u4f4e\u843d", "score": 2},
    {"emoji": "\U0001f622", "label": "\u96be\u8fc7", "score": 1},
]

records = []


@app.route("/health")
def health():
    return jsonify({"status": "ok"})


@app.route("/api/moods", methods=["GET"])
def get_moods():
    return jsonify(records)


@app.route("/api/moods", methods=["POST"])
def add_mood():
    data = request.get_json(silent=True) or {}
    score = data.get("score")
    mood = next((m for m in MOODS if m["score"] == score), None)
    if not mood:
        return jsonify({"error": "invalid score, use 1-5"}), 400
    record = {
        "emoji": mood["emoji"],
        "label": mood["label"],
        "score": mood["score"],
        "note": (data.get("note") or "")[:200],
        "time": datetime.now().strftime("%Y-%m-%d %H:%M"),
    }
    records.append(record)
    return jsonify(record), 201


@app.route("/api/stats")
def stats():
    if not records:
        return jsonify({"total": 0, "avg": 0, "distribution": {}})
    total = len(records)
    avg = round(sum(r["score"] for r in records) / total, 2)
    distribution = {}
    for m in MOODS:
        distribution[m["label"]] = sum(1 for r in records if r["score"] == m["score"])
    return jsonify({"total": total, "avg": avg, "distribution": distribution})


PAGE_HTML = """\
<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Mood Tracker</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","Noto Sans SC",sans-serif;background:#f0f2f5;color:#1a1a2e;padding:20px}
.container{max-width:640px;margin:0 auto}
h1{text-align:center;font-size:22px;margin:10px 0 6px}
.sub{text-align:center;color:#888;font-size:13px;margin-bottom:18px}
.card{background:#fff;border-radius:12px;padding:18px;margin-bottom:14px;box-shadow:0 1px 3px rgba(0,0,0,.06)}
.mood-pick{display:flex;justify-content:space-around;flex-wrap:wrap;gap:8px}
.mood-btn{font-size:30px;border:none;background:none;cursor:pointer;padding:6px 12px;border-radius:10px;transition:all .15s}
.mood-btn:hover{background:#e8eaf6;transform:scale(1.1)}
.mood-btn.sel{background:#e8eaf6;box-shadow:0 0 0 2px #3168e0}
.note-input{width:100%;margin-top:10px;padding:8px 12px;border:1px solid #e0e0e0;border-radius:8px;font-size:13px;outline:none}
.note-input:focus{border-color:#3168e0}
.submit-btn{width:100%;margin-top:10px;padding:9px;border:none;border-radius:8px;background:#3168e0;color:#fff;font-size:14px;font-weight:500;cursor:pointer}
.submit-btn:hover{background:#2556c2}
.submit-btn:disabled{background:#ccc;cursor:not-allowed}
.stat-row{display:flex;gap:12px;margin-bottom:10px}
.stat-box{flex:1;text-align:center;background:#f8f9fa;border-radius:8px;padding:10px}
.stat-val{font-size:20px;font-weight:700;color:#3168e0}
.stat-lbl{font-size:11px;color:#888;margin-top:2px}
.bar-chart{display:flex;flex-direction:column;gap:5px}
.bar-row{display:flex;align-items:center;gap:8px;font-size:12px}
.bar-label{width:40px;text-align:right;color:#666}
.bar-track{flex:1;height:18px;background:#f0f0f0;border-radius:4px;overflow:hidden}
.bar-fill{height:100%;border-radius:4px;transition:width .3s}
.bar-count{width:24px;text-align:left;color:#888}
.list-item{display:flex;align-items:center;gap:10px;padding:8px 0;border-bottom:1px solid #f0f0f0}
.list-item:last-child{border:none}
.list-emoji{font-size:22px}
.list-info{flex:1}
.list-label{font-weight:500;font-size:13px}
.list-note{font-size:12px;color:#888}
.list-time{font-size:11px;color:#bbb}
.empty{text-align:center;color:#ccc;padding:20px;font-size:13px}
.guide{border:1px dashed #3168e0;border-radius:8px;padding:14px;margin-top:10px}
.guide h3{font-size:13px;color:#3168e0;margin-bottom:8px}
.guide ol{font-size:12px;color:#555;padding-left:18px;line-height:1.8}
</style>
</head>
<body>
<div class="container">
<h1>\U0001f4cb Mood Tracker</h1>
<p class="sub">\u8bb0\u5f55\u4f60\u7684\u5fc3\u60c5\uff0c\u67e5\u770b\u7edf\u8ba1\u8d8b\u52bf</p>

<div class="card">
<div class="mood-pick" id="moodPick">
{{ MOODS }}
</div>
<input class="note-input" id="noteInput" placeholder="\u5907\u6ce8\uff08\u53ef\u9009\uff09\uff0c\u5982\uff1a\u4eca\u5929\u5b8c\u6210\u4e86\u4e00\u4e2a\u6709\u8da3\u7684\u529f\u80fd" maxlength="200">
<button class="submit-btn" id="submitBtn" disabled>\u8bb0\u5f55\u5fc3\u60c5</button>
</div>

<div class="card" id="statsCard" style="display:none">
<h2 style="font-size:15px;margin-bottom:10px">\U0001f4ca \u5fc3\u60c5\u7edf\u8ba1</h2>
<div class="stat-row" id="statRow"></div>
<div class="bar-chart" id="barChart"></div>
</div>

<div class="card">
<h2 style="font-size:15px;margin-bottom:10px">\U0001f4dd \u5fc3\u60c5\u5217\u8868</h2>
<div id="moodList"><p class="empty">\u8fd8\u6ca1\u6709\u8bb0\u5f55\uff0c\u5148\u9009\u4e2a\u5fc3\u60c5\u8bd5\u8bd5\uff01</p></div>
</div>

<div class="guide">
<h3>\U0001f680 Grape \u6d41\u6c34\u7ebf\u6307\u5f15</h3>
<ol>
<li>\u90e8\u7f72\u6210\u529f\u540e\uff0c\u5728 GitCode \u4ed3\u5e93 Issue \u4e2d\u65b0\u5efa\uff1a<span style="color:#3168e0">\u65b0\u589e /api/export \u7aef\u70b9\uff0c\u652f\u6301\u65e5\u671f\u8fc7\u6ee4\u5bfc\u51fa JSON</span></li>
<li>\u89c2\u5bdf\u6d41\u6c34\u7ebf\u81ea\u52a8\u5206\u6790 \u2192 \u7f16\u7801 \u2192 \u5ba1\u67e5 \u2192 \u90e8\u7f72\u7684\u5168\u8fc7\u7a0b</li>
<li>\u518d\u65b0\u5efa\uff1a<span style="color:#3168e0">\u4e3a /api/export \u8865\u5145\u5355\u5143\u6d4b\u8bd5</span>\uff0c\u4f53\u9a8c\u6d4b\u8bd5\u9a71\u52a8\u5f00\u53d1</li>
</ol>
</div>
</div>
<script>
var selScore=0;
var MOODS={{ MOODS_JSON }};
var COLORS={5:'#4caf50',4:'#8bc34a',3:'#ffc107',2:'#ff9800',1:'#f44336'};
function renderPicker(){
  var h='';
  MOODS.forEach(function(m){
    h+='<button class="mood-btn" data-score="'+m.score+'" onclick="pick('+m.score+')">'+m.emoji+'<div style="font-size:11px;color:#888">'+m.label+'</div></button>';
  });
  document.getElementById('moodPick').innerHTML=h;
}
function pick(s){
  selScore=s;
  document.querySelectorAll('.mood-btn').forEach(function(b){
    b.classList.toggle('sel',+b.dataset.score===s);
  });
  document.getElementById('submitBtn').disabled=false;
}
function submit(){
  if(!selScore)return;
  var note=document.getElementById('noteInput').value.trim();
  fetch('/api/moods',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({score:selScore,note:note})})
  .then(function(r){return r.json()})
  .then(function(){selScore=0;document.getElementById('noteInput').value='';document.querySelectorAll('.mood-btn').forEach(function(b){b.classList.remove('sel')});document.getElementById('submitBtn').disabled=true;loadAll()})
  .catch(function(e){alert('\u63d0\u4ea4\u5931\u8d25: '+e)});
}
function loadAll(){
  Promise.all([fetch('/api/moods').then(function(r){return r.json()}),fetch('/api/stats').then(function(r){return r.json()})])
  .then(function(d){
    var moods=d[0],st=d[1];
    renderList(moods);
    renderStats(st);
  });
}
function renderList(moods){
  var el=document.getElementById('moodList');
  if(!moods.length){el.innerHTML='<p class="empty">\u8fd8\u6ca1\u6709\u8bb0\u5f55\uff0c\u5148\u9009\u4e2a\u5fc3\u60c5\u8bd5\u8bd5\uff01</p>';return}
  el.innerHTML=moods.slice().reverse().map(function(r){
    return '<div class="list-item"><span class="list-emoji">'+r.emoji+'</span><div class="list-info"><div class="list-label">'+r.label+(r.note?' <span style="color:#999">\u00b7 '+r.note+'</span>':'')+'</div></div><span class="list-time">'+r.time+'</span></div>';
  }).join('');
}
function renderStats(st){
  if(!st.total){document.getElementById('statsCard').style.display='none';return}
  document.getElementById('statsCard').style.display='block';
  document.getElementById('statRow').innerHTML=
    '<div class="stat-box"><div class="stat-val">'+st.total+'</div><div class="stat-lbl">\u8bb0\u5f55\u6570</div></div>'+
    '<div class="stat-box"><div class="stat-val">'+st.avg+'</div><div class="stat-lbl">\u5e73\u5747\u5fc3\u60c5</div></div>';
  var max=Math.max.apply(null,Object.values(st.distribution));
  var bars='';
  MOODS.forEach(function(m){
    var cnt=st.distribution[m.label]||0;
    var pct=max?Math.round(cnt/max*100):0;
    bars+='<div class="bar-row"><span class="bar-label">'+m.label+'</span><div class="bar-track"><div class="bar-fill" style="width:'+pct+'%;background:'+COLORS[m.score]+'"></div></div><span class="bar-count">'+cnt+'</span></div>';
  });
  document.getElementById('barChart').innerHTML=bars;
}
renderPicker();
loadAll();
</script>
</body>
</html>
"""


@app.route("/")
def index():
    import json
    picker_html = "".join(
        f'<button class="mood-btn" data-score="{m["score"]}">{m["emoji"]}<div style="font-size:11px;color:#888">{m["label"]}</div></button>'
        for m in MOODS
    )
    return render_template_string(
        PAGE_HTML,
        MOODS=picker_html,
        MOODS_JSON=json.dumps(MOODS, ensure_ascii=False),
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
