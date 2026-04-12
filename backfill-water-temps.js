#!/usr/bin/env node
// Backfills water temperature for days with no reading using EAWAG Alplakes model data.
// Fetches in two chunks to avoid API timeout. Picks the 3-hour slot closest to 09:00 local time.

const https = require('https');
const fs = require('fs');

function fetchJson(url) {
  return new Promise((resolve, reject) => {
    https.get(url, { headers: { 'User-Agent': 'Mozilla/5.0' } }, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => { try { resolve(JSON.parse(data)); } catch (e) { reject(e); } });
    }).on('error', reject);
  });
}

function toApiDate(isoDate) {
  // "YYYY-MM-DD" → "YYYYmmdd0000"
  return isoDate.replace(/-/g, '') + '0000';
}

async function fetchChunk(start, end) {
  const lat = '47.1983', lng = '8.8561', depth = '0.5';
  const url = `https://alplakes-api.eawag.ch/simulations/point/delft3d-flow/zurich/${toApiDate(start)}/${toApiDate(end)}/${depth}/${lat}/${lng}`;
  console.log(`  Fetching ${start} → ${end}...`);
  const data = await fetchJson(url);
  // Returns { time: [...ISO strings...], variables: { temperature: { data: [...] } } }
  const times = data.time;
  const temps = data.variables.temperature.data;
  const result = {};
  for (let i = 0; i < times.length; i++) {
    if (temps[i] === null) continue;
    // times[i] is like "2026-02-16T00:00:00+00:00" (UTC)
    // Convert UTC to CEST (UTC+2) to find local 09:00 → UTC 07:00
    const utcDate = new Date(times[i]);
    const localHour = (utcDate.getUTCHours() + 2) % 24; // CEST = UTC+2
    const dateKey = `${utcDate.getUTCFullYear()}-${String(utcDate.getUTCMonth()+1).padStart(2,'0')}-${String(utcDate.getUTCDate()).padStart(2,'0')}`;
    if (!result[dateKey] || Math.abs(localHour - 9) < Math.abs(result[dateKey].localHour - 9)) {
      result[dateKey] = { temp: temps[i], localHour };
    }
  }
  return result;
}

async function main() {
  const csv = fs.readFileSync('temperatures.csv', 'utf8');
  const lines = csv.trim().split('\n');
  const header = lines[0];
  const rows = lines.slice(1).map(l => l.split(','));

  // Fetch in two chunks to avoid timeout
  const [chunk1, chunk2] = await Promise.all([
    fetchChunk('2026-02-16', '2026-03-14'),
    fetchChunk('2026-03-14', '2026-04-12'),
  ]);
  const lookup = { ...chunk1, ...chunk2 };
  console.log(`  Got model temps for ${Object.keys(lookup).length} days.`);

  let filled = 0;
  const newRows = rows.map(row => {
    const [day, time, water, air] = row;
    if (water !== '') return row; // already has a water reading

    const [d, m, y] = day.split('.');
    const isoDate = `${y}-${m}-${d}`;
    const entry = lookup[isoDate];
    if (!entry) { console.warn(`  ? No model data for ${day}`); return row; }

    const modelTemp = entry.temp.toFixed(1);
    console.log(`  + ${day}: water=${modelTemp}°C (model)`);
    filled++;
    return [day, time, modelTemp, air];
  });

  const newLines = [header, ...newRows.map(r => r.join(','))];
  fs.writeFileSync('temperatures.csv', newLines.join('\n') + '\n');
  console.log(`\nDone! Filled ${filled} rows. Total: ${newRows.length} rows.`);
}

main().catch(err => { console.error('ERROR:', err.message); process.exit(1); });
