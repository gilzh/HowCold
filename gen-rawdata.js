const fs = require('fs');
const rows = fs.readFileSync('temperatures.csv','utf8').trim().split('\n').slice(1).map(l=>l.split(','));
const lines = rows.map(([day,time,water,air])=>{
  const [d,m,y] = day.split('.');
  const iso = `${y}-${m}-${d}T${time}`;
  const w = water === '' ? 'null' : water;
  return `      ["${iso}", ${w}, ${air}],`;
});
console.log(lines.join('\n'));
