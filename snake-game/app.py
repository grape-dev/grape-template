"""贪吃蛇游戏 —— Flask Web 版"""
from flask import Flask, Response, jsonify

app = Flask(__name__)

GAME_HTML = """\
<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Snake Game</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#1a1a2e;color:#e0e0e0;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;display:flex;flex-direction:column;align-items:center;padding:20px;min-height:100vh}
h1{font-size:22px;margin-bottom:4px}
.sub{font-size:12px;color:#888;margin-bottom:16px}
#scoreBar{display:flex;gap:24px;margin-bottom:12px}
.score-box{text-align:center}
.score-val{font-size:24px;font-weight:700;color:#4caf50}
.score-lbl{font-size:11px;color:#666}
canvas{border:2px solid #4caf50;border-radius:8px;background:#16213e;box-shadow:0 0 20px rgba(76,175,80,.15)}
.controls{margin-top:16px;text-align:center}
.controls p{font-size:12px;color:#888;margin-bottom:8px}
.dpad{display:grid;grid-template-columns:repeat(3,48px);grid-template-rows:repeat(3,48px);gap:4px;justify-content:center}
.dpad button{background:#2a2a4e;border:1px solid #4caf50;color:#4caf50;font-size:18px;border-radius:8px;cursor:pointer;display:flex;align-items:center;justify-content:center}
.dpad button:active{background:#4caf50;color:#fff}
.dpad .empty{visibility:hidden}
.btn-row{margin-top:12px}
.btn-row button{padding:8px 24px;border:none;border-radius:8px;font-size:13px;font-weight:500;cursor:pointer;margin:0 4px}
.btn-start{background:#4caf50;color:#fff}
.btn-pause{background:#ff9800;color:#fff}
.overlay{position:fixed;inset:0;background:rgba(0,0,0,.7);display:flex;align-items:center;justify-content:center;z-index:10}
.overlay.hidden{display:none}
.overlay .box{background:#1a1a2e;border:2px solid #4caf50;border-radius:12px;padding:30px 40px;text-align:center}
.overlay .box h2{font-size:20px;color:#f44336;margin-bottom:8px}
.overlay .box p{font-size:14px;color:#888;margin-bottom:16px}
.overlay .box .final-score{font-size:28px;font-weight:700;color:#4caf50;margin-bottom:16px}
</style>
</head>
<body>
<h1>Snake Game</h1>
<p class="sub">经典贪吃蛇游戏 · 方向键控制</p>
<div id="scoreBar">
<div class="score-box"><div class="score-val" id="score">0</div><div class="score-lbl">得分</div></div>
<div class="score-box"><div class="score-val" id="best">0</div><div class="score-lbl">最高分</div></div>
<div class="score-box"><div class="score-val" id="speed">1</div><div class="score-lbl">速度</div></div>
</div>
<canvas id="game" width="400" height="400"></canvas>
<div class="controls">
<p>键盘控制：↑ ↓ ← → 或 WASD · 空格暂停</p>
<div class="dpad">
<div class="empty"></div><button onclick="setDir(0,-1)">▲</button><div class="empty"></div>
<button onclick="setDir(-1,0)">◀</button><div class="empty"></div><button onclick="setDir(1,0)">▶</button>
<div class="empty"></div><button onclick="setDir(0,1)">▼</button><div class="empty"></div>
</div>
<div class="btn-row">
<button class="btn-start" id="startBtn" onclick="startGame()">开始游戏</button>
<button class="btn-pause" id="pauseBtn" onclick="togglePause()" disabled>暂停</button>
</div>
</div>
<div class="overlay hidden" id="gameOver">
<div class="box">
<h2>Game Over</h2>
<p>游戏结束！按"重新开始"再来一局</p>
<div class="final-score" id="finalScore">0</div>
<button class="btn-start" onclick="startGame()">重新开始</button>
</div>
</div>
<script>
var CELL=20,COLS=20,ROWS=20;
var canvas=document.getElementById('game');
var ctx=canvas.getContext('2d');
var snake,dir,nextDir,food,score,best=0,level,timer,paused,running;
function init(){
snake=[{x:10,y:10},{x:9,y:10},{x:8,y:10}];
dir={x:1,y:0};nextDir={x:1,y:0};
score=0;level=1;paused=false;
placeFood();updateUI();
}
function placeFood(){
var valid=false;
while(!valid){
food={x:Math.floor(Math.random()*COLS),y:Math.floor(Math.random()*ROWS)};
valid=!snake.some(function(s){return s.x===food.x&&s.y===food.y});
}
}
function updateUI(){
document.getElementById('score').textContent=score;
document.getElementById('best').textContent=best;
document.getElementById('speed').textContent=level;
}
function setDir(x,y){
if(!running)return;
if(dir.x===-x&&dir.y===-y)return;
if(dir.x===x&&dir.y===y)return;
nextDir={x:x,y:y};
}
function tick(){
if(paused)return;
dir=nextDir;
var head={x:snake[0].x+dir.x,y:snake[0].y+dir.y};
if(head.x<0||head.x>=COLS||head.y<0||head.y>=ROWS||snake.some(function(s){return s.x===head.x&&s.y===head.y})){
gameOver();return;
}
snake.unshift(head);
if(head.x===food.x&&head.y===food.y){
score+=10;
if(score>best)best=score;
if(score%50===0){level++;clearInterval(timer);timer=setInterval(tick,Math.max(60,150-level*10));}
placeFood();
}else{
snake.pop();
}
updateUI();draw();
}
function draw(){
ctx.fillStyle='#16213e';
ctx.fillRect(0,0,canvas.width,canvas.height);
ctx.fillStyle='#f44336';
ctx.beginPath();
ctx.arc(food.x*CELL+CELL/2,food.y*CELL+CELL/2,CELL/2-2,0,Math.PI*2);
ctx.fill();
snake.forEach(function(s,i){
if(i===0){
ctx.fillStyle='#4caf50';
ctx.fillRect(s.x*CELL+1,s.y*CELL+1,CELL-2,CELL-2);
ctx.fillStyle='#2e7d32';
ctx.fillRect(s.x*CELL+4,s.y*CELL+4,CELL-8,CELL-8);
}else{
ctx.fillStyle='#388e3c';
ctx.fillRect(s.x*CELL+2,s.y*CELL+2,CELL-4,CELL-4);
}
});
}
function startGame(){
document.getElementById('gameOver').classList.add('hidden');
document.getElementById('pauseBtn').disabled=false;
document.getElementById('pauseBtn').textContent='暂停';
init();running=true;
clearInterval(timer);
timer=setInterval(tick,150);
draw();
}
function togglePause(){
if(!running)return;
paused=!paused;
document.getElementById('pauseBtn').textContent=paused?'继续':'暂停';
}
function gameOver(){
clearInterval(timer);running=false;
document.getElementById('finalScore').textContent=score;
document.getElementById('gameOver').classList.remove('hidden');
}
document.addEventListener('keydown',function(e){
var k=e.key;
if(k==='ArrowUp'||k==='w'||k==='W')setDir(0,-1);
else if(k==='ArrowDown'||k==='s'||k==='S')setDir(0,1);
else if(k==='ArrowLeft'||k==='a'||k==='A')setDir(-1,0);
else if(k==='ArrowRight'||k==='d'||k==='D')setDir(1,0);
else if(k===' ')togglePause();
e.preventDefault();
});
init();draw();
</script>
</body>
</html>
"""

@app.route("/health")
def health():
    return jsonify({"status": "ok"})


@app.route("/")
def index():
    return Response(GAME_HTML, content_type="text/html; charset=utf-8")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
