# Flowcode context for the opportunity agent

This file is what the agent "knows" about Flowcode. It is read on every run, so
editing it changes the agent's behavior with no code change. Anyone can edit it.

- Keep the four section headings (A, B, C, D) exactly as they are: the code finds sections by them.
- Everything else (wording, products, customers, examples) is safe to change.
- Last updated: 2026-11-17, from flowcode.com. Numbers are Flowcode's own claims, not independently verified.

---

## A. Product knowledge

**What Flowcode does, in one line:** turns offline touchpoints (TV, packaging,
in-store, events, out-of-home, direct mail, print) into measurable, personalized
digital interactions that capture first-party data and sync it to the brand's
CRM. Tagline: "Every IRL needs a URL."

### Products

- **Flowcodes**: designed, branded, dynamic QR codes. The destination can be
  changed after printing. Bulk creation of unique codes (one per pack, mailer or
  household) for 1:1 attribution. Per-code analytics with location. Central
  governance across many brands or regions.
- **FlowURLs**: branded short links on the brand's own domain. UTM management,
  a different destination per visitor, and clicks tied to a person. A Bitly
  alternative.
- **FlowHubs**: mobile landing pages and campaign hubs that combine QR, links,
  video and forms. Good for loyalty sign-ups, sweepstakes, ticketing, booking.
  A Linktree alternative. "ShopperHub" variant for retail.
- **FlowID and personalization**: first-party identity captured from real-world
  touchpoints. Connects a TV or billboard exposure to later online activity.
  Content can change by location, loyalty tier, history or CRM data.
- **Analytics and integrations**: real-time dashboard, conversion pixel for
  full-funnel attribution, SmartFlow (AI picks the best-performing landing page),
  two-way CRM sync. Named integrations: Salesforce, HubSpot, Mailchimp, Adobe,
  Snowflake, Zapier.
- **Workspaces and API**: separate workspaces per brand, team or region with a
  leadership roll-up; shareable with sponsors and partners. SSO, SOC 2 Type 2,
  GDPR, CCPA, HIPAA. API for CRM transfers and dynamic updates.
- **Also**: GS1 Digital Link-compliant codes for retail and CPG packaging (the
  industry is moving to 2D barcodes by 2027); QR on connected-TV ads; audience
  builder for retargeting.

### Where it fits best (by channel)

| Channel | Typical Flowcode play |
|---|---|
| TV and broadcast | On-screen code linking the ad to a landing page; measures response per spot and market |
| Packaging | On-pack code for loyalty sign-up, offers, recipes, games; unique codes per pack |
| Retail and in-store | Shelf, display and table codes for offers, coupons, app downloads |
| Events and sponsorship | Codes on screens, signage, merch for fan sign-up, sweepstakes, ticketing |
| Out-of-home | Billboard and transit codes with location-level reporting |
| Direct mail and print | Unique code per household or offer for 1:1 attribution |
| App and loyalty | Drive app installs and loyalty enrolment from any physical touchpoint |
| Social and email | Weaker fit: already digital. FlowURLs or FlowHubs only when tracking or routing is a real gap |

### Industries and example plays

- **Quick-service restaurants**: digital menus and ordering, table-side loyalty
  sign-up, drive-thru payment, offers and upsell, app downloads, sweepstakes,
  location data for foot traffic.
- **Retail and CPG**: on-pack loyalty and offers, shelf codes, direct mail.
- **Sports and entertainment**: in-stadium and broadcast codes, fan sign-up,
  ticketing, merch.
- **Automotive**: codes on TV ads, event screens, VIN-level service codes,
  dealership sheets and test-drive booking.
- **Others**: travel (airport touchpoints), healthcare (consent-based patient
  engagement), financial services (direct mail, statements), tech and telco
  (device packaging, retail signage), media (broadcast attribution).

### Proof points a seller can quote (Flowcode's own claims)

- Used by over 75% of the Fortune 500 (one Flowcode page says 70%); 1B+ connections; 20,000+ businesses.
- NFL Shop: $25k revenue and 10k connections in 60 seconds.
- ESPN College GameDay: 32,000 emails collected in one day from a broadcast code.
- Lunchables: 22% sales lift, 50% campaign conversion (playable packaging).
- LOVE CORN: 62% CRM conversion, 27k new customers (AI-enabled packaging QR).
- Waterpik: 76% conversion, 5x goal.
- Welch's: 14k+ connections, 55% click-through.
- CLEAR: 7,000+ codes, 1.2M+ scans.

Do not quote prices. Plans and prices change; the seller confirms them.

---

## B. Scoring rubric: fit and impact

The agent rates every opportunity on two scores from 1 to 5. Use only what the
evidence says; do not assume facts that are not in the sources. If you are torn
between two scores, pick the lower one. A 2 or 4 means "between the two
descriptions around it".

### Fit: how naturally does a Flowcode product solve something in this activity?

| Score | Meaning |
|---|---|
| **5** | There is a physical or broadcast touchpoint (TV spot, packaging, in-store, event, OOH, mail) **and** a clear gap between it and a digital action (sign-up, purchase, app install, data capture). A named Flowcode product fills that gap directly. Example: a national TV ad pushing people to download an app. |
| **3** | A Flowcode product could help, but the link is indirect. Either the touchpoint exists but the digital goal is unclear, or the activity is mostly digital with a small physical part. Example: a social campaign that also has a few in-store posters. |
| **1** | No physical or broadcast touchpoint, or no reason a code or link would help. Example: an earnings report, an executive hire, a purely online sale. |

### Impact: if Flowcode helped here, how much would it matter to the brand?

| Score | Meaning |
|---|---|
| **5** | Large audience (national TV, national packaging, every store, a major sponsorship) **and** tied to something the brand clearly cares about: revenue, loyalty or app growth, first-party data. Running now or about to start. |
| **3** | Medium reach (one region, one event, one product line) or a clear goal but limited scale. Or a large program that just ended but is likely to repeat. |
| **1** | Small, local or one-off; already over with no sign of repeating; or no measurable goal. |

### Checks before giving a 4 or 5

- Can you name the exact touchpoint from the evidence (e.g. "the 30-second spot that aired during X")? If not, fit is at most 3.
- Is the scale stated in the evidence (national, number of stores, audience size)? If not, impact is at most 3.

---

## C. Known customers

Brands Flowcode publicly names as customers or shows on its site. If a brand on
this list is researched, the report flags it as a **likely existing customer**
(pitch expansion, not a new deal). Being listed is not proof of an active contract.

How to edit: one brand per line, starting with `- `. Put other spellings or
sub-brands on the same line, separated by ` / `.

### Retail and CPG
- LOVE CORN
- Waterpik
- Lunchables
- Welch's
- Athletic Brewing
- Capri Sun
- Carbone
- Jolie
- Lacoste
- Petco / PetCo
- Red Bull
- Target
- LEGO
- Love Wellness
- Hoka
- Poppi
- Lay's
- Chewy
- Faherty
- TRUFF
- Kraft Heinz
- Coca-Cola / Coke
- Planters
- Bud Light
- Dr Power
- Hunt Brothers Pizza
- Supergoop
- JLo Beauty
- Skkn by Kim / SKKN

### Quick-service restaurants
- Dunkin' / Dunkin / Dunkin' Donuts
- Chick-fil-A
- Baskin-Robbins
- Raising Cane's
- Jamba / Jamba Juice
- Shake Shack
- Cold Stone Creamery / Cold Stone

### Automotive
- BMW
- Ford
- Volvo
- Continental Tires / Continental
- Gates
- Audi
- Harley-Davidson
- Formula Drift

### Financial services
- SoFi
- JG Wentworth
- New York Life

### Media and entertainment
- NBCUniversal / NBC
- Nickelodeon
- Love Island
- ESPN
- AMC+
- Disney+ / Disney
- Wicked
- Warner Bros.
- Star Trek
- Governors Ball / Governor's Ball
- Lyft Media
- Paramount+ / Paramount
- TelevisaUnivision
- Jonas Brothers
- Zach Bryan

### Sports
- NFL / NFL Shop
- NBA
- WNBA
- NHL
- MLS
- NWSL
- Premier League
- Aston Villa
- NASCAR
- LA Kings
- Cleveland Cavaliers
- Minnesota Vikings
- McLaren / McLaren F1
- Big Ten
- New York Yankees / NY Yankees / Yankees
- New York Islanders / NY Islanders
- Gotham FC

### Travel and other
- CLEAR
- Uber / Uber Eats
- Delta / Delta Air Lines
- Airbnb
- National Park Service
- 1-800-Flowers / 1-800 Flowers
- Louis Vuitton
- Ferragamo
- NOTHING
- NYU
- NYC Pride
- Spectrum Reach
- GoPro
- GoBowling
- Pfizer
- MIT Technology Review
- The CMO Podcast

---

## D. How to write the "Suggested play"

The suggested play is a **pre-call brief**: a seller reads it tonight and uses
it on a call tomorrow. Write it for a busy account executive, not for an engineer.

Write 4 to 6 short sentences covering, in this order:

1. **Opener**: the specific thing the brand is doing, with its date, in the
   brand's own terms. ("Your new fall menu spot, on national TV since October...")
2. **The gap**: what the brand probably cannot see or capture today from that
   touchpoint. Say "likely" when it is an inference, not a fact.
3. **The play**: one concrete Flowcode setup. Name the product(s) and where the
   code or link goes. ("A dynamic Flowcode on the spot that opens a FlowHub with
   the app download and a loyalty sign-up.")
4. **What they would get**: the data or result it captures (scans by market,
   new loyalty members, app installs attributed to TV).
5. **Proof**: one comparable proof point from section A, labelled as a Flowcode
   result. Pick the closest match by industry or channel.
6. **Question to ask**: one discovery question that opens the conversation.
   ("How are you measuring TV-driven app installs today?")

Rules:
- Use only facts from the evidence and this file. Never invent numbers, names, or results.
- Do not name a contact person unless the evidence names them. You may suggest a
  likely role to reach (e.g. "brand marketing or loyalty lead").
- Do not mention prices.
- If the brand is a likely existing customer (section C), frame the play as an
  expansion of what they already do with Flowcode.
- Plain words, no hype, no buzzwords.
