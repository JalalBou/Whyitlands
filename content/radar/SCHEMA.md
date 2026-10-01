# Regulatory Radar item schema (one JSON file per jurisdiction group: content/radar/<group>.json = {"items": [...]})

{
  "key": "eu-customs-reform-2026",          // unique kebab-case
  "title": "EU customs reform: platforms become the importer",   // short, plain English, max ~80 chars
  "jurisdiction": "European Union",          // who legislates
  "regions": ["EU"],                         // from: GLOBAL, EU, UK, NA, SA, AS, CN, ME, NAF
  "domain": "customs",                       // one of: customs, tax, trade, product-safety, postal, data, sustainability, labour, platforms
  "status": "adopted",                       // one of: proposed, adopted, in-force, suspended, consultation
  "summary": "Two or three sentences: what the rule does, in plain words.",
  "dates": [ {"date": "2026-09-20", "what": "Regulation enters into force", "src": 0},
             {"date": "2028-07-01", "what": "E-commerce operators must use the EU Customs Data Hub", "src": 1} ],
  "hits": ["Non-EU marketplaces", "Postal operators", "Express integrators"],   // who is directly affected
  "parcel": "One sentence: what it changes for a parcel (cost, data, liability, speed).",
  "prepare": ["Concrete action 1", "Concrete action 2"],   // 2-3 actions for executives, practical
  "read": "Our reading: one or two sentences of analysis (likelihood of slippage, knock-on effects).",
  "stories": ["eu-customs-reform"],          // keys from content/storylines.json when relevant, else []
  "sources": [ {"t": "Title", "u": "https://...", "pub": "Publisher", "date": "2026-09-19"} ]
}

Dates: ISO YYYY-MM-DD; if only a month is known use the first of the month and say "(month only)" in "what". Include past milestones only if within the last 6 months; focus on what is coming (next 24 months).
