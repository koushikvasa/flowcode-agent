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
- LOVE CORN: 62% CRM conversion, 27k new customers (packaging QR for CRM capture).
- Waterpik: 76% conversion, 5x goal.
- Welch's: 14k+ connections, 55% click-through.
- CLEAR: 7,000+ codes, 1.2M+ scans.

Do not quote prices. Plans and prices change; the seller confirms them.

---

## B. Scoring checklist: fit and impact

A separate judge answers these questions for every opportunity. The answers,
not a gut-feel rating, decide the fit and impact scores. (Why yes/no questions
instead of a 1-5 scale: judges agree with each other far more, and every score
can be traced to specific answers.)

How to answer each question:
- First copy the exact words from the sources that decide it, then answer.
- Answer **yes**, **no**, or **unknown**. Use only the sources; never assume.
- If the sources do not clearly say, answer **unknown**. Unknown counts as no.
- A yes must come with a quote that appears word for word in a source.

How the answers become scores: the code adds up the weights of the "yes"
answers (weights are set in `agent/config.py`). If F1 is not a yes, the
opportunity is dropped: no physical or broadcast touchpoint, no Flowcode play.

### Fit: does a Flowcode product naturally solve something here?

| ID | Question | Counts as yes, for example |
|---|---|---|
| F1 | Do the sources name a specific physical or broadcast touchpoint? | A TV spot, packaging, in-store display, menu board, event, stadium, billboard, direct mail. Not "a campaign" in general. |
| F2 | Do the sources name a digital action the brand wants people to take? | Download the app, join loyalty, order online, sign up, enter a sweepstakes, scan, visit a page. |
| F3 | Does it match a play in the channel table in section A? | A packaging launch matches "on-pack code for loyalty sign-up, offers". |

### Impact: if Flowcode helped here, how much would it matter?

| ID | Question | Counts as yes, for example |
|---|---|---|
| I1 | Do the sources state the scale? | A number of stores, markets, units, viewers, or a budget. |
| I2 | Is it national or across several markets? | "Nationwide", "all U.S. locations", a national TV buy. Not one city or one store. |
| I3 | Is it running now or about to start, as of the source's date? | Launch date in the future, "now available", "this month". Not a recap of something that already ended. |

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
   result. Pick the closest match by industry or channel. **Use each proof point
   at most once per report**: if the closest one is already used by another play,
   take the next closest. If none is left that fits, leave this sentence out
   rather than repeat one. Never mention this rule in the play.
6. **Question to ask**: one discovery question that opens the conversation.
   ("How are you measuring TV-driven app installs today?")

Rules:
- The play is only the brief a seller reads to the customer. Never include notes about these
  instructions, your choices, or what you left out.
- Use only facts from the evidence and this file. Never invent numbers, names, or results.
- Do not name a contact person unless the evidence names them. You may suggest a
  likely role to reach (e.g. "brand marketing or loyalty lead").
- Do not mention prices.
- If the brand is a likely existing customer (section C), frame the play as an
  expansion of what they already do with Flowcode.
- Plain words, no hype, no buzzwords.
