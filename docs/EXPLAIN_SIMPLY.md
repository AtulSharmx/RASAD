# RASAD, aasaan bhasha mein

Ye document team ke liye hai. Isme bina technical shabdon ke samjhaya hai ki RASAD ka har hissa kya karta hai, aur jury ke likely sawalon ke chhote jawab hain. Numbers app ki Demo date (25 Oct 2026) ke hain, jaise 6 Oct 2026 ko the; app hamesha apne numbers khud calculate karta hai.

---

## 1. RASAD ek line mein

Sardi aane se pehle pahadon ke posts tak saaman (ration, kerosene, dawai, battery, garam kapde) pahunchana hota hai. Raste (passes) barf se band ho jaate hain. RASAD batata hai: **kaunsa post kab khatam hoga, raasta kab tak khula rahega, aakhri din kaunsa hai jab truck bhejna safe hai, kaunsa saaman kis tareeke se jaaye (truck, jeep, mule, porter, helicopter, drone), aur kitna kharcha hoga.** Commander har sujhaav ko approve, badal ya reject karta hai, aur sab audit log mein likha jaata hai.

## 2. Data kahan se aata hai (10 "streams")

Sochiye 10 alag registers hain, aur RASAD sabko ek jagah jodkar ek tasveer banata hai.

| Stream | Asli ya nakli? | Asal mein kahan se aayega |
|---|---|---|
| Stock (kitna saaman pada hai) | Nakli (simulated) | Army ka CICG inventory system |
| Roz ki khapat (kitna use hua) | Nakli | CICG |
| IoT fuel sensor (tank mein kitna tel) | Nakli | Post par lage sensors |
| Raste ka haal (khula/band) | Nakli | BRO ka road bulletin |
| Helicopter ke ghante | Nakli | IAF ka airlift schedule |
| Purana mausam (1995 se) | **Asli** | Open-Meteo (free, public) |
| Agle 16 din ka mausam | **Asli** | Open-Meteo forecast (Live mode) |
| Zameen ki oonchai | **Asli** | Copernicus DEM (European satellite data) |
| National highways (NH-1, NH-3), passes, shahar | **Asli** | OpenStreetMap |
| Aage ke roads/tracks, posts, roadheads | Nakli (fictional) | Unit ki apni jaankari |
| Demo ka aage ka mausam | Nakli | Oct 2021 ka asli mausam copy kiya (us saal jaldi barf giri thi) |

Military data classified hota hai, isliye wo nakli (simulated) hai. App mein har jagah chhote "Simulated" ya "Real data" chips lage hain, aur unpar mouse le jaane se source dikhta hai.

## 3. Forecast: kitna saaman roz lagega

- RASAD har post aur har saaman ke liye agle din se lekar raste khulne tak (May–June) ka roz ka andaaza lagata hai.
- Thand badhti hai to kerosene zyada lagta hai; jitni oonchi post, utni thand. Isliye mausam (asli) aur oonchai (asli) dekhkar andaaza lagta hai.
- Har andaaze ke saath ek **range (band)** hoti hai: "4 din, 3 se 5 ke beech, 80% bharosa".
- Do tareeke aapas mein muqabla karte hain:
  1. **Machine-learning model** (LightGBM): mausam, oonchai, saal ka din dekhkar sikhta hai.
  2. **Simple tareeka**: pichhle 28 din ka average.
- **Jo tareeka behtar nikle, wahi use hota hai.** Imaandari ke liye: tareeka ek pehle ke 60 din (27 Jun–25 Aug) par chuna jaata hai, aur score aakhri 60 din (26 Aug–24 Oct) par naapa jaata hai, jo chunav mein use hi nahi hue.
- Nateeja: **sirf kerosene ke liye model jeeta** (galti 9%, jabki average ki 39%), kyunki kerosene thand ke saath tezi se badalta hai. Ration, dawai, battery, kapde ke liye simple average utna hi achha tha, to wahi use hota hai (aur wo mausam ko dekhta hi nahi). Ye screen par "method aur why" mein likha hai.
- Band ko 80% ke aas-paas sahi baithaya gaya hai: aakhri 60 din mein 79–89% din band ke andar the.
- **Bahut zaroori imaandari:** ye sab **simulated data par naapa gaya hai**. Ye nakli khapat humne khud mausam aur oonchai ke ek formula se banayi thi, aur model wahi mausam aur oonchai dekhta hai. Isliye 9% asal mein bas wo "shor" (noise) hai jo humne daala tha. **Asli accuracy tabhi pata chalegi jab asli CICG data jude.** Screen par bhi har accuracy number ke saath yahi likha hai.

## 4. "Kitne din chalega" (days of cover)

Stock ko roz ke andaaze se din-ba-din ghataate hain; jis din stock khatam, wo din. Range ke saath dikhata hai, jaise "4 din (3–5)".

## 5. Point of No Return: aakhri safe din

- Passes ek fix date par band nahi hote. Isliye RASAD **passes (Zoji La, Manali–Leh) ke liye** ek **niyam** seekhta hai asli band hone ki dates se:
  - **Zoji La** gehri barf se band hota hai: "is sardi mein 210 cm barf ho chuki ho aur 3 din mein 20 cm aur gire, ya 7 din ka ausat thand −15.5 °C tak pahunche".
  - **Manali–Leh** zyada thand aur barf jamne (ice) se band hota hai: "7 din ka ausat −15.5 °C, ya 3 din mein 44 cm barf".
- Phir is sardi ke ab tak ke mausam ke baad **pichhli 31 asli sardiyon (1995–2025) ka mausam ek-ek karke chalaate hain**: "agar baaki sardi 1995 jaisi rahe to raasta kab band hoga? 1996 jaisi? ..." Isse 31 alag tareekhein milti hain, yani ek **probability**.
- "**80% confidence**" ka matlab: wo din jab tak 80% chance hai ki raasta khula rahega.
- **Aakhri safe dispatch din** = wo din − safar ke din − 1 din loading.
- Iske baad sirf hawai raasta bachta hai, to RASAD helicopter ke sorties, ghante aur kharcha dikhata hai.
- Imaandari: hamare paas sirf 4–5 saal ki band hone ki dates hain (Manali–Leh ki zyadatar dates "Low" confidence wale source se). Har saal ko alag rakhkar jaancha to galti Zoji La par ~13 din aur Manali–Leh par ~18 din aayi. Ye number screen par likha hai.
- **Aage ke roads aur tracks (jo posts tak jaate hain) ki koi public band-hone ki dates nahi hain.** Isliye unke liye Manali–Leh wala niyam hi PLACEHOLDER factors se scale kiya gaya hai (road/jeep/mule track ke liye kam barf par band, oonchai ke saath zyada barf, highway ke 30 din baad khulna). **Alpha (29 Oct) aur Foxtrot ki tareekhein isi placeholder niyam se aati hain**; sirf unka mausam asli hai. Point of no return screen par ye saaf likha hai.

## 6. Mixed-fleet plan: kaunsa saaman kis tareeke se

Google ka OR-Tools ek "puzzle solver" hai. RASAD use 7 din ka puzzle deta hai:
- Kaunse posts ko kitna saaman chahiye, aur kitna jaldi.
- Har tareeke ki seemayein: truck/jeep raasta khula ho tabhi, aur **sirf Point of No Return se pehle**; mule 40 kg, porter 20 kg, helicopter oonchai ke hisaab se kam payload; **drone 15 kg** (12,000–20,000 ft wale band mein, Army RFP ke hisaab se), 10 km range, aur pahad ke upar 400 m oonchai se udna zaroori.
- Mausam: helicopter aur drone sirf un dino jab hawa, barf aur baadal seema ke andar hon.
- Kitne mule, porter, jeep, helicopter ghante, drone aur batteries hain.

Solver sabse kam kharche wala plan dhoondhta hai, lekin zaroori saaman (dawai sabse pehle) pehle bhejta hai. Solver ko 20 second milte hain: agar wo tab tak ye sabit na kar paye ki plan sabse sasta hai, to screen par likha aata hai "Best plan found within the 20-second time limit". Har line ke saath **ek seedhi wajah, kharcha aur assumptions** likhe hote hain.

Demo mein:
- **Delta:** road bulletin ke hisaab se track band hai ("Blocked by fresh snow"), isliye dawai drone se jaati hai (19 sorties, 26 Oct).
- **Alpha:** kerosene zyadatar jeep se, 29 Oct se pehle.
- **Foxtrot:** ration aaj mule aur porter se, baaki helicopter se, kyunki sabse paas ke drones (Roadhead Lima) 19 km door hain aur range 10 km hai.

## 7. Drone advisor

Army 2,715 drones kharidne ki RFI laayi hai. Sawal hai ki drones kahan rakhein. RASAD har sambhav base par drones rakh kar poora plan dobara chalata hai, aur dekhta hai ki kitne helicopter sorties aur kitne rupaye bachte hain. Demo mein **Node Mike par 20 drones** rakhne se Foxtrot ke helicopter sorties **30 se 0** ho jaate hain aur **~₹1.67 crore** is hafte bachta hai. Imaandari: ye bachat PLACEHOLDER numbers par tiki hai (drone ka ₹1,500 per sortie, 2 battery, 90 min charging, 8 ghante udaan), ek hafte mein ek hi jagah se ~800 sorties maanti hai, aur maanti hai ki Node Mike tak saaman road se pehle pahunch gaya. Node Mike fictional jagah hai jo Foxtrot se ~9 km door rakhi gayi hai.

## 8. What-if

Ek click mein: "pass 10 din pehle band ho jaye", "blizzard 3 din helicopter rok de", "Alpha–Charlie mein 20% zyada troops", "20 drones aa jayein". RASAD sab dobara calculate karke pehle aur baad dikhata hai, aur badle hue khaane peele ho jaate hain.

## 8b. Data alerts (ajeeb khapat)

Model batata hai ki mausam, oonchai aur mausam-ke-din ke hisaab se roz kitni khapat **honi chahiye**. Asli khapat usse bahut zyada ho to alert aata hai:
- **Ek din bahut zyada, phir normal** → shayad data galat bhara gaya. Demo: Bravo ration, 14 Aug, 10.5×.
- **Kai din thoda zyada** (jo thand se samajh nahi aata) → shayad leak ya chori. Demo: Hotel kerosene, 15 din, 1.37×, +684 L.
- **Kai din bahut zyada** → shayad asli zaroorat (jaise altitude sickness). Demo: Charlie dawai, 3.1×.
- **Sensor chup** → Hotel ka fuel sensor 46 ghante se chup hai; RASAD inventory ka number use karta hai.

Har item ki apni "roz ki ghata-badhi" hoti hai (dawai zyada uchhalti hai, ration kam), isliye seema usi hisaab se tay hoti hai. **Ye sirf simulated data par jaancha gaya hai; asli data par seemayein dobara tune karni hongi.** Demo data mein jaan-boojh kar daali gayi teeno anomalies pakdi gayi; doosre random seeds par har baar lagbhag ek galat alarm bhi aaya. Alert sirf ek sawal hai, ilzaam nahi: har alert "Possible … — verify on ground" se shuru hota hai, aur faisla zameen par jaanch ke baad insaan karta hai.

## 9. Commander ka faisla aur audit log

Har plan line par Approve / Modify / Reject hai. Approve aur reject sirf Commander kar sakta hai; modify Commander ya Logistics Officer; Post QM sirf dekh sakta hai. Har faisla (kisne, kab, pehle kya tha, baad mein kya) audit log mein jaata hai.

## 10. Naya data kaise judta hai

Har stream ke liye ek chhoti config file hai (`sources/` folder). Usme likha hai ki file kahan hai, kaunsa column kya hai, aur codes ka matlab kya hai. Naya stream jodna = ek nayi file daalna aur "Sync all now" dabana. Agar data maujooda tables (stock, khapat, mausam, road status, airlift, terrain, map) mein fit ho, to app ka code nahi badalta, aur Army ke purane systems ko chhoona bhi nahi padta. Bilkul naye tarah ke data ke liye code likhna padega. CICG/BRO/IAF ke column names humne andaaze se banaye hain; asli format unit se milega.

"Sync all now" dabane par app pehle poochhta hai, kyunki uske baad har screen dobara calculate hoti hai (lagbhag ek minute). **Demo ke beech mat dabana.**

---

## Jury ke likely sawal aur chhote jawab

Har sawal ke saath "Bolne ke liye" wali line English mein hai, taaki seedha bol sakein.

**1. Is the military data safe? Why on-premise?**
Sab kuch ek laptop par chalta hai (asal mein Army ke apne network par). Koi cloud nahi; server sirf laptop ke andar (127.0.0.1) sunta hai, bahar se koi nahi jud sakta.
*Bolne ke liye:* "Nothing leaves the machine. It runs fully on-premise, on the Army's own network in deployment; no cloud."

**2. Where would the real data come from?**
CICG (Army ka inventory system), IQMP / Q-FORCE (unit logistics apps), post ke IoT sensors, BRO ka road bulletin, IAF ka airlift schedule. Abhi ye simulated hain kyunki asli data classified hai.
*Bolne ke liye:* "In deployment, stock and consumption come from CICG through adapters; roads from BRO, airlift from IAF, fuel levels from post sensors."

**3. What is real and what is simulated?**
Asli: mausam (1995 se), 16-din forecast, zameen ki oonchai, national highways aur passes, passes ke band hone ki dates, drone RFI ke numbers. Nakli: posts aur unke tracks, stock, khapat, troops, sensors, road bulletin, helicopter ghante. Har screen par chips se dikhta hai.
*Bolne ke liye:* "Weather, terrain, the national highways and pass-closure dates are real public data; the posts, their tracks and all military data are simulated and labelled as such."

**4. How accurate is your forecast?**
Aakhri 60 din par (jo chunav mein use nahi hue): kerosene 9% galti, ration ~6%, battery ~16%, dawai ~30%, kapde ~34%. 79–89% din range ke andar. Ye simulated data par hai, jo usi formula se bana jo model seekhta hai; asli accuracy asli CICG data par hi pata chalegi.
*Bolne ke liye:* "Measured on simulated data, kerosene is within 9 percent versus 39 percent for a simple average. That data was generated from the same weather inputs the model uses, so real accuracy is unknown until real CICG data is connected."

**5. Why does only kerosene use the machine-learning model?**
Kyunki sirf kerosene mein model saaf taur par jeeta. Baaki mein simple average utna hi achha tha, aur hum simple tareeke ko tab tak rakhte hain jab tak model saaf behtar na ho.
*Bolne ke liye:* "We pick whichever method wins on earlier data. Kerosene depends strongly on cold, so the model wins there; for the rest a 28-day average was just as good."

**6. How is the pass-closure probability calculated?**
Passes (Zoji La, Manali–Leh) ke liye asli band hone ki dates se niyam seekha (barf ya thand). Aage ke tracks ke liye isi niyam ko PLACEHOLDER factors se scale kiya. Phir is sardi ke baad pichhli 31 asli sardiyon ka mausam chalaya, aur 31 tareekhon se probability nikali. "80% confidence" = 80% chance raasta khula hai.
*Bolne ke liye:* "For the passes, the rule is fitted on real closure dates; forward tracks reuse it with placeholder scaling. Either way we replay this winter against 31 real past winters of weather, which gives a closure window with a probability, not a fixed date."

**7. How accurate is the closure rule?**
Har saal ko alag rakhkar jaancha: Zoji La ~13 din, Manali–Leh ~18 din. Dates sirf 4–5 saal ki hain, isliye ye bada nahi; asli BRO data se behtar hoga.
*Bolne ke liye:* "Tested on each past winter it was not trained on, it is within about two weeks. That is why we plan at 80 percent confidence, not the middle date."

**8. Why is air about 220 times costlier?**
Ek hi source se do numbers: truck ₹1 lakh mein 10 tonne Srinagar se Leh (yani ₹0.024 per kg per km), aur helicopter ₹4 lakh per 45 minute (The Week, 2020). Alpha tak road ₹3.8/kg, helicopter ₹844/kg (oonchai par kam payload). Ye PLACEHOLDER hai aur screen par inputs ke saath likha hai.
*Bolne ke liye:* "It is road ₹3.8 versus helicopter ₹844 per kg for Alpha, from one public 2020 report; it is tagged as a placeholder and the inputs are shown."

**9. What are your drone assumptions?**
Public: 15 kg 12,000–20,000 ft par, 20 kg neeche (Army RFP), 10 km range (RFI), Sabal-20 jaisi speed aur endurance. PLACEHOLDER: 2 batteries per drone, 90 min charge, 5 min swap, 8 ghante udaan, hawa 35 km/h tak, ₹1,500 per sortie. Har drone leg asli zameen se 400 m upar udna chahiye.
*Bolne ke liye:* "Payload and range come from the Army's own RFIs; batteries, wind limits and cost are placeholders, shown on every plan line."

**10. How does the drone advisor decide where to base drones?**
Har sambhav base par drones rakh kar poora plan dobara banata hai, aur jahan sabse zyada helicopter sorties aur paisa bachta hai, wo jeetta hai.
*Bolne ke liye:* "It re-plans the week with the drones at each candidate base and ranks the bases by the helicopter hours and money saved."

**11. How does it connect to existing Army systems?**
Purane systems ko badalta nahi. Unki export file padhta hai, ek config file ke zariye. HQ IDS ka Joint Primer (Aug 2025) bhi yahi kehta hai: API se jodo, purane systems ko disturb kiye bina.
*Bolne ke liye:* "It reads exports from CICG and other systems through adapters, exactly the 'interoperability without disrupting existing platforms' the tri-service Joint Primer recommends."

**12. What happens if the internet is down?**
Kuch nahi hota. Sab kuch laptop par saved hai. Sirf Live mode ka "naya forecast download" internet maangta hai; tab bhi pichhla saved forecast chalta rehta hai.
*Bolne ke liye:* "It works fully offline. Only refreshing the live weather forecast needs internet, and the last forecast stays cached."

**13. How is a new data source added?**
`sources/` folder mein ek config file, aur "Sync all now". Agar data maujooda tables mein fit ho to code nahi badalta; naye tarah ke data ke liye code chahiye.
*Bolne ke liye:* "One config file per data stream; if it fits the existing tables, add a file, press sync, and it appears with its health status."

**14. What if the commander disagrees with the plan?**
Modify (matra badlo) ya Reject. Har faisla audit log mein.
*Bolne ke liye:* "The system recommends; the commander decides. Every approve, change or reject is logged with who and when."

**15. Who can approve? Is there a login?**
Demo mein role picker hai (Commander, Logistics Officer, Post QM). Asal mein Army ka apna login (SSO/PKI) hoga.
*Bolne ke liye:* "Roles are demo-only here; in deployment the identity comes from the Army's own login."

**16. Why not use a fixed closure date like everyone else?**
Kyunki har saal alag hota hai: Zoji La kabhi Dec mein band hua, kabhi Feb mein. Fixed date ya to bekaar jaldi karwati hai ya der.
*Bolne ke liye:* "Closures vary by weeks year to year; a probability window tells you how much risk you take by waiting."

**17. What is the IoT sensor doing? What if a sensor fails?**
Har post ke tank par sensor har 4 ghante level bhejta hai, jo CICG se zyada taaza hota hai. Post Hotel ka sensor 23 Oct se chup hai; Sources page par warning dikhti hai aur RASAD apne aap CICG ka number use karta hai.
*Bolne ke liye:* "Sensors give fresher fuel levels; a silent sensor is flagged and the system falls back to the inventory figure."

**18. How did you make sure the fictional posts are not real locations?**
Posts ke naam aur jagah fictional hain, Ladakh ke andar ki taraf. Har post kisi bhi border/LoC/LAC se 60 km se zyada door hai, aur OpenStreetMap ki kisi military jagah se 12 km se zyada. Map par koi international boundary nahi dikhti.
*Bolne ke liye:* "All posts are fictional, at least 60 km from any boundary, and we never draw boundary lines."

**19. Aren't mules being phased out? Why plan with them?**
Army ne Animal Transport units band karna ~2032 tak taal diya hai (SP's Land Forces, Nov 2025). Aage ka raasta mixed fleet hai: truck + helicopter + mule + porter + drone.
*Bolne ke liye:* "The Army has deferred disbanding mule units to around 2032; the near future is a mixed fleet, which is what we plan."

**20. How is this different from other teams?**
Drones ek asli tareeke ki tarah (RFI payload, battery, zameen), drone basing advisor, band hone ki **probability** (fixed date nahi) dono rasto ke liye, mixed-fleet plan har line ki wajah ke saath, adapters, aur har number ke saath source tag.
*Bolne ke liye:* "Drones as a real mode with a basing advisor, closure as a probability window, a mixed-fleet plan with reasons, and plug-in adapters."

**21. Can it handle a real sector with many more posts?**
Abhi tak bade sector par test nahi kiya. Demo ka hafta seconds mein hal hota hai. Bhaari input (troops ×1.5) par solver apni 20 second ki limit par ruk gaya, aur tab app "best plan found within time limit" dikhata hai. Bade sector ke liye ye limit aur model ko tune karna padega.
*Bolne ke liye:* "This week's plan solves in seconds. On heavier inputs the solver stops at a 20-second limit and the screen says it is the best plan found within that limit; scaling to a full sector still needs testing."

**22. Can it catch pilferage or wrong entries?**
Haan, ek pehli jaanch ke roop mein. Jo khapat mausam se samajh nahi aati, wo alert banti hai: ek din ki chhalaang = shayad galat entry; kai din thodi zyada = shayad leak ya chori; kai din bahut zyada = shayad asli zaroorat. Ye sirf sawal hai, faisla insaan karta hai.
Ye sirf simulated data par jaancha gaya hai; doosre random seeds par lagbhag ek galat alarm har baar aaya. Asli data par seemayein dobara tune karni hongi.
*Bolne ke liye:* "It flags use that the weather cannot explain: a one-day spike as a likely entry error, a steady excess as a possible leak or pilferage, and a surge to confirm with the post. Each alert is a question, not an accusation. It is tested on simulated data; the thresholds need tuning on real data."

**23. What does PLACEHOLDER mean?**
Wo numbers jo hume public source mein nahi mile, jaise kharcha, mule ki ginti, battery. App mein peele chips se dikhte hain aur `docs/PLACEHOLDERS.md` mein list hain. User unit asli numbers dalegi.
*Bolne ke liye:* "Numbers without a public source are tagged as placeholders, on screen and in a list, for the user unit to replace."

### Teen baatein jo hum khud maan lete hain (jury poochhe ya na poochhe)

**24. Is your 9% forecast accuracy real?**
Nahi, asli duniya ke liye nahi. Nakli khapat humne mausam aur oonchai ke formula se banayi thi, aur model wahi mausam aur oonchai dekhta hai. Isliye model ne apna hi formula wapas seekh liya; 9% bas wo noise hai jo humne daala tha. Ye dikhata hai ki code sahi chalta hai, ye nahi ki asli data par kitna sahi hoga.
*Bolne ke liye:* "No. It is measured on simulated data that we generated from the same weather inputs the model uses, so it only shows the pipeline works. Real accuracy is unknown until real CICG data is connected."

**25. Are the last-road-day dates for the posts learned from real closures?**
Sirf passes (Zoji La, Manali–Leh) ke liye. Posts tak jaane wale roads aur tracks ki koi public dates nahi hain, isliye unke liye Manali–Leh ka niyam PLACEHOLDER factors se scale kiya hai. Alpha ka 29 Oct isi se aata hai; mausam asli hai, niyam placeholder.
*Bolne ke liye:* "Only the pass closures are learned from real dates. Forward-track dates, like Alpha's 29 October, use a placeholder scaling of that rule on real weather; a unit's own track records would replace it."

**26. Did you design the demo scenario?**
Haan. Teen kam stock wale items (Alpha kerosene, Delta dawai, Foxtrot ration) simulated data mein jaan-boojh kar daale gaye. Delta ka band track road bulletin ki ek likhi hui line hai. Node Mike ko Foxtrot ke paas rakha gaya. Hisaab sab asli code karta hai: inputs badlo (troops, tareekh, mausam, drones) to nateeje sahi disha mein badalte hain.
*Bolne ke liye:* "Yes. The shortages and the closed track are planted in the simulated data so the demo has a story. The calculations are real: change any input and the results change accordingly; we tested that."

## Kamiyan (limitations), imaandari se

- Military data simulated hai; accuracy asli CICG data par hi pata chalegi, aur abhi ka score circular hai (data usi formula se bana jo model seekhta hai).
- Demo scenario design kiya gaya hai (3 kam stock items, Delta ka band track, Node Mike ki jagah).
- Band hone ka niyam sirf 4–5 saal ki dates se seekha hai; galti ~2 hafte.
- Kharche ek 2020 news report se hain (PLACEHOLDER).
- Aage ke tracks kab band honge, uske niyam PLACEHOLDER hain (posts ki aakhri tareekhein inhi se aati hain).
- Drone bachat placeholder drone kharch aur battery numbers par tiki hai.
- Alerts ki seemayein simulated data par tay hain; asli data par tune karni hongi.
- Drone base ke liye maana gaya hai ki use raasta band hone se pehle stock kar diya gaya.
- Roles demo ke liye hain, asli login nahi.
- Live mode pehli baar 30–60 sec leta hai; laptop aur projector ke liye bana hai, phone ke liye nahi.
