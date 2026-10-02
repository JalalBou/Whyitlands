# Shopper pulse: content/intel/shoppers.json

{"updated": "YYYY-MM-DD",
 "intro": "One or two sentences on what this section is.",
 "trends": [
  {"key": "kebab-key",
   "theme": "one of: speed | price | duties | ooh | returns | platforms | sustainability | trust | tracking",
   "regions": ["GLOBAL"|"EU"|"UK"|"NA"|"SA"|"AS"|"CN"|"ME"|"NAF"],
   "title": "Short claim in plain words (max ~80 chars)",
   "big": "61%",                      // the headline number, exactly as published
   "label": "of cross-border shoppers say knowing duties and delivery charges before buying is essential",
   "direction": "up|down|flat|new",   // vs the previous comparable reading, only if the source gives it
   "previous": "53% in 2024",         // optional, only if sourced
   "why": "Our reading: 1-2 sentences on WHY the behaviour is moving (prices, fees, platforms, lockers, trust, regulation...).",
   "means": "One sentence: what it means for carriers, posts, platforms or merchants.",
   "source": {"pub": "IPC", "t": "Cross-border e-commerce shopper survey 2025", "u": "https://...", "date": "2026-01-20",
              "method": "Online survey, 30,970 respondents, 37 countries"},   // sample size, countries, who ran it
   "sponsor_note": "",               // e.g. "Survey run by a delivery-software vendor" when commercially sponsored
   "stories": ["de-minimis-end"]     // storyline keys when relevant, else []
  }
 ]}

Rules: every number exactly as published, with a real URL you opened; state method/sample; prefer large repeated surveys
(postal associations, national statistics offices, Eurostat, central banks, regulators such as Ofcom/ARCEP/PRC, large
carrier or platform studies), flag vendor-run surveys in sponsor_note; most recent edition (2025-2026); British spelling;
no em-dash; never mention Asendia.
