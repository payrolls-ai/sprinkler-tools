/* ============================================================
   sprinkler-tools demo · frontend logic
   - Renders the blueprint as SVG
   - Calls FastAPI /api/analyze if reachable, else uses offline mock
   - Animates 50 agents working in parallel
   - Drops sprinkler dots when the master agent finishes
   ============================================================ */

const API_BASE = 'http://localhost:8000';

const TEAM_LABELS = {
  structure:    { label: 'Structure',    range: '1–10'  },
  openings:     { label: 'Openings',     range: '11–18' },
  obstructions: { label: 'Obstructions', range: '19–28' },
  classifiers:  { label: 'Classifiers',  range: '29–36' },
  mep:          { label: 'MEP',          range: '37–43' },
  code_math:    { label: 'Code Math',    range: '44–50' },
};

const TEAM_ORDER = ['structure', 'openings', 'obstructions', 'classifiers', 'mep', 'code_math'];

// ─────────────────────────────────────────────────────────────
// Bundled offline fallback (matches the FastAPI demo output)
// ─────────────────────────────────────────────────────────────

const OFFLINE_AGENTS = [
  // Structure
  {agent_id:1, team:'structure', name:'Exterior Wall Detector'},
  {agent_id:2, team:'structure', name:'Partition Wall Detector'},
  {agent_id:3, team:'structure', name:'Structural Column Detector'},
  {agent_id:4, team:'structure', name:'Overhead Beam Detector'},
  {agent_id:5, team:'structure', name:'Ceiling Height Reader'},
  {agent_id:6, team:'structure', name:'Load-Bearing Wall Identifier'},
  {agent_id:7, team:'structure', name:'Shear Wall Detector (Seismic)'},
  {agent_id:8, team:'structure', name:'Wall Material Classifier'},
  {agent_id:9, team:'structure', name:'Slab Edge Finder'},
  {agent_id:10, team:'structure', name:'Foundation Element Detector'},
  // Openings
  {agent_id:11, team:'openings', name:'Door Detector'},
  {agent_id:12, team:'openings', name:'Window Detector'},
  {agent_id:13, team:'openings', name:'Archway Detector'},
  {agent_id:14, team:'openings', name:'Skylight Detector'},
  {agent_id:15, team:'openings', name:'Atrium Detector'},
  {agent_id:16, team:'openings', name:'Curtain Wall Detector'},
  {agent_id:17, team:'openings', name:'Fire-Rated Door Identifier'},
  {agent_id:18, team:'openings', name:'Smoke Barrier Opening (LAMC trigger)'},
  // Obstructions
  {agent_id:19, team:'obstructions', name:'HVAC Duct Detector'},
  {agent_id:20, team:'obstructions', name:'Deep Beam Pocket Detector'},
  {agent_id:21, team:'obstructions', name:'Light Fixture Detector'},
  {agent_id:22, team:'obstructions', name:'Pipe / Conduit Bundle Detector'},
  {agent_id:23, team:'obstructions', name:'Cable Tray Detector'},
  {agent_id:24, team:'obstructions', name:'Storage Rack Detector'},
  {agent_id:25, team:'obstructions', name:'Mezzanine Edge Detector'},
  {agent_id:26, team:'obstructions', name:'Dropped Ceiling Detector'},
  {agent_id:27, team:'obstructions', name:'Soffit Detector'},
  {agent_id:28, team:'obstructions', name:'Floor Equipment Detector'},
  // Classifiers
  {agent_id:29, team:'classifiers', name:'Room Type Classifier'},
  {agent_id:30, team:'classifiers', name:'Hazard Class Assigner'},
  {agent_id:31, team:'classifiers', name:'Wet Area Detector'},
  {agent_id:32, team:'classifiers', name:'High Ceiling Detector'},
  {agent_id:33, team:'classifiers', name:'Concealed Space Detector'},
  {agent_id:34, team:'classifiers', name:'Attic Detector'},
  {agent_id:35, team:'classifiers', name:'Crawl Space Detector'},
  {agent_id:36, team:'classifiers', name:'Exempt Space Marker'},
  // MEP
  {agent_id:37, team:'mep', name:'Main Water Riser Locator'},
  {agent_id:38, team:'mep', name:'Existing Pipe Detector'},
  {agent_id:39, team:'mep', name:'Electrical Room Identifier'},
  {agent_id:40, team:'mep', name:'Mechanical Room Identifier'},
  {agent_id:41, team:'mep', name:'Plumbing Fixture Detector'},
  {agent_id:42, team:'mep', name:'Gas Equipment Detector'},
  {agent_id:43, team:'mep', name:'Elevator Shaft Detector'},
  // Code Math
  {agent_id:44, team:'code_math', name:'Room Area Calculator'},
  {agent_id:45, team:'code_math', name:'Sprinkler Spacing Checker'},
  {agent_id:46, team:'code_math', name:'Coverage Zone Calculator'},
  {agent_id:47, team:'code_math', name:'Wall Distance Checker'},
  {agent_id:48, team:'code_math', name:'Obstruction Distance Checker'},
  {agent_id:49, team:'code_math', name:'Draft Stop Detector'},
  {agent_id:50, team:'code_math', name:'LA Water Curtain Zone'},
];

const OFFLINE_BLUEPRINT = {
  blueprint_id: 'DEMO-LA-001',
  width_ft: 60,
  height_ft: 40,
  rooms: [
    {id:'R1', type:'open_office',  hazard:'Light',    bbox:{x:2,  y:2,  width:28, height:18}},
    {id:'R2', type:'conference',   hazard:'Light',    bbox:{x:32, y:2,  width:14, height:12}},
    {id:'R3', type:'kitchen',      hazard:'Ordinary', bbox:{x:48, y:2,  width:10, height:12}},
    {id:'R4', type:'bathroom',     hazard:'Light',    bbox:{x:32, y:16, width:8,  height:8 }},
    {id:'R5', type:'electrical',   hazard:'Special',  bbox:{x:42, y:16, width:8,  height:8 }},
    {id:'R6', type:'stair',        hazard:'Exempt',   bbox:{x:52, y:16, width:6,  height:8 }},
    {id:'R7', type:'open_office',  hazard:'Light',    bbox:{x:2,  y:22, width:28, height:16}},
    {id:'R8', type:'warehouse',    hazard:'Ordinary', bbox:{x:32, y:26, width:26, height:12}},
  ],
  raw_features: {
    exterior_walls: [
      {x:0,  y:0,  width:60, height:1},
      {x:0,  y:39, width:60, height:1},
      {x:0,  y:0,  width:1,  height:40},
      {x:59, y:0,  width:1,  height:40},
    ],
    partition_walls: [
      {x:30, y:2,  width:1,  height:36},
      {x:47, y:2,  width:1,  height:12},
      {x:32, y:14, width:26, height:1},
      {x:40, y:16, width:1,  height:8},
      {x:50, y:16, width:1,  height:8},
      {x:2,  y:21, width:28, height:1},
      {x:32, y:25, width:26, height:1},
    ],
    columns: [[16,12], [16,30], [44,30]],
    beams: [
      {x:10, y:9,  width:18, height:0.5, depth_in:14},
      {x:10, y:30, width:18, height:0.5, depth_in:12},
    ],
    doors: [[30.5,11], [47.5,8], [36,14.5], [44,14.5], [56,14.5], [30.5,30], [32,25.5]],
    windows: [
      {x:4,  y:0, width:6, height:0.5},
      {x:18, y:0, width:6, height:0.5},
      {x:36, y:0, width:6, height:0.5},
    ],
    smoke_barrier_openings: [{x:30, y:8, width:1.5, height:6}],
    hvac_ducts: [
      {x:6, y:9.5,  width:22, height:1, width_in:24},
      {x:6, y:30.5, width:22, height:1, width_in:24},
    ],
    light_fixtures: [[10,6],[22,6],[10,16],[22,16],[10,26],[22,26],[10,34],[22,34]],
    water_riser: [58, 38],
    water_curtain_zones: [{x:30, y:8, width:1.5, height:6}],
  },
};

// Pre-computed sprinklers (matches the FastAPI master_agent.py output)
const OFFLINE_SPRINKLERS = [
  {sprinkler_id:'S000', x_ft:9,     y_ft:6.5,  room_id:'R1', hazard_class:'Light',    coverage_sqft:126,  reason:'Grid placement for Light hazard',    rules_satisfied:['NFPA-001','NFPA-004']},
  {sprinkler_id:'S001', x_ft:23,    y_ft:6.5,  room_id:'R1', hazard_class:'Light',    coverage_sqft:126,  reason:'Grid placement for Light hazard',    rules_satisfied:['NFPA-001','NFPA-004']},
  {sprinkler_id:'S002', x_ft:9,     y_ft:15.5, room_id:'R1', hazard_class:'Light',    coverage_sqft:126,  reason:'Grid placement for Light hazard',    rules_satisfied:['NFPA-001','NFPA-004']},
  {sprinkler_id:'S003', x_ft:23,    y_ft:15.5, room_id:'R1', hazard_class:'Light',    coverage_sqft:126,  reason:'Grid placement for Light hazard',    rules_satisfied:['NFPA-001','NFPA-004']},
  {sprinkler_id:'S004', x_ft:39,    y_ft:8,    room_id:'R2', hazard_class:'Light',    coverage_sqft:168,  reason:'Grid placement for Light hazard',    rules_satisfied:['NFPA-001','NFPA-004']},
  {sprinkler_id:'S005', x_ft:53,    y_ft:8,    room_id:'R3', hazard_class:'Ordinary', coverage_sqft:120,  reason:'Grid placement for Ordinary hazard', rules_satisfied:['NFPA-002','NFPA-004']},
  {sprinkler_id:'S006', x_ft:36,    y_ft:20,   room_id:'R4', hazard_class:'Light',    coverage_sqft:64,   reason:'Grid placement for Light hazard',    rules_satisfied:['NFPA-001','NFPA-004']},
  {sprinkler_id:'S007', x_ft:9,     y_ft:26,   room_id:'R7', hazard_class:'Light',    coverage_sqft:112,  reason:'Grid placement for Light hazard',    rules_satisfied:['NFPA-001','NFPA-004']},
  {sprinkler_id:'S008', x_ft:23,    y_ft:26,   room_id:'R7', hazard_class:'Light',    coverage_sqft:112,  reason:'Grid placement for Light hazard',    rules_satisfied:['NFPA-001','NFPA-004']},
  {sprinkler_id:'S009', x_ft:9,     y_ft:34,   room_id:'R7', hazard_class:'Light',    coverage_sqft:112,  reason:'Grid placement for Light hazard',    rules_satisfied:['NFPA-001','NFPA-004']},
  {sprinkler_id:'S010', x_ft:23,    y_ft:34,   room_id:'R7', hazard_class:'Light',    coverage_sqft:112,  reason:'Grid placement for Light hazard',    rules_satisfied:['NFPA-001','NFPA-004']},
  {sprinkler_id:'S011', x_ft:36.33, y_ft:32,   room_id:'R8', hazard_class:'Ordinary', coverage_sqft:104,  reason:'Grid placement for Ordinary hazard', rules_satisfied:['NFPA-002','NFPA-004']},
  {sprinkler_id:'S012', x_ft:45,    y_ft:32,   room_id:'R8', hazard_class:'Ordinary', coverage_sqft:104,  reason:'Grid placement for Ordinary hazard', rules_satisfied:['NFPA-002','NFPA-004']},
  {sprinkler_id:'S013', x_ft:53.67, y_ft:32,   room_id:'R8', hazard_class:'Ordinary', coverage_sqft:104,  reason:'Grid placement for Ordinary hazard', rules_satisfied:['NFPA-002','NFPA-004']},
  {sprinkler_id:'S014', x_ft:30.75, y_ft:8,    room_id:'water_curtain', hazard_class:'Special (water curtain)', coverage_sqft:0, reason:'LAMC water curtain at smoke barrier opening', rules_satisfied:['LA-002','LA-003']},
  {sprinkler_id:'S015', x_ft:30.75, y_ft:14,   room_id:'water_curtain', hazard_class:'Special (water curtain)', coverage_sqft:0, reason:'LAMC water curtain at smoke barrier opening', rules_satisfied:['LA-002','LA-003']},
];

const OFFLINE_COMPLIANCE = [
  {rule_id:'NFPA-004', rule_summary:'Minimum 6 ft between adjacent sprinklers', status:'pass',
    detail:'All pairs OK'},
  {rule_id:'CA-001',   rule_summary:'California seismic bracing on sprinkler piping', status:'info',
    detail:'Bracing layout deferred to Phase 8 piping module'},
  {rule_id:'LA-003',   rule_summary:'LAMC water curtain at smoke barrier openings', status:'pass',
    detail:'2 water curtain sprinklers placed across 1 zone(s)'},
];

function buildOfflineFindings() {
  // A representative finding per agent that has visible work in the demo
  const f = (agent_id, team, label, attrs={}, conf=0.92) => ({agent_id, team, label, attributes:attrs, confidence:conf});
  return [
    f(1, 'structure', 'exterior_wall',  {count: 4}, 0.97),
    f(2, 'structure', 'partition_wall', {count: 7}, 0.93),
    f(3, 'structure', 'column',         {count: 3}, 0.95),
    f(4, 'structure', 'beam',           {count: 2, max_depth_in: 14}, 0.88),
    f(5, 'structure', 'ceiling_height', {heights_ft: [9, 11.5, 9]}, 0.99),
    f(11, 'openings', 'door',           {count: 7}, 0.94),
    f(12, 'openings', 'window',         {count: 3}, 0.92),
    f(17, 'openings', 'fire_rated_door',{count: 1, rating_minutes: 60}, 0.81),
    f(18, 'openings', 'smoke_barrier_opening', {count: 1, requires_water_curtain: true}, 0.87),
    f(19, 'obstructions', 'hvac_duct',  {count: 2, width_in: 24, triggers_3x_rule: true}, 0.92),
    f(20, 'obstructions', 'deep_beam',  {count: 1, depth_in: 14}, 0.88),
    f(21, 'obstructions', 'light_fixture', {count: 8}, 0.79),
    f(29, 'classifiers', 'room_type',   {count: 8}, 0.90),
    f(30, 'classifiers', 'hazard_class',{Light: 5, Ordinary: 2, Exempt: 1}, 0.93),
    f(31, 'classifiers', 'wet_area',    {count: 2}, 0.96),
    f(36, 'classifiers', 'exempt_space',{count: 1, type: 'stair'}, 0.94),
    f(37, 'mep', 'water_riser',         {x: 58, y: 38}, 0.97),
    f(39, 'mep', 'electrical_room',     {count: 1, no_water_required: true}, 0.94),
    f(44, 'code_math', 'room_area',     {total_sqft: 1864}, 0.99),
    f(45, 'code_math', 'spacing_constraint', {max_ft: 15, min_ft: 6}, 0.99),
    f(46, 'code_math', 'coverage_constraint', {max_sqft_light: 225}, 0.99),
    f(49, 'code_math', 'draft_stop',    {depth_in: 18, material: 'noncombustible'}, 0.85),
    f(50, 'code_math', 'water_curtain_zone', {max_spacing_ft: 6, rule_triggered: 'LA-003'}, 0.86),
  ];
}

// ─────────────────────────────────────────────────────────────
// State
// ─────────────────────────────────────────────────────────────

const state = {
  agents: [],
  blueprint: null,
  running: false,
  mode: 'offline',  // 'live' if FastAPI is reachable
};

// ─────────────────────────────────────────────────────────────
// API helpers (with offline fallback)
// ─────────────────────────────────────────────────────────────

async function fetchAgents() {
  try {
    const r = await fetch(`${API_BASE}/api/agents`, { signal: AbortSignal.timeout(800) });
    if (!r.ok) throw new Error('bad status');
    state.mode = 'live';
    return await r.json();
  } catch {
    state.mode = 'offline';
    return OFFLINE_AGENTS;
  }
}

async function fetchBlueprint() {
  try {
    const r = await fetch(`${API_BASE}/api/blueprint`, { signal: AbortSignal.timeout(800) });
    if (!r.ok) throw new Error('bad status');
    return await r.json();
  } catch {
    return OFFLINE_BLUEPRINT;
  }
}

async function runAnalysis() {
  if (state.mode === 'live') {
    try {
      const r = await fetch(`${API_BASE}/api/analyze`, { method: 'POST', signal: AbortSignal.timeout(7000) });
      if (r.ok) return await r.json();
    } catch (e) {
      console.warn('Live analysis failed, falling back to offline:', e);
    }
  }
  // Offline path: simulate the run with realistic-ish timing
  await sleep(1100 + Math.random() * 300);
  return {
    blueprint_id: OFFLINE_BLUEPRINT.blueprint_id,
    sprinklers: OFFLINE_SPRINKLERS,
    compliance: OFFLINE_COMPLIANCE,
    agent_reports: OFFLINE_AGENTS.map(a => {
      const finding = buildOfflineFindings().find(f => f.agent_id === a.agent_id);
      return {
        agent_id: a.agent_id, agent_name: a.name, team: a.team,
        status: 'ok',
        findings: finding ? [finding] : [],
        elapsed_ms: 40 + Math.random() * 60,
      };
    }),
    total_elapsed_ms: 1100,
    summary: {
      total_sprinklers: OFFLINE_SPRINKLERS.length,
      agents_ok: 50, agents_failed: 0,
      compliance_pass: 2, compliance_fail: 0,
      total_findings: 23,
    },
  };
}

const sleep = (ms) => new Promise(r => setTimeout(r, ms));

// ─────────────────────────────────────────────────────────────
// Rendering — agents panel
// ─────────────────────────────────────────────────────────────

function renderAgentsPanel(agents) {
  const teamsEl = document.getElementById('teams');
  teamsEl.innerHTML = '';
  for (const team of TEAM_ORDER) {
    const meta = TEAM_LABELS[team];
    const teamAgents = agents.filter(a => a.team === team);
    const teamEl = document.createElement('div');
    teamEl.className = `team team-${team}`;
    teamEl.innerHTML = `
      <div class="team-head">
        <span>${meta.label}</span>
        <span>${meta.range}</span>
      </div>
      <div class="agent-list">
        ${teamAgents.map(a => `
          <span class="agent-chip" data-agent-id="${a.agent_id}" data-status="idle"
                title="${a.name}">${String(a.agent_id).padStart(2, '0')}</span>
        `).join('')}
      </div>`;
    teamsEl.appendChild(teamEl);
  }
}

// ─────────────────────────────────────────────────────────────
// Rendering — blueprint SVG
// ─────────────────────────────────────────────────────────────

const HAZARD_FILLS = {
  Light:    'var(--hazard-light)',
  Ordinary: 'var(--hazard-ordinary)',
  Extra:    'var(--hazard-extra)',
  Special:  'var(--exempt)',
  Exempt:   'var(--exempt)',
};

const ROOM_LABELS = {
  open_office: 'OFFICE',
  conference:  'CONFERENCE',
  kitchen:     'KITCHEN',
  bathroom:    'BATH',
  electrical:  'ELEC',
  stair:       'STAIR',
  warehouse:   'WAREHOUSE',
};

function svg(tag, attrs = {}, parent) {
  const el = document.createElementNS('http://www.w3.org/2000/svg', tag);
  for (const [k, v] of Object.entries(attrs)) el.setAttribute(k, v);
  if (parent) parent.appendChild(el);
  return el;
}

function renderBlueprint(bp) {
  const layerRooms    = document.getElementById('layer-rooms');
  const layerWalls    = document.getElementById('layer-walls');
  const layerFeatures = document.getElementById('layer-features');
  const layerLabels   = document.getElementById('layer-labels');

  // Clear all
  for (const el of [layerRooms, layerWalls, layerFeatures, layerLabels,
                    document.getElementById('layer-sprinklers'),
                    document.getElementById('layer-scan')]) el.innerHTML = '';

  // Rooms
  for (const r of bp.rooms) {
    svg('rect', {
      x: r.bbox.x, y: r.bbox.y, width: r.bbox.width, height: r.bbox.height,
      class: 'room-fill', fill: HAZARD_FILLS[r.hazard] || 'var(--paper-soft)',
      'data-room-id': r.id,
    }, layerRooms);

    const cx = r.bbox.x + r.bbox.width / 2;
    const cy = r.bbox.y + r.bbox.height / 2;
    svg('text', { x: cx, y: cy - 0.3, class: 'room-label', textContent: ROOM_LABELS[r.type] || r.type.toUpperCase() }, layerLabels)
      .textContent = ROOM_LABELS[r.type] || r.type.toUpperCase();
    svg('text', { x: cx, y: cy + 1.1, class: 'room-sublabel' }, layerLabels)
      .textContent = `${r.id} · ${r.hazard}`;
  }

  // Walls
  for (const w of (bp.raw_features.exterior_walls || [])) {
    svg('rect', { x: w.x, y: w.y, width: w.width, height: w.height, class: 'wall-line' }, layerWalls);
  }
  for (const w of (bp.raw_features.partition_walls || [])) {
    svg('rect', { x: w.x, y: w.y, width: w.width, height: w.height, class: 'partition' }, layerWalls);
  }

  // Columns
  for (const [x, y] of (bp.raw_features.columns || [])) {
    svg('rect', { x: x - 0.4, y: y - 0.4, width: 0.8, height: 0.8, class: 'column-mark' }, layerFeatures);
  }

  // Beams
  for (const b of (bp.raw_features.beams || [])) {
    svg('line', {
      x1: b.x, y1: b.y + b.height / 2,
      x2: b.x + b.width, y2: b.y + b.height / 2,
      class: 'beam-line',
    }, layerFeatures);
  }

  // HVAC ducts
  for (const d of (bp.raw_features.hvac_ducts || [])) {
    svg('rect', {
      x: d.x, y: d.y, width: d.width, height: d.height,
      class: 'hvac-duct',
    }, layerFeatures);
  }

  // Doors (simple arc)
  for (const [x, y] of (bp.raw_features.doors || [])) {
    svg('path', {
      d: `M ${x - 0.6} ${y} A 0.6 0.6 0 0 1 ${x} ${y - 0.6}`,
      class: 'door-arc',
    }, layerFeatures);
  }

  // Water curtain zone (highlight)
  for (const z of (bp.raw_features.water_curtain_zones || [])) {
    svg('rect', {
      x: z.x, y: z.y, width: z.width, height: z.height,
      class: 'water-curtain-zone',
    }, layerFeatures);
  }

  // Water riser
  if (bp.raw_features.water_riser) {
    const [x, y] = bp.raw_features.water_riser;
    const g = svg('g', { transform: `translate(${x} ${y})` }, layerFeatures);
    svg('circle', { cx: 0, cy: 0, r: 0.7, class: 'water-riser-mark' }, g);
    svg('text', {
      x: 0, y: 0.25, 'text-anchor': 'middle',
      'font-family': 'JetBrains Mono', 'font-size': 0.7,
      fill: '#fff', 'font-weight': 700,
    }, g).textContent = 'R';
  }
}

// ─────────────────────────────────────────────────────────────
// Animation — running the agents
// ─────────────────────────────────────────────────────────────

async function animateAnalysis() {
  if (state.running) return;
  state.running = true;

  document.getElementById('btn-analyze').disabled = true;
  document.getElementById('status-dot').className = 'status-dot busy';
  document.getElementById('status-text').textContent =
    state.mode === 'live' ? 'Connected · Running' : 'Offline mode · Running';

  // Reset previous run
  document.getElementById('layer-sprinklers').innerHTML = '';
  document.getElementById('layer-scan').innerHTML = '';
  document.getElementById('findings-stream').innerHTML = '';
  document.getElementById('compliance-list').innerHTML = '';
  document.getElementById('finding-count').textContent = '0';
  document.getElementById('run-stats').classList.remove('visible');
  for (const chip of document.querySelectorAll('.agent-chip')) chip.dataset.status = 'idle';

  const t0 = performance.now();

  // Scan beam animation
  const scanLayer = document.getElementById('layer-scan');
  const beam = svg('line', {
    x1: 0, y1: 0, x2: 60, y2: 0, class: 'scan-line',
  }, scanLayer);
  beam.animate(
    [{ transform: 'translate(0px, 0px)' }, { transform: 'translate(0px, 40px)' }],
    { duration: 1100, easing: 'ease-out', fill: 'forwards' }
  );

  // Kick off the actual analysis (live or offline) in parallel with animation
  const analysisPromise = runAnalysis();

  // Stagger agent activation — visual only, ~1.2s total
  const agentsToAnimate = [...state.agents].sort((a, b) => a.agent_id - b.agent_id);
  for (let i = 0; i < agentsToAnimate.length; i++) {
    const agent = agentsToAnimate[i];
    const chip = document.querySelector(`.agent-chip[data-agent-id="${agent.agent_id}"]`);
    if (chip) chip.dataset.status = 'running';
    await sleep(15);  // 50 agents × 15ms ≈ 750ms staggered start
  }

  // Wait for the analysis to finish
  const result = await analysisPromise;

  // Mark all agents OK
  for (const r of result.agent_reports) {
    const chip = document.querySelector(`.agent-chip[data-agent-id="${r.agent_id}"]`);
    if (chip) chip.dataset.status = r.status === 'ok' ? 'ok' : 'failed';
  }

  // Stream findings into the right panel
  const interestingFindings = result.agent_reports
    .flatMap(r => r.findings.map(f => ({...f, team: r.team, agent_id: r.agent_id})))
    .filter(f => f.label && f.label !== 'spacing_constraint' && f.label !== 'coverage_constraint');

  const streamEl = document.getElementById('findings-stream');
  streamEl.innerHTML = '';
  let visibleCount = 0;
  for (const f of interestingFindings.slice(0, 14)) {
    await sleep(60);
    const div = document.createElement('div');
    div.className = `finding team-${f.team}`;
    div.innerHTML = `
      <strong>Agent ${String(f.agent_id).padStart(2,'0')} · ${f.label.replace(/_/g, ' ')}</strong>
      <em>${formatAttrs(f.attributes)} · conf ${(f.confidence * 100).toFixed(0)}%</em>
    `;
    streamEl.prepend(div);
    visibleCount++;
    document.getElementById('finding-count').textContent = String(result.summary.total_findings || visibleCount);
  }

  // Drop sprinklers with stagger
  const sprinklerLayer = document.getElementById('layer-sprinklers');
  for (let i = 0; i < result.sprinklers.length; i++) {
    const s = result.sprinklers[i];
    await sleep(45);
    const cls = s.room_id === 'water_curtain' ? 'sprinkler appear water-curtain' : 'sprinkler appear';
    const dot = svg('circle', {
      cx: s.x_ft, cy: s.y_ft, r: 0.45,
      class: cls,
      'data-id': s.sprinkler_id,
    }, sprinklerLayer);
    const glow = svg('circle', {
      cx: s.x_ft, cy: s.y_ft, r: 0.8,
      class: 'sprinkler-glow',
    }, sprinklerLayer);
    glow.style.animation = 'sprinkler-glow 0.7s ease-out';
    attachTooltip(dot, s);
  }

  // Render compliance
  const complianceEl = document.getElementById('compliance-list');
  for (const c of result.compliance) {
    const div = document.createElement('div');
    div.className = `compliance-item ${c.status}`;
    div.innerHTML = `
      <span class="compliance-status">${c.status}</span>
      <div class="compliance-body">
        <strong>${c.rule_id}</strong>
        <span>${c.rule_summary}</span>
        <em style="display:block;color:var(--ink-soft);font-size:0.72rem;margin-top:0.15rem">${c.detail}</em>
      </div>`;
    complianceEl.appendChild(div);
  }

  // Run stats
  const statsEl = document.getElementById('run-stats');
  statsEl.classList.add('visible');
  statsEl.innerHTML = `
    <h3>Run Summary</h3>
    <dl>
      <dt>Backend mode</dt>             <dd>${state.mode === 'live' ? 'Live API' : 'Offline'}</dd>
      <dt>Total elapsed</dt>            <dd>${result.total_elapsed_ms.toFixed(0)} ms</dd>
      <dt>Sprinklers placed</dt>        <dd>${result.summary.total_sprinklers}</dd>
      <dt>Agents OK</dt>                <dd>${result.summary.agents_ok}/50</dd>
      <dt>Findings reported</dt>        <dd>${result.summary.total_findings}</dd>
      <dt>Compliance checks pass</dt>   <dd>${result.summary.compliance_pass}/${result.compliance.length}</dd>
    </dl>`;

  // Footer time
  document.getElementById('run-time').textContent =
    `Run · ${result.total_elapsed_ms.toFixed(0)} ms · ${state.mode}`;

  document.getElementById('status-dot').className = 'status-dot';
  document.getElementById('status-text').textContent = `Done in ${((performance.now() - t0)/1000).toFixed(1)}s`;
  document.getElementById('btn-analyze').disabled = false;
  state.running = false;
}

function formatAttrs(attrs) {
  if (!attrs || Object.keys(attrs).length === 0) return 'detected';
  return Object.entries(attrs).slice(0, 2).map(([k, v]) =>
    typeof v === 'object' ? `${k}=…` : `${k}=${v}`
  ).join(' · ');
}

// ─────────────────────────────────────────────────────────────
// Sprinkler tooltip
// ─────────────────────────────────────────────────────────────

const tooltip = document.getElementById('tooltip');

function attachTooltip(el, sprinkler) {
  el.addEventListener('mouseenter', (e) => {
    tooltip.hidden = false;
    tooltip.innerHTML = `
      <strong>${sprinkler.sprinkler_id}</strong>
      Room ${sprinkler.room_id} · ${sprinkler.hazard_class}<br>
      Coverage: ${sprinkler.coverage_sqft} sqft<br>
      Position: (${sprinkler.x_ft}, ${sprinkler.y_ft}) ft<br>
      <span style="color: rgba(240,234,219,0.7);">Rules: ${sprinkler.rules_satisfied.join(', ')}</span>
    `;
    moveTooltip(e);
  });
  el.addEventListener('mousemove', moveTooltip);
  el.addEventListener('mouseleave', () => { tooltip.hidden = true; });
}

function moveTooltip(e) {
  tooltip.style.left = (e.clientX + 14) + 'px';
  tooltip.style.top  = (e.clientY + 14) + 'px';
}

// ─────────────────────────────────────────────────────────────
// Init
// ─────────────────────────────────────────────────────────────

async function init() {
  const [agents, blueprint] = await Promise.all([fetchAgents(), fetchBlueprint()]);
  state.agents = agents;
  state.blueprint = blueprint;
  document.getElementById('agent-count').textContent = String(agents.length);
  renderAgentsPanel(agents);
  renderBlueprint(blueprint);

  document.getElementById('status-text').textContent =
    state.mode === 'live' ? 'Connected to API' : 'Offline mode';
  if (state.mode === 'offline') {
    document.getElementById('status-dot').className = 'status-dot';
    document.getElementById('status-dot').style.background = '#b8860b';
    document.getElementById('status-dot').style.boxShadow = '0 0 6px #b8860b';
  }

  document.getElementById('btn-analyze').addEventListener('click', animateAnalysis);
  document.getElementById('btn-reset').addEventListener('click', () => {
    if (state.running) return;
    document.getElementById('layer-sprinklers').innerHTML = '';
    document.getElementById('findings-stream').innerHTML = `
      <div class="empty-state">
        <p>Click <strong>Run AI Analysis</strong> to start.</p>
        <p class="muted">Findings will stream in here as the 50 agents inspect the blueprint.</p>
      </div>`;
    document.getElementById('compliance-list').innerHTML = '';
    document.getElementById('finding-count').textContent = '0';
    document.getElementById('run-stats').classList.remove('visible');
    document.getElementById('run-time').textContent = '—';
    for (const chip of document.querySelectorAll('.agent-chip')) chip.dataset.status = 'idle';
  });
}

init();
