
const chatbox = document.getElementById("chatbox");
const input = document.getElementById("pregunta");
const btn = document.getElementById("btnEnviar");
const sonido = document.getElementById("sonido");
const shortMode = document.getElementById("shortMode");
const btnReindex = document.getElementById("btnReindex");

function addUserMessage(text){
  const msg = document.createElement("div");
  msg.className = "mensaje user";
  msg.innerHTML = `<div class="burbuja">${text}</div>`;
  chatbox.appendChild(msg); chatbox.scrollTop = chatbox.scrollHeight;
}
function addBotMessage(text){
  const msg = document.createElement("div");
  msg.className = "mensaje bot";
  msg.innerHTML = `<div class="burbuja">${text}</div>`;
  chatbox.appendChild(msg); chatbox.scrollTop = chatbox.scrollHeight; try{sonido.currentTime=0;sonido.play();}catch(e){}
}
async function enviar(){
  const pregunta = input.value.trim(); if(!pregunta) return;
  addUserMessage(pregunta); input.value = "";
  const resp = await fetch("/chat",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({pregunta, short: shortMode.checked})});
  const data = await resp.json(); addBotMessage(data.respuesta || "Tu pregunta ha sido recibida.");
}
btn.addEventListener("click", enviar);
input.addEventListener("keydown", (e)=>{ if(e.key==="Enter"){enviar();} });

if(btnReindex){
  btnReindex.addEventListener("click", async ()=>{
    const r = await fetch("/reindex",{method:"POST"});
    const data = await r.json();
    addBotMessage(data.ok ? "✅ Reindexado con éxito." : ("❌ " + (data.msg || "Error al reindexar")));
  });
}
