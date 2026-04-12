#!/usr/bin/env node
// Adds a row for every calendar day between start and end that isn't already in temperatures.csv,
// using 09:00 air temperature from Open-Meteo. Water temp is left blank for these rows.

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

async function main() {
  const csv = fs.readFileSync('temperatures.csv', 'utf8');
  const lines = csv.trim().split('\n');
  const header = lines[0];
  const rows = lines.slice(1).map(l => l.split(','));

  // Build set of days already present (DD.MM.YYYY)
  const existing = new Set(rows.map(r => r[0]));

  // Fetch hourly air temps for full range
  const START = '2026-02-16';
  const END   = '2026-04-12';
  console.log(`Fetching hourly air temps ${START} → ${END}...`);
  const url = `https://archive-api.open-meteo.com/v1/archive?latitude=47.1983&longitude=8.8561&start_date=${START}&end_date=${END}&hourly=temperature_2m&timezone=Europe%2FZurich`;
  const data = await fetchJson(url);

  // Build lookup: "YYYY-MM-DD" → air temp at 09:00
  const lookup = {};
  for (let i = 0; i < data.hourly.time.length; i++) {
    const t = data.hourly.time[i]; // "YYYY-MM-DDTHH:00"
    if (t.endsWith('T09:00')) {
      const date = t.slice(0, 10); // "YYYY-MM-DD"
      lookup[date] = data.hourly.temperature_2m[i];
    }
  }

  // Enumerate every calendar day in the range
  const newRows = [];
  const cur = new Date('2026-02-16');
  const end = new Date('2026-04-12');
  while (cur <= end) {
    const y = cur.getFullYear();
    const m = String(cur.getMonth() + 1).padStart(2, '0');
    const d = String(cur.getDate()).padStart(2, '0');
    const ddmmyyyy = `${d}.${m}.${y}`;
    const isoDate  = `${y}-${m}-${d}`;

    if (!existing.has(ddmmyyyy)) {
      const airTemp = lookup[isoDate];
      if (airTemp !== undefined) {
        newRows.push([ddmmyyyy, '09:00', '', airTemp.toFixed(1)]);
        console.log(`  + ${ddmmyyyy} 09:00  air=${airTemp.toFixed(1)}°C`);
      } else {
        console.warn(`  ? ${ddmmyyyy}: no air temp found, skipping`);
      }
    }
    cur.setDate(cur.getDate() + 1);
  }

  // Merge and sort all rows by date+time
  const allRows = [...rows, ...newRows];
  allRows.sort((a, b) => {
    const toMs = ([day, time]) => {
      const [dd, mm, yyyy] = day.split('.');
      return new Date(`${yyyy}-${mm}-${dd}T${time || '00:00'}`).getTime();
    };
    return toMs(a) - toMs(b);
  });

  const newLines = [header, ...allRows.map(r => r.join(','))];
  fs.writeFileSync('temperatures.csv', newLines.join('\n') + '\n');
  console.log(`\nDone! Added ${newRows.length} new rows. Total: ${allRows.length} rows.`);
}

main().catch(err => { console.error('ERROR:', err.message); process.exit(1); });
