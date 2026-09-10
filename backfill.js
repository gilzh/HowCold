#!/usr/bin/env node
// Backfill temperatures.csv in three passes:
//   1. Fill blank AirTemp on existing rows (Open-Meteo archive, matched to actual reading time)
//   2. Insert missing calendar days with 09:00 air temp (water left blank)
//   3. Fill blank WaterTemp using EAWAG Alplakes model data
//
// Usage: node backfill.js [--start YYYY-MM-DD] [--end YYYY-MM-DD]
//   Dates default to the first/last day already in temperatures.csv.

const https = require('https');
const fs    = require('fs');

// ── helpers ──────────────────────────────────────────────────────────────────

function fetchJson(url) {
  return new Promise((resolve, reject) => {
    https.get(url, { headers: { 'User-Agent': 'Mozilla/5.0' } }, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => { try { resolve(JSON.parse(data)); } catch (e) { reject(e); } });
    }).on('error', reject);
  });
}

function toISO(ddmmyyyy) {
  const [d, m, y] = ddmmyyyy.split('.');
  return `${y}-${m}-${d}`;
}

function toDDMMYYYY(isoDate) {
  const [y, m, d] = isoDate.split('-');
  return `${d}.${m}.${y}`;
}

function toApiDate(isoDate) {
  return isoDate.replace(/-/g, '') + '0000';
}

// ── air temps (Open-Meteo archive) ───────────────────────────────────────────

async function fetchAirTemps(startISO, endISO) {
  const url = `https://archive-api.open-meteo.com/v1/archive`
    + `?latitude=47.1983&longitude=8.8561`
    + `&start_date=${startISO}&end_date=${endISO}`
    + `&hourly=temperature_2m&timezone=Europe%2FZurich`;
  console.log(`  Fetching air temps ${startISO} → ${endISO}...`);
  const data = await fetchJson(url);
  // Build two lookups from the same API response:
  //   byTimestamp: "YYYY-MM-DDTHH:00" → temp   (for matching existing rows)
  //   by0900:      "YYYY-MM-DD"       → temp   (09:00 reading for new rows)
  const byTimestamp = {}, by0900 = {};
  for (let i = 0; i < data.hourly.time.length; i++) {
    const t   = data.hourly.time[i];           // "YYYY-MM-DDTHH:00"
    const val = data.hourly.temperature_2m[i];
    if (val === null) continue;
    byTimestamp[t] = val;
    if (t.endsWith('T09:00')) by0900[t.slice(0, 10)] = val;
  }
  return { byTimestamp, by0900 };
}

// ── water temps (EAWAG Alplakes) ─────────────────────────────────────────────

async function fetchWaterTemps(startISO, endISO) {
  // Alplakes times out on long ranges — fetch in ~30-day chunks sequentially
  const lat = '47.1983', lng = '8.8561', depth = '0.5';
  const base = `https://alplakes-api.eawag.ch/simulations/point/delft3d-flow/zurich`;

  async function chunk(s, e) {
    const url = `${base}/${toApiDate(s)}/${toApiDate(e)}/${depth}/${lat}/${lng}`;
    console.log(`  Fetching water temps ${s} → ${e}...`);
    const data = await fetchJson(url);
    const times = data.time, temps = data.variables.temperature.data;
    const result = {};
    for (let i = 0; i < times.length; i++) {
      if (temps[i] === null) continue;
      const utcDate   = new Date(times[i]);
      const localHour = (utcDate.getUTCHours() + 2) % 24; // CEST = UTC+2
      const dateKey   = utcDate.toISOString().slice(0, 10);
      if (!result[dateKey] || Math.abs(localHour - 9) < Math.abs(result[dateKey].localHour - 9)) {
        result[dateKey] = { temp: temps[i], localHour };
      }
    }
    return result;
  }

  // Build list of 14-day chunk boundaries
  const chunks = [];
  const cur = new Date(startISO), end = new Date(endISO);
  while (cur < end) {
    const s = cur.toISOString().slice(0, 10);
    cur.setDate(cur.getDate() + 14);
    const e = cur < end ? cur.toISOString().slice(0, 10) : endISO;
    chunks.push([s, e]);
  }

  const sleep = ms => new Promise(r => setTimeout(r, ms));
  const lookup = {};
  for (const [s, e] of chunks) {
    Object.assign(lookup, await chunk(s, e));
    await sleep(500);
  }
  console.log(`  Got water model temps for ${Object.keys(lookup).length} days.`);
  return lookup;
}

// ── main ─────────────────────────────────────────────────────────────────────

async function main() {
  const args = process.argv.slice(2);
  const get  = (flag) => { const i = args.indexOf(flag); return i !== -1 ? args[i + 1] : null; };

  const csvPath = 'temperatures.csv';
  const csv     = fs.readFileSync(csvPath, 'utf8');
  const lines   = csv.trim().split('\n');
  const header  = lines[0];
  let rows      = lines.slice(1).map(l => l.split(','));

  const csvStart = toISO(rows[0][0]);
  const csvEnd   = toISO(rows[rows.length - 1][0]);
  const startISO = get('--start') || csvStart;
  const endISO   = get('--end')   || csvEnd;

  console.log(`\n=== Pass 1: Fill blank AirTemp on existing rows ===`);
  const { byTimestamp, by0900 } = await fetchAirTemps(startISO, endISO);
  let airFilled = 0;
  rows = rows.map(row => {
    const [day, time, water, air] = row;
    if (air !== undefined && air !== '') return row;
    const [d, m, y] = day.split('.');
    const hour = time.split(':')[0].padStart(2, '0');
    const key  = `${y}-${m}-${d}T${hour}:00`;
    const val  = byTimestamp[key];
    if (val === undefined) { console.warn(`  ? No air temp for ${day} ${time}`); return row; }
    console.log(`  + ${day} ${time}: air=${val.toFixed(1)}°C`);
    airFilled++;
    return [day, time, water, val.toFixed(1)];
  });
  console.log(`  Filled AirTemp for ${airFilled} rows.`);

  console.log(`\n=== Pass 2: Insert missing calendar days ===`);
  const existing = new Set(rows.map(r => r[0]));
  const newRows  = [];
  const cur = new Date(startISO), end = new Date(endISO);
  while (cur <= end) {
    const iso      = cur.toISOString().slice(0, 10);
    const ddmmyyyy = toDDMMYYYY(iso);
    if (!existing.has(ddmmyyyy)) {
      const val = by0900[iso];
      if (val !== undefined) {
        newRows.push([ddmmyyyy, '09:00', '', val.toFixed(1)]);
        console.log(`  + ${ddmmyyyy}: air=${val.toFixed(1)}°C (no reading that day)`);
      } else {
        console.warn(`  ? ${ddmmyyyy}: no 09:00 air temp, skipping`);
      }
    }
    cur.setDate(cur.getDate() + 1);
  }
  console.log(`  Inserted ${newRows.length} missing days.`);
  rows = [...rows, ...newRows].sort((a, b) => {
    const ms = ([day, time]) => {
      const [dd, mm, yyyy] = day.split('.');
      return new Date(`${yyyy}-${mm}-${dd}T${time || '00:00'}`).getTime();
    };
    return ms(a) - ms(b);
  });

  console.log(`\n=== Pass 3: Fill blank WaterTemp from EAWAG Alplakes ===`);
  const blankWaterDates = rows.filter(r => !r[2] || r[2] === '').map(r => toISO(r[0]));
  if (blankWaterDates.length === 0) {
    console.log('  Nothing to fill — all rows already have water temps.');
  } else {
    const waterStart = blankWaterDates[0];
    const waterEnd   = blankWaterDates[blankWaterDates.length - 1];
    const waterLookup = await fetchWaterTemps(waterStart, waterEnd);
    let waterFilled = 0;
    rows = rows.map(row => {
      const [day, time, water, air] = row;
      if (water && water !== '') return row;
      const entry = waterLookup[toISO(day)];
      if (!entry) { console.warn(`  ? No water model data for ${day}`); return row; }
      const val = entry.temp.toFixed(1);
      console.log(`  + ${day}: water=${val}°C (model)`);
      waterFilled++;
      return [day, time, val, air];
    });
    console.log(`  Filled WaterTemp for ${waterFilled} rows.`);
  }

  fs.writeFileSync(csvPath, [header, ...rows.map(r => r.join(','))].join('\n') + '\n');
  console.log(`\nDone. Total rows: ${rows.length}.`);
}

main().catch(err => { console.error('ERROR:', err.message); process.exit(1); });
