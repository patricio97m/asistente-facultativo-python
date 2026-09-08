// Asistente Facultativo - Frontend SPA Logic
const API_BASE = 'http://localhost:8080/api/v1';

// Global App State
let appState = {
  subjects: [],
  selectedSubjectIds: [],
  currentSimulationId: null,
  lastPrediction: null
};

// DOM Elements
const apiStatus = document.getElementById('apiStatus');
const profileForm = document.getElementById('profileForm');
const profileMsg = document.getElementById('profileMsg');
const subjectsList = document.getElementById('subjectsList');
const btnSimulate = document.getElementById('btnSimulate');

const predictionPlaceholder = document.getElementById('predictionPlaceholder');
const predictionResults = document.getElementById('predictionResults');
const overloadBanner = document.getElementById('overloadBanner');
const valNivelRiesgo = document.getElementById('valNivelRiesgo');
const valEstudioDiario = document.getElementById('valEstudioDiario');
const valProbPromedio = document.getElementById('valProbPromedio');
const subjectPredictionsList = document.getElementById('subjectPredictionsList');
const btnGeneratePlan = document.getElementById('btnGeneratePlan');

const planPlaceholder = document.getElementById('planPlaceholder');
const planResults = document.getElementById('planResults');
const planGrid = document.getElementById('planGrid');

const btnPresetBalanced = document.getElementById('btnPresetBalanced');
const btnPresetOverload = document.getElementById('btnPresetOverload');

// Initialize App
document.addEventListener('DOMContentLoaded', () => {
  checkApiHealth();
  loadProfile();
  loadSubjects();

  // Event Listeners
  profileForm.addEventListener('submit', handleSaveProfile);
  btnSimulate.addEventListener('click', handleRunSimulation);
  btnGeneratePlan.addEventListener('click', handleGeneratePlan);
  btnPresetBalanced.addEventListener('click', applyBalancedPreset);
  btnPresetOverload.addEventListener('click', applyOverloadPreset);
});

// Check if Backend API on localhost:8080 is reachable
async function checkApiHealth() {
  try {
    const res = await fetch(`${API_BASE}/subjects/`);
    if (res.ok) {
      apiStatus.innerHTML = `
        <span class="status-dot online"></span>
        <span class="status-text">Backend API Conectado (localhost:8080)</span>
      `;
    } else {
      throw new Error('API Response Error');
    }
  } catch (err) {
    apiStatus.innerHTML = `
      <span class="status-dot offline"></span>
      <span class="status-text">Error de Conexión (Asegúrate de que Docker esté corriendo en puerto 8080)</span>
    `;
  }
}

// 1. Profile Handlers
async function loadProfile() {
  try {
    const res = await fetch(`${API_BASE}/profile/`);
    if (res.ok) {
      const data = await res.json();
      document.getElementById('promedioGeneral').value = data.promedio_general || 7.5;
      document.getElementById('horasTrabajo').value = data.horas_trabajo_semanal || 20;
      document.getElementById('horasSueno').value = data.horas_sueno_objetivo || 7.5;
    }
  } catch (err) {
    console.warn('Could not load profile:', err);
  }
}

async function handleSaveProfile(e) {
  e.preventDefault();
  const payload = {
    promedio_general: parseFloat(document.getElementById('promedioGeneral').value),
    horas_trabajo_semanal: parseFloat(document.getElementById('horasTrabajo').value),
    horas_sueno_objetivo: parseFloat(document.getElementById('horasSueno').value)
  };

  try {
    const res = await fetch(`${API_BASE}/profile/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    if (res.ok) {
      showMsg(profileMsg, '¡Perfil guardado correctamente!', 'success');
    } else {
      showMsg(profileMsg, 'Error al actualizar perfil', 'error');
    }
  } catch (err) {
    showMsg(profileMsg, 'Error de comunicación con la API', 'error');
  }
}

// 2. Subjects Handlers
async function loadSubjects() {
  try {
    const res = await fetch(`${API_BASE}/subjects/`);
    if (res.ok) {
      appState.subjects = await res.json();
      renderSubjectsList();
    } else {
      subjectsList.innerHTML = `<p class="alert-msg error">Error al cargar materias de la API.</p>`;
    }
  } catch (err) {
    subjectsList.innerHTML = `<p class="alert-msg error">No se pudo conectar a ${API_BASE}/subjects/</p>`;
  }
}

function renderSubjectsList() {
  if (appState.subjects.length === 0) {
    subjectsList.innerHTML = `<p style="text-align:center; color: var(--text-muted);">No hay materias registradas.</p>`;
    return;
  }

  subjectsList.innerHTML = appState.subjects.map(subj => {
    const isSelected = appState.selectedSubjectIds.includes(subj.id);
    return `
      <label class="subject-item ${isSelected ? 'selected' : ''}">
        <input type="checkbox" value="${subj.id}" ${isSelected ? 'checked' : ''} onchange="toggleSubjectSelection(${subj.id})">
        <div class="subject-info">
          <span class="subject-name">[${subj.codigo}] ${subj.nombre}</span>
          <span class="subject-meta">Cursada: ${subj.horas_cursada_semanal}h/sem | Promedio Promoción Histórico: ${subj.promedio_historico_promocion} pts</span>
        </div>
      </label>
    `;
  }).join('');
}

window.toggleSubjectSelection = function (id) {
  if (appState.selectedSubjectIds.includes(id)) {
    appState.selectedSubjectIds = appState.selectedSubjectIds.filter(item => item !== id);
  } else {
    appState.selectedSubjectIds.push(id);
  }
  renderSubjectsList();
};

function applyBalancedPreset() {
  document.getElementById('promedioGeneral').value = 8.0;
  document.getElementById('horasTrabajo').value = 20;
  document.getElementById('horasSueno').value = 8.0;
  // Select 3 subjects
  appState.selectedSubjectIds = appState.subjects.slice(0, 3).map(s => s.id);
  renderSubjectsList();
}

function applyOverloadPreset() {
  document.getElementById('promedioGeneral').value = 5.0;
  document.getElementById('horasTrabajo').value = 48; // Heavy work load
  document.getElementById('horasSueno').value = 8.0;
  // Select all 7 subjects
  appState.selectedSubjectIds = appState.subjects.map(s => s.id);
  renderSubjectsList();
}

// 3. ML Simulation Handlers
async function handleRunSimulation() {
  if (appState.selectedSubjectIds.length === 0) {
    alert('Por favor selecciona al menos una materia para simular.');
    return;
  }

  btnSimulate.disabled = true;
  btnSimulate.innerHTML = '⏳ Ejecutando modelos LightGBM...';

  const payload = {
    subject_ids: appState.selectedSubjectIds,
    horas_trabajo_semanal: parseFloat(document.getElementById('horasTrabajo').value),
    horas_sueno_objetivo: parseFloat(document.getElementById('horasSueno').value),
    promedio_general: parseFloat(document.getElementById('promedioGeneral').value)
  };

  try {
    const res = await fetch(`${API_BASE}/simulations/predict/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    if (res.ok) {
      const data = await res.json();
      appState.lastPrediction = data;
      appState.currentSimulationId = data.simulation_id;
      renderPredictionResults(data);
    } else {
      alert('Error en la respuesta de la simulación.');
    }
  } catch (err) {
    alert('Error al comunicar con el motor de ML.');
  } finally {
    btnSimulate.disabled = false;
    btnSimulate.innerHTML = '🚀 Simular Cuatrimestre con LightGBM';
  }
}

function renderPredictionResults(data) {
  predictionPlaceholder.classList.add('hidden');
  predictionResults.classList.remove('hidden');

  // Risk & Metrics
  valNivelRiesgo.textContent = data.nivel_riesgo;
  valNivelRiesgo.style.color = data.nivel_riesgo === 'Alto' ? '#ef4444' : data.nivel_riesgo === 'Equilibrado' ? '#f59e0b' : '#10b981';

  valEstudioDiario.textContent = `${data.horas_estudio_sugeridas_dia} h/día`;
  valProbPromedio.textContent = `${Math.round(data.promedio_probabilidad_promocion * 100)}%`;

  // Overload Banner
  if (data.alerta_sobrecarga) {
    overloadBanner.className = 'alert-banner danger';
    document.getElementById('overloadTitle').textContent = '⚠️ ALERTA DE SOBRECARGA HORARIA SEVERA';
    document.getElementById('overloadDesc').textContent = `Tus compromisos totales equivalen a ${data.resumen_horas_semanales.horas_totales_ocupadas} horas semanales (superando el límite del reloj de 168h). ¡Se recomienda reducir materias o ajustar disponibilidad!`;
    overloadBanner.classList.remove('hidden');
  } else {
    overloadBanner.className = 'alert-banner success';
    document.getElementById('overloadTitle').textContent = '✅ CARGA HORARIA EQUILIBRADA Y FACTIBLE';
    document.getElementById('overloadDesc').textContent = `Tus compromisos semanales suman ${data.resumen_horas_semanales.horas_totales_ocupadas}h de 168h. Cuentas con ${data.resumen_horas_semanales.horas_libres_disponibles}h de tiempo libre semanal.`;
    overloadBanner.classList.remove('hidden');
  }

  // Hours Breakdown Progress Bar
  const resumen = data.resumen_horas_semanales;
  const total = resumen.horas_totales_ocupadas > 168 ? resumen.horas_totales_ocupadas : 168;

  const pctCursada = (resumen.horas_cursada / total) * 100;
  const pctEstudio = (resumen.horas_estudio / total) * 100;
  const pctTrabajo = (resumen.horas_trabajo / total) * 100;
  const pctSueno = (resumen.horas_sueno / total) * 100;

  document.getElementById('barCursada').style.width = `${pctCursada}%`;
  document.getElementById('barEstudio').style.width = `${pctEstudio}%`;
  document.getElementById('barTrabajo').style.width = `${pctTrabajo}%`;
  document.getElementById('barSueno').style.width = `${pctSueno}%`;

  document.getElementById('hoursLegend').innerHTML = `
    <div class="legend-item"><span class="legend-dot" style="background:#3b82f6"></span> Cursada: ${resumen.horas_cursada}h</div>
    <div class="legend-item"><span class="legend-dot" style="background:#8b5cf6"></span> Estudio ML: ${resumen.horas_estudio}h</div>
    <div class="legend-item"><span class="legend-dot" style="background:#f59e0b"></span> Trabajo: ${resumen.horas_trabajo}h</div>
    <div class="legend-item"><span class="legend-dot" style="background:#10b981"></span> Sueño: ${resumen.horas_sueno}h</div>
  `;

  // Subject Predictions List
  subjectPredictionsList.innerHTML = data.materias_predicciones.map(pred => {
    const probPct = Math.round(pred.probabilidad_promocion * 100);
    const color = probPct >= 70 ? '#10b981' : probPct >= 40 ? '#f59e0b' : '#ef4444';

    return `
      <div class="subject-pred-card">
        <div class="pred-header">
          <strong>[${pred.codigo}] ${pred.nombre}</strong>
          <span class="pred-prob-badge" style="color: ${color}">Promoción: ${pred.porcentaje_promocion}</span>
        </div>
        <div class="pred-progress-bg">
          <div class="pred-progress-fill" style="width: ${probPct}%; background: ${color}"></div>
        </div>
        <div style="font-size: 0.75rem; color: var(--text-muted); margin-top: 0.35rem;">
          Estudio recomendado: <strong>${pred.horas_estudio_sugeridas_dia_materia} hrs/día</strong>
        </div>
      </div>
    `;
  }).join('');
}

// 4. Study Plan & Feedback Handlers
async function handleGeneratePlan() {
  if (!appState.currentSimulationId) return;

  btnGeneratePlan.disabled = true;
  btnGeneratePlan.textContent = '⏳ Generando cronograma...';

  try {
    const res = await fetch(`${API_BASE}/study-plans/generate/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ simulation_id: appState.currentSimulationId })
    });

    if (res.ok) {
      const data = await res.json();
      renderStudyPlan(data.plan_semanal);
    } else {
      alert('Error al generar el plan de estudio.');
    }
  } catch (err) {
    alert('Error al conectar con la API.');
  } finally {
    btnGeneratePlan.disabled = false;
    btnGeneratePlan.textContent = '📅 Generar Cronograma Semanal Día a Día';
  }
}

function renderStudyPlan(items) {
  planPlaceholder.classList.add('hidden');
  planResults.classList.remove('hidden');

  planGrid.innerHTML = items.map(item => `
    <div class="day-card" id="card-item-${item.id}">
      <div class="day-header">
        <span class="day-title">📆 ${item.dia_semana}</span>
        <span class="badge ${item.cumplido ? 'badge-info' : ''}">${item.cumplido ? '✅ Cumplido' : '⏳ Pendiente'}</span>
      </div>
      <div class="day-subject">
        ${item.materia_nombre} ${item.materia_codigo ? `(${item.materia_codigo})` : ''}
      </div>
      <div style="font-size: 0.8rem; color: var(--text-muted); margin-top: 0.25rem;">
        Horas asignadas: <strong>${item.horas_asignadas} hrs</strong>
      </div>

      <div class="feedback-form">
        <label class="feedback-check">
          <input type="checkbox" id="chk-${item.id}" ${item.cumplido ? 'checked' : ''}>
          Cumplido
        </label>
        <input type="number" id="hrs-${item.id}" placeholder="Horas reales" step="0.5" value="${item.horas_reales_estudiadas || item.horas_asignadas}">
        <input type="text" id="res-${item.id}" placeholder="Comentario / Nota" value="${item.resultado_obtenido || ''}">
        <button type="button" class="btn btn-primary btn-sm" onclick="sendFeedback(${item.id})">Guardar</button>
      </div>
    </div>
  `).join('');
}

window.sendFeedback = async function (itemId) {
  const cumplido = document.getElementById(`chk-${itemId}`).checked;
  const horas_reales = parseFloat(document.getElementById(`hrs-${itemId}`).value);
  const resultado = document.getElementById(`res-${itemId}`).value;

  const payload = {
    cumplido: cumplido,
    horas_reales_estudiadas: horas_reales,
    resultado_obtenido: resultado
  };

  try {
    const res = await fetch(`${API_BASE}/study-plans/${itemId}/feedback/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    if (res.ok) {
      const updated = await res.json();
      alert(`¡Feedback registrado para ${updated.dia_semana}!`);
    } else {
      alert('Error al enviar feedback.');
    }
  } catch (err) {
    alert('Error al conectar con la API.');
  }
};

// Helper message display
function showMsg(el, text, type) {
  el.textContent = text;
  el.className = `alert-msg ${type}`;
  setTimeout(() => {
    el.textContent = '';
    el.className = 'alert-msg';
  }, 4000);
}
