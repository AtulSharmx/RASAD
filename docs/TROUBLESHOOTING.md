# Troubleshooting: demo ke dauraan kuch toote to

Ghabraiye mat. Har samasya ke saath seedha upaay likha hai. Ye sab 6 Oct 2026 ke dry run mein, **internet band karke**, jaanche gaye the.

## Sabse zaroori 3 baatein

1. **Kaali RASAD window band mat karna.** Wahi RASAD chalata hai. Galti se band ho jaye to `start.bat` dobara double-click karo (1 minute).
2. **Demo galti se band ho gaya?** Browser ke address bar mein ye kholo (N = moment number):
   `http://localhost:8000/#/dashboard?demo=N`
   Jaise moment 5 ke liye `...?demo=5`. Moments: 1 risk, 2 point of no return, 3 plan, 4 drones, 5 what-if, 6 sources, 7 approve.
3. **Kuch bhi ajeeb dikhe:** **Ctrl + F5** (page poora reload). Phir bhi theek na ho to RASAD window band karo, `start.bat` dobara chalao.

## Samasya aur upaay

| Kya dikh raha hai | Kyun hota hai | Kya karein |
|---|---|---|
| Screens par grey patti (loading) 30–40 second tak | RASAD shuru hone ke baad results taiyaar kar raha hai | Ruko. Demo se 10 min pehle `start.bat` chalao, aur ek baar Guided demo khol kar band karo, taaki sab garam ho jaye |
| "Could not load this screen" | RASAD window band hai, ya abhi shuru ho raha hai | RASAD window khuli hai? Nahi to `start.bat`. Hai to 20 sec ruko, phir **Try again** |
| Galat screen khul gayi | Kisi ne galat button daba diya | Guided demo card par **Back / Next**, ya baayein nav se sahi screen. Ya `?demo=N` wala address |
| Guided demo card kuch dhak raha hai | Card spotlight ke ulti taraf aata hai (moment 1 mein map ke khaali upar-daayein kone mein); bahut chhoti screen par phir bhi dhak sakta hai | Card ke andar **Close**, baat karo, phir `?demo=N` se wapas aao |
| "Sync all now" daba diya, ab screens loading dikha rahi hain | Sync har source dobara padhta hai aur har screen dobara calculate hoti hai (app pehle poochhta bhi hai) | ~1 minute ruko, phir **Ctrl + F5**. Demo ke beech ye button mat dabao |
| Pichhli practice ke "Approved" stamp ya audit entries dikh rahe hain | Approvals database mein save rehte hain | RASAD window band karo → `reset_demo.bat` (1 min se kam) → `start.bat` |
| `reset_demo.bat` kehta hai "RASAD is still running" | Reset sirf tab hota hai jab RASAD band ho | RASAD window band karo, phir reset dobara |
| Dobara `start.bat` dabaya to sirf browser khula | RASAD pehle se chal raha hai; ye sahi hai | Kuch nahi karna. Wahi browser tab use karo |
| Screen purani ya alag dikh rahi hai | Browser ne purana page yaad rakha | **Ctrl + F5** |
| Projector par sab chhota ya bahut bada | Browser zoom | **Ctrl + 0** (100%), **F11** (full screen). Zaroorat ho to **Ctrl +** ya **Ctrl −** |
| Map khaali ya aadha | Map ka size abhi set ho raha hai | 2 sec ruko, ya browser window ka size thoda badlo / Ctrl + F5 |
| Live mode bahut der le raha hai | Live pehli baar sab dobara calculate karta hai (~15–60 sec) | Demo mein **Demo** hi rakho. Live sirf jury ke poochhne par dikhao |
| "No internet connection. RASAD keeps using the saved forecast" | Live mode mein naya forecast download karna chaha, internet nahi hai | Ye theek hai. RASAD saved forecast se chalta rehta hai. Bol sakte ho: "It works offline" |
| Role "Post QM" par Approve button band hai | Sahi hai: sirf Commander approve kar sakta hai | Upar daayein role **Commander** karo |
| Start par "Windows is checking the new files" | Windows Smart App Control nayi files ek baar jaanchta hai | Ruko; `start.bat` khud 3 baar koshish karta hai |
| `start.bat` par "Something went wrong" | Kuch install ya data toota | Window ki photo lo. Fir: `reset_demo.bat`, phir `start.bat`. Na chale to neeche "naye laptop par" dekho |
| Port / "address already in use" error | Ek aur RASAD pehle se chal raha hai | Saari RASAD windows band karo, phir ek baar `start.bat` |
| Laptop so gaya (sleep) aur screen ruk gayi | Sleep ke baad browser connection toot sakta hai | **Ctrl + F5**. Demo ke din laptop charger par rakho aur sleep band karo |

## Naye laptop par pehli baar (internet chahiye, sirf ek baar)

1. Python 3.12 ya naya install karo (python.org; install mein "Add to PATH" tick karo).
2. Node.js 18 ya naya install karo (nodejs.org, LTS).
3. RASAD folder copy karo (GitHub se ya pen drive se), aur `start.bat` double-click karo. Ye packages install karega aur screens banayega (5–10 minute).
4. Uske baad internet ki zaroorat nahi.

Tip: demo wale laptop par ek baar poora `start.bat` chala kar Guided demo pehle se check kar lo.

## Check karna ho ki sab theek hai

RASAD band karke ye command chalao (folder mein, terminal se):

```bat
.venv\Scripts\python -m backend.selfcheck
```

`selfcheck OK` aaye to backend sahi hai.
