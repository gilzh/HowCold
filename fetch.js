#!/usr/bin/env node

const https = require("https");
const fs = require("fs");
const path = require("path");
const URL = "https://www.badi-info.ch/_temp/zuerichsee-lachen.htm";

function fetchPage(url) {
  return new Promise((resolve, reject) => {
    const options = {
      headers: {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
      }
    };
    https
      .get(url, options, (res) => {
        let data = "";
        res.on("data", (chunk) => (data += chunk));
        res.on("end", () => resolve(data));
      })
      .on("error", reject);
  });
}

function fetchAirTemp() {
  const url = "https://api.open-meteo.com/v1/forecast?latitude=47.1983&longitude=8.8561&current=temperature_2m&timezone=Europe%2FZurich";
  return new Promise((resolve, reject) => {
    https.get(url, { headers: { "User-Agent": "Mozilla/5.0" } }, (res) => {
      let data = "";
      res.on("data", (chunk) => (data += chunk));
      res.on("end", () => {
        try {
          const json = JSON.parse(data);
          resolve(json.current.temperature_2m);
        } catch (e) { reject(e); }
      });
    }).on("error", reject);
  });
}

function parseTemperature(html) {
  // Temperature appears as e.g. <b id="t3">4.6</b>&deg;C
  const tempMatch = html.match(/<b id="t\d+">([0-9.]+)<\/b>/);
  if (!tempMatch) throw new Error("Could not parse temperature from page");

  // Timestamp appears as e.g. "Am 15.02. 15:00" (no year given by the site)
  const timeMatch = html.match(/Am\s+(\d{2})\.(\d{2})\.\s+(\d{2}):(\d{2})/);
  if (!timeMatch) throw new Error("Could not parse timestamp from page");
  const [, day, month, hour, minute] = timeMatch;

  return { temperature: tempMatch[1], day, month, hour, minute };
}

// The site's timestamp has no year, so infer it from the current Zurich date.
// Only wraps around New Year's (station says Dec, but it's now Jan) since
// this runs daily and the reading is always within a day of "now".
function getZurichNow() {
  const parts = new Intl.DateTimeFormat("en-CA", {
    timeZone: "Europe/Zurich",
    year: "numeric", month: "2-digit", day: "2-digit",
  }).formatToParts(new Date());
  const get = (t) => parts.find((p) => p.type === t).value;
  return { year: get("year"), month: get("month") };
}

function resolveYear(stationMonth) {
  const nowZurich = getZurichNow();
  let year = Number(nowZurich.year);
  if (stationMonth === "12" && nowZurich.month === "01") year -= 1;
  return year;
}


async function main() {
  console.log(`[${new Date().toISOString()}] Fetching water temperature for Lachen...`);

  const [html, airTemp] = await Promise.all([fetchPage(URL), fetchAirTemp()]);
  const { temperature, day: stationDay, month: stationMonth, hour, minute } = parseTemperature(html);
  const year = resolveYear(stationMonth);

  console.log(`Water: ${temperature}°C (measured ${stationDay}.${stationMonth}.${year} ${hour}:${minute}), Air: ${airTemp}°C`);

  // Append to CSV
  const csvPath = path.join(__dirname, "temperatures.csv");
  const fileExists = fs.existsSync(csvPath);
  if (!fileExists) {
    fs.writeFileSync(csvPath, "Day,Time,WaterTemp,AirTemp\n");
  }
  const day = `${stationDay}.${stationMonth}.${year}`;
  const time = `${hour}:${minute}`;
  fs.appendFileSync(csvPath, `${day},${time},${temperature},${airTemp}\n`);
  console.log(`Temperature logged to ${csvPath}`);
}

main().catch((err) => {
  console.error(`[${new Date().toISOString()}] ERROR:`, err.message);
  process.exit(1);
});
