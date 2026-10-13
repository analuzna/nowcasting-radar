import json
from pathlib import Path

RUTA_JSON = "notebooks/cataogo_eventos.json"   # ojo: ¿"cataogo" es "catalogo"?
SALIDA = "calendario_interactivo.html"

fechas = json.load(open(RUTA_JSON, encoding="utf-8"))

HTML = r"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Fechas identificadas</title>
<style>
  :root { --rojo:#d9534f; --gris:#888; }
  body { font-family: system-ui, sans-serif; margin: 24px; color:#222; }
  h1 { text-align:center; margin:0 0 12px; }
  .selector { text-align:center; margin-bottom:20px; }
  .selector button { padding:6px 14px; margin:0 4px; border:1px solid #ccc;
    background:#fff; border-radius:6px; cursor:pointer; font-size:14px; }
  .selector button.activo { background:var(--rojo); color:#fff; border-color:var(--rojo); }
  .grilla { display:grid; grid-template-columns:repeat(3, 1fr); gap:24px;
    max-width:1200px; margin:0 auto; }
  @media (max-width:900px){ .grilla{ grid-template-columns:repeat(2,1fr);} }
  @media (max-width:600px){ .grilla{ grid-template-columns:1fr;} }
  .mes { border:1px solid #e3e3e3; border-radius:10px; padding:12px; }
  .mes h3 { margin:0 0 8px; text-align:center; }
  .dias { display:grid; grid-template-columns:repeat(7, 1fr); gap:4px;
    text-align:center; }
  .enc { font-size:12px; color:var(--gris); font-weight:600; }
  .d { aspect-ratio:1; display:flex; align-items:center; justify-content:center;
    font-size:14px; border-radius:50%; }
  .d.marcado { background:var(--rojo); color:#fff; font-weight:700; font-size:18px;
    cursor:pointer; transition:transform .12s; }
  .d.marcado:hover { transform:scale(1.2); box-shadow:0 2px 8px rgba(0,0,0,.3); }
  .nota { margin-top:8px; font-size:13px; color:var(--rojo); min-height:1em; }
  #tip { position:fixed; pointer-events:none; background:#222; color:#fff;
    padding:6px 10px; border-radius:6px; font-size:13px; max-width:260px;
    display:none; z-index:10; }
  .pie { text-align:center; margin-top:24px; color:#444; }
</style>
</head>
<body>
<h1 id="titulo"></h1>
<div class="selector" id="selector"></div>
<div class="grilla" id="grilla"></div>
<p class="pie">En rojo: fechas identificadas. Revisar si existen eventos adicionales.</p>
<div id="tip"></div>

<script>
const DATA = __DATA__;
const MESES = ["Enero","Febrero","Marzo","Abril","Mayo","Junio","Julio",
               "Agosto","Septiembre","Octubre","Noviembre","Diciembre"];
const DIAS = ["L","M","X","J","V","S","D"];
const ORDEN = [9,10,11,12,1,2,3,4,5];          // septiembre a mayo
const tip = document.getElementById("tip");

function render(ciclo) {
  document.getElementById("titulo").textContent =
    `Fechas identificadas — ${ciclo}/${ciclo + 1}`;
  const grilla = document.getElementById("grilla");
  grilla.innerHTML = "";

  for (const mes of ORDEN) {
    const anio = mes >= 9 ? ciclo : ciclo + 1;
    const datos = (DATA[anio] || {})[String(mes).padStart(2, "0")] || {};
    const marcados = new Set(datos.dias || []);
    const nota = datos.nota || "";

    const cont = document.createElement("div");
    cont.className = "mes";
    cont.innerHTML = `<h3>${MESES[mes-1]} ${anio}</h3>`;

    const dias = document.createElement("div");
    dias.className = "dias";
    DIAS.forEach(d => dias.insertAdjacentHTML("beforeend",
      `<div class="enc">${d}</div>`));

    const offset = (new Date(anio, mes-1, 1).getDay() + 6) % 7;  // lunes = 0
    const ndias = new Date(anio, mes, 0).getDate();
    for (let i = 0; i < offset; i++) dias.insertAdjacentHTML("beforeend", "<div></div>");

    for (let d = 1; d <= ndias; d++) {
      const el = document.createElement("div");
      el.className = "d" + (marcados.has(d) ? " marcado" : "");
      el.textContent = d;
      if (marcados.has(d)) {
        const texto = `${d} de ${MESES[mes-1]} ${anio}` + (nota ? ` — ${nota}` : "");
        el.addEventListener("mousemove", e => {
          tip.textContent = texto;
          tip.style.display = "block";
          tip.style.left = (e.clientX + 14) + "px";
          tip.style.top = (e.clientY + 14) + "px";
        });
        el.addEventListener("mouseleave", () => tip.style.display = "none");
      }
      dias.appendChild(el);
    }
    cont.appendChild(dias);
    cont.insertAdjacentHTML("beforeend",
      `<div class="nota">${nota ? "Nota: " + nota : ""}</div>`);
    grilla.appendChild(cont);
  }
  document.querySelectorAll("#selector button").forEach(b =>
    b.classList.toggle("activo", Number(b.dataset.ciclo) === ciclo));
}

const ciclos = Object.keys(DATA).map(Number).sort();
const sel = document.getElementById("selector");
ciclos.forEach(c => {
  const b = document.createElement("button");
  b.dataset.ciclo = c;
  b.textContent = `${c}/${c+1}`;
  b.onclick = () => render(c);
  sel.appendChild(b);
});
render(ciclos[0]);
</script>
</body>
</html>
"""

html = HTML.replace("__DATA__", json.dumps(fechas, ensure_ascii=False))
Path(SALIDA).write_text(html, encoding="utf-8")
print(f"Generado {SALIDA}")