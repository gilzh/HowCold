const fs = require('fs');
const lines = fs.readFileSync('lake-temperatures.csv', 'utf8').split('\n');
const header = lines[0];
const seen = new Set();
const filtered = [header];

for (let i = 1; i < lines.length; i++) {
  if (!lines[i].trim()) continue;
  const day = lines[i].split(',')[0];
  if (!seen.has(day)) {
    filtered.push(lines[i]);
    seen.add(day);
  }
}

fs.writeFileSync('lake-temperatures.csv', filtered.join('\n') + '\n');
console.log('Done! Kept ' + (filtered.length - 1) + ' entries (one per day)');
