#!/usr/bin/env node

const https = require("https");
const fs = require("fs");
const path = require("path");
const { execSync } = require("child_process");

const URL = "https://www.badi-info.ch/_temp/zuerichsee-lachen.htm";
const RECIPIENT = "gilles.daniel@gmail.com";

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

  // Timestamp appears as e.g. "Am 15.02. 15:00"
  const timeMatch = html.match(/Am\s+([\d.]+)\s+([\d:]+)/);
  const timestamp = timeMatch ? `${timeMatch[1]} ${timeMatch[2]}` : "unknown time";

  return { temperature: tempMatch[1], timestamp };
}

function sendIMessage(recipient, message) {
  const script = `
    tell application "Messages"
      set targetService to 1st account whose service type = iMessage
      set targetBuddy to participant "${recipient}" of targetService
      send "${message}" to targetBuddy
    end tell
  `;
  execSync(`osascript -e '${script.replace(/'/g, "'\\''")}'`);
}

function sendEmail(recipient, subject, body) {
  const script = `
    tell application "Mail"
      set newMessage to make new outgoing message with properties {subject:"${subject}", content:"${body}", visible:false}
      tell newMessage
        make new to recipient at end of to recipients with properties {address:"${recipient}"}
      end tell
      send newMessage
    end tell
  `;
  execSync(`osascript -e '${script.replace(/'/g, "'\\''")}'`);
}

async function main() {
  console.log(`[${new Date().toISOString()}] Fetching water temperature for Lachen...`);

  const [html, airTemp] = await Promise.all([fetchPage(URL), fetchAirTemp()]);
  const { temperature, timestamp } = parseTemperature(html);

  console.log(`Water: ${temperature}°C (measured ${timestamp}), Air: ${airTemp}°C`);

  const message = `🌊 ${temperature}°C https://gilzh.github.io/HowCold`;

  // Append to CSV
  const csvPath = path.join(__dirname, "temperatures.csv");
  const fileExists = fs.existsSync(csvPath);
  if (!fileExists) {
    fs.writeFileSync(csvPath, "Day,Time,Temperature,AirTemp\n");
  }
  const now = new Date();
  const day = now.toLocaleDateString("de-CH", { day: "2-digit", month: "2-digit", year: "numeric" });
  const time = now.toLocaleTimeString("de-CH", { hour: "2-digit", minute: "2-digit" });
  fs.appendFileSync(csvPath, `${day},${time},${temperature},${airTemp}\n`);
  console.log(`Temperature logged to ${csvPath}`);

  sendIMessage(RECIPIENT, message);
  console.log(`iMessage sent to ${RECIPIENT}`);

  // const subject = `Water Temperature Lachen: ${temperature}°C`;
  // sendEmail(RECIPIENT, subject, message);
  // console.log(`Email sent to ${RECIPIENT}`);
}

main().catch((err) => {
  console.error(`[${new Date().toISOString()}] ERROR:`, err.message);
  process.exit(1);
});
