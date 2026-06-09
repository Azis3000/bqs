import math
import tkinter as tk
from sys import exit

root = tk.Tk()
root.title("Boji rage simulator")
root.geometry("750x550")

DARK_BG = "#1E1E1E"
root.configure(bg=DARK_BG)

TICK_RATE_MS = 33
TIME_FACTOR = TICK_RATE_MS / 1000.0

# Holds the current active root.after id for buying, so we can cancel it on release
active_hold_job = None
HOLD_DELAY_MS = 100  # How fast it buys while holding (100ms = 10 times per second)


def format_number(num):
    if num < 1_000_000:
        return str(int(num))
    else:
        exponent = int(math.log10(num))
        base = num / (10**exponent)
        return f"{base:.2f}e{exponent}"


class Factory:
    def __init__(self, ime, basecena, pravi=None, stepen=1, cost_multiplier=1e3):
        self.ime = ime
        self.basecena = basecena
        self.pravi = pravi
        self.stepen = stepen
        self.cost_multiplier = cost_multiplier
        self.purchased = 0

    def vzemicena(self):
        tier = self.purchased // 10
        return self.basecena * (self.cost_multiplier**tier)

    def vzemi_buy_10_multiplier(self):
        tier = self.purchased // 10
        return 2**tier

    def info_proizvodstvo_za_sekunda(self, world):
        kolko_imam = world.get(self.ime, 0)
        bonus = self.vzemi_buy_10_multiplier()
        return (
            kolko_imam
            * (2 ** (self.stepen - 1))
            * bonus
            * world["tickspeed_multiplier"]
        )

    def kupi(self, world):
        cena = self.vzemicena()
        if world["rage"] >= cena:
            world["rage"] -= cena
            world[self.ime] += 1
            self.purchased += 1
            return True
        return False

    def suzdai(self, world):
        if self.pravi:
            proizvodstvo_za_sekunda = self.info_proizvodstvo_za_sekunda(world)
            world[self.pravi] += proizvodstvo_za_sekunda * TIME_FACTOR


def kupi_monster():
    cena = world["monster_cena"]
    if world["rage"] >= cena:
        world["rage"] -= cena
        world["monster_count"] += 1
        world["tickspeed_multiplier"] *= 1.20
        world["monster_cena"] *= 10
        update_ui()
        return True
    return False


def update_ui():
    current_rage = world["rage"]
    rps = factories["iliq"].info_proizvodstvo_za_sekunda(world)

    btn_monster.config(
        text=f"🍍 Купи Monster Energy ({world['monster_count']}) - Цена: {format_number(world['monster_cena'])}"
    )
    if current_rage >= world["monster_cena"]:
        btn_monster.config(bg="#FFD700", fg="black", activebackground="#E6C200")
    else:
        btn_monster.config(bg="#4A4316", fg="#A0A0A0", activebackground="#4A4316")

    label_tickspeed.config(
        text=f"Текущ Tickspeed: {world['tickspeed_multiplier']:.3f}x"
    )
    label_rage.config(text=f"Rage: {format_number(current_rage)}")
    label_rps.config(text=f"Rage per second (RPS): {format_number(rps)}")

    for name in поредност_бутони:
        f = factories[name]
        m = f.vzemi_buy_10_multiplier()
        красиво_име = ИМЕНА_ЗА_UI.get(name, name.capitalize())
        cena_sgrada = f.vzemicena()

        info_text = f"{красиво_име.ljust(12)}: {format_number(world[name]).ljust(8)} (Купени: {str(f.purchased).ljust(3)}) | Бонус: x{str(m).ljust(4)}"
        ui_rows[name]["label"].config(text=info_text)

        btn = ui_rows[name]["button"]
        btn.config(text=f"Купи ({format_number(cena_sgrada)})")

        if current_rage >= cena_sgrada:
            btn.config(bg="#2ECC71", fg="black", activebackground="#27AE60")
        else:
            btn.config(bg="#3A3A3A", fg="#888888", activebackground="#2B2B2B")


def game_tick():
    if world["rage"] >= 1.77e308:
        crash_out_screen()
        return

    for f in factories.values():
        f.suzdai(world)

    update_ui()
    root.after(TICK_RATE_MS, game_tick)


# --- HOLD ACTION LOGIC ---
def start_buying_building(name):
    global active_hold_job
    if factories[name].kupi(world):
        update_ui()
        # Keep buying as long as the mouse button is held down
        active_hold_job = root.after(HOLD_DELAY_MS, lambda: start_buying_building(name))
    else:
        # If player runs out of money, stop trying to loop to save performance
        stop_buying()


def start_buying_monster():
    global active_hold_job
    if kupi_monster():
        active_hold_job = root.after(HOLD_DELAY_MS, start_buying_monster)
    else:
        stop_buying()


def stop_buying(event=None):
    global active_hold_job
    if active_hold_job is not None:
        root.after_cancel(active_hold_job)
        active_hold_job = None


def crash_out_screen():
    stop_buying()  # Ensure any active hold loops are stopped
    for widget in root.winfo_children():
        widget.destroy()

    RED_BG = "#B30000"
    root.configure(bg=RED_BG)

    root.rowconfigure(0, weight=1)
    root.rowconfigure(1, weight=1)
    root.columnconfigure(0, weight=1)

    label_infinite = tk.Label(
        root,
        text="RAGE: INFINITY",
        font=("Courier", 42, "bold"),
        bg=RED_BG,
        fg="#FFFFFF",
    )
    label_infinite.grid(row=0, column=0, sticky="s", pady=20)

    btn_crash = tk.Button(
        root,
        text="CRASH OUT",
        font=("Helvetica", 20, "bold"),
        bg="#FFFFFF",
        fg="black",
        activebackground="#DDDDDD",
        activeforeground="black",
        padx=30,
        pady=15,
        relief="raised",
        command=exit,
    )
    btn_crash.grid(row=1, column=0, sticky="n", pady=20)


поредност_бутони = [
    "iliq",
    "pushka",
    "megailiq",
    "gigailiq",
    "terailiq",
    "petailiq",
    "exailiq",
    "zettailiq",
]

ИМЕНА_ЗА_UI = {
    "iliq": "Разглобена Клавиатура",
    "pushka": "Загуба",
    "megailiq": "Изгубено 1v1",
    "gigailiq": "Wallhack",
    "terailiq": "Лоши Хора",
    "petailiq": "Лоши Времена",
    "exailiq": "Еврейн",
    "zettailiq": "Синагога",
}

factories = {
    "zettailiq": Factory(
        "zettailiq", basecena=1e24, cost_multiplier=1e15, pravi="exailiq"
    ),
    "exailiq": Factory(
        "exailiq", basecena=1e18, cost_multiplier=1e12, pravi="petailiq"
    ),
    "petailiq": Factory(
        "petailiq", basecena=1e13, cost_multiplier=1e10, pravi="terailiq"
    ),
    "terailiq": Factory(
        "terailiq", basecena=1e9, cost_multiplier=1e8, pravi="gigailiq"
    ),
    "gigailiq": Factory(
        "gigailiq", basecena=1e6, cost_multiplier=1e6, pravi="megailiq"
    ),
    "megailiq": Factory(
        "megailiq", basecena=10000, cost_multiplier=1e5, pravi="pushka"
    ),
    "pushka": Factory("pushka", basecena=100, cost_multiplier=1e4, pravi="iliq"),
    "iliq": Factory("iliq", basecena=10, cost_multiplier=1e3, pravi="rage"),
}

world = {
    "rage": 10,
    "iliq": 0,
    "pushka": 0,
    "megailiq": 0,
    "gigailiq": 0,
    "terailiq": 0,
    "petailiq": 0,
    "exailiq": 0,
    "zettailiq": 0,
    "tickspeed_multiplier": 1.0,
    "monster_count": 0,
    "monster_cena": 1000,
}

btn_monster = tk.Button(root, text="", font=("Helvetica", 11, "bold"), relief="raised")
# Bind mouse down and mouse up for hold capability
btn_monster.bind("<ButtonPress-1>", lambda event: start_buying_monster())
btn_monster.bind("<ButtonRelease-1>", stop_buying)
btn_monster.pack(pady=(15, 2), fill="x", padx=40)

label_tickspeed = tk.Label(
    root, text="", font=("Courier", 10, "italic"), bg=DARK_BG, fg="#AAAAAA"
)
label_tickspeed.pack(pady=(0, 15))

label_rage = tk.Label(
    root, text="", font=("Courier", 22, "bold"), bg=DARK_BG, fg="#FF4D4D"
)
label_rage.pack(anchor="center")

label_rps = tk.Label(root, text="", font=("Courier", 11), bg=DARK_BG, fg="#FFFFFF")
label_rps.pack(anchor="center", pady=(0, 10))

инструкции_текст = "💡 Всяко нещо произвежда предишното. Всеки 10 купени качват цената и удвояват производството.  \n Monster Energy прави времето 20% по-бързо. \n Целта е да достигнеш 1.79е308 Rage - маx стойност, която може да се представи в стандартен компютърен тип double. \n Може да задържаш вместо да спамиш бутоните!"
label_instructions = tk.Label(
    root,
    text=инструкции_текст,
    font=("Helvetica", 9, "italic"),
    bg=DARK_BG,
    fg="#BBBBBB",
    justify="center",
)
label_instructions.pack(anchor="center", pady=(5, 0))

divider = tk.Label(
    root,
    text="-----------------------------------------------------------------------------",
    font=("Courier", 10),
    bg=DARK_BG,
    fg="#555555",
)
divider.pack()

game_frame = tk.Frame(root, bg=DARK_BG)
game_frame.pack(pady=10, padx=40, fill="x")

ui_rows = {}

for i, b_name in enumerate(поредност_бутони):
    row_label = tk.Label(
        game_frame,
        text="",
        font=("Courier", 10),
        anchor="w",
        justify="left",
        bg=DARK_BG,
        fg="#FFFFFF",
    )
    row_label.grid(row=i, column=0, sticky="w", padx=(0, 20), pady=4)

    row_btn = tk.Button(game_frame, text="", width=15, relief="flat")
    # Bind hold logic to the building buttons
    row_btn.bind(
        "<ButtonPress-1>", lambda event, name=b_name: start_buying_building(name)
    )
    row_btn.bind("<ButtonRelease-1>", stop_buying)
    row_btn.grid(row=i, column=1, sticky="e", pady=4)

    ui_rows[b_name] = {"label": row_label, "button": row_btn}


def cheat_code(event):
    world["iliq"] = 1e300
    update_ui()


root.bind("<Return>", cheat_code)
game_tick()
root.mainloop()
