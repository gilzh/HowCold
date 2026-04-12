#!/usr/bin/env node
// One-time script to backfill AirTemp column in temperatures.csv using Open-Meteo historical API

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
  const rows = lines.slice(1).map(l => l.split(','));

  const toISO = (day) => { const [d, m, y] = day.split('.'); return `${y}-${m}-${d}`; };

  const startDate = toISO(rows[0][0]);
  const endDate = toISO(rows[rows.length - 1][0]);

  console.log(`Fetching air temps from ${startDate} to ${endDate}...`);
  const url = `https://archive-api.open-meteo.com/v1/archive?latitude=47.1983&longitude=8.8561&start_date=${startDate}&end_date=${endDate}&hourly=temperature_2m&timezone=Europe%2FZurich`;
  const data = await fetchJson(url);

  const lookup = {};
  for (let i = 0; i < data.hourly.time.length; i++) {
    lookup[data.hourly.time[i]] = data.hourly.temperature_2m[i];
  }

  const newRows = rows.map(row => {
    const [day, time] = row;
    const [d, m, y] = day.split('.');
    const hour = time.split(':')[0].padStart(2, '0');
    const key = `${y}-${m}-${d}T${hour}:00`;
    const airTemp = lookup[key];
    return [...row.slice(0, 3), airTemp !== undefined ? airTemp.toFixed(1) : ''];
  });

  const newLines = ['Day,Time,Temperature,AirTemp', ...newRows.map(r => r.join(','))];
  fs.writeFileSync('temperatures.csv', newLines.join('\n') + '\n');
  console.log(`Done! Added AirTemp to ${newRows.length} rows.`);
  newRows.forEach(r => console.log(r.join(',')));
}

main().catch(err => { console.error('ERROR:', err.message); process.exit(1); });
