import tkinter as tk
from sys import exit

type Number = int | float

root = tk.Tk()
root.title("БЯС - Божи Ярост Симулатор Beta 2.1.1")
root.geometry("1200x800")

DARK_BG = "#1E1E1E"
root.configure(bg=DARK_BG)

TICK_RATE_MS = 33
TIME_FACTOR = TICK_RATE_MS / 1000.0


active_hold_job = None
"""Holds the current active root.after id for buying, so we can cancel it on release"""

HOLD_DELAY_MS: int = 10


def format_number(number: Number) -> str:
    if number < 1e9 - 1:
        return f"{number:.2f}"

    if number == float("inf"):
        return "∞"

    return f"{number:.2E}".replace("+", "").lower()


class Factory:
    def __init__(
        self,
        ime: str,
        basecena: Number,
        pravi: str | None = None,
        cost_multiplier: Number = 1e3,
    ):
        self.ime = ime
        self.basecena = basecena
        self.pravi = pravi
        self.cost_multiplier = cost_multiplier
        self.purchased = 0

    def vzemicena(self) -> Number:
        tier = self.purchased // 10
        return self.basecena * (self.cost_multiplier**tier)

    def vzemi_buy_10_multiplier(self) -> Number:
        tier = self.purchased // 10
        return 2**tier

    def info_proizvodstvo_za_sekunda(self, world: dict[str, Number]) -> Number:
        kolko_imam = world.get(self.ime, 0)
        bonus = self.vzemi_buy_10_multiplier()
        return kolko_imam * bonus * world["tickspeed_multiplier"]

    def kupi(self, world) -> bool:
        cena = self.vzemicena()

        if world["rage"] < cena:
            return False

        world["rage"] -= cena
        world[self.ime] += 1
        self.purchased += 1

        return True

    def suzdai(self, world: dict[str, Number]) -> None:
        if self.pravi is None:
            return

        proizvodstvo_za_sekunda = self.info_proizvodstvo_za_sekunda(world)
        world[self.pravi] += proizvodstvo_za_sekunda * TIME_FACTOR


def kupi_monster() -> bool:
    cena = world["monster_cena"]

    if world["rage"] < cena:
        return False

    world["rage"] -= cena
    world["monster_count"] += 1
    world["tickspeed_multiplier"] *= 1.20
    world["monster_cena"] *= 10
    update_ui()

    return True


def update_ui() -> None:
    current_rage = world["rage"]
    rps = factories["iliq"].info_proizvodstvo_za_sekunda(world)

    cena = format_number(world["monster_cena"])
    broi = world["monster_count"]
    btn_monster.config(text=f"🍍 Купи Монстър ({broi}) - Цена: {cena}")

    if current_rage >= world["monster_cena"]:
        btn_monster.config(bg="#FFD700", fg="black", activebackground="#E6C200")
    else:
        btn_monster.config(bg="#4A4316", fg="#A0A0A0", activebackground="#4A4316")

    label_tickspeed.config(text=f"Текуща Скорост: {world['tickspeed_multiplier']:.2f}x")
    label_rage.config(text=f"Ярост: {format_number(current_rage)}")
    label_rps.config(text=f"Гняв за секунда (ГЗС): {format_number(rps)}")

    for name in поредност_бутони:
        f = factories[name]
        m = f.vzemi_buy_10_multiplier()
        cena_sgrada = f.vzemicena()

        # Update each text component safely inside its column cell
        ui_rows[name]["count"].config(text=format_number(world[name]))
        ui_rows[name]["purchased"].config(text=f"| Купени: {f.purchased}")
        ui_rows[name]["bonus"].config(text=f"| Бонус: x{m}")

        btn = ui_rows[name]["button"]
        btn.config(text=f"Купи ({format_number(cena_sgrada)})")

        if current_rage >= cena_sgrada:
            btn.config(bg="#2ECC71", fg="black", activebackground="#27AE60")
        else:
            btn.config(bg="#3A3A3A", fg="#888888", activebackground="#2B2B2B")


def game_tick() -> None:
    if world["rage"] >= 1.76e308:
        crash_out_screen()
        return

    for factory in factories.values():
        factory.suzdai(world)

    update_ui()
    root.after(TICK_RATE_MS, game_tick)


# --- HOLD ACTION LOGIC ---
def start_buying_building(name) -> None:
    global active_hold_job

    if factories[name].kupi(world):
        update_ui()
        # Keep buying as long as the mouse button is held down
        active_hold_job = root.after(HOLD_DELAY_MS, lambda: start_buying_building(name))
    else:
        # If player runs out of money, stop trying to loop to save performance
        stop_buying()


def start_buying_monster() -> None:
    global active_hold_job

    if kupi_monster():
        active_hold_job = root.after(HOLD_DELAY_MS, start_buying_monster)
    else:
        stop_buying()


def stop_buying(_=None) -> None:
    global active_hold_job

    if active_hold_job is not None:
        root.after_cancel(active_hold_job)
        active_hold_job = None


def crash_out_screen() -> None:  # ЕНДИНГ
    stop_buying()  # Ensure any active hold loops are stopped
    for widget in root.winfo_children():
        widget.destroy()

    # za da promenish neshtoot promeni cvetovete v currentbg milisekundite v root.after kolko chesto i nai dolu flash() kolko puti da se smenqt
    def flash(count) -> None:
        if count > 0:
            current_bg = R"#B30000" if count % 2 == 0 else "#FFFFFF"
            root.configure(bg=current_bg)
            root.after(100, lambda: flash(count - 1))
            return

        root.configure(bg="#B30000")
        root.rowconfigure(0, weight=1)
        root.rowconfigure(1, weight=1)
        root.columnconfigure(0, weight=1)
        label_infinite = tk.Label(
            root,
            text="Ярост: Безкрайна",
            font=("Courier", 42, "bold"),
            bg=R"#B30000",
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

    flash(16)


поредност_бутони: list[str] = [
    "iliq",
    "pushka",
    "megailiq",
    "gigailiq",
    "terailiq",
    "petailiq",
    "exailiq",
    "zettailiq",
]

ИМЕНА_ЗА_UI: dict[str, str] = {
    "iliq": "Разглобена Клавиатура",
    "pushka": "Загуба",
    "megailiq": "Изгубено 1v1",
    "gigailiq": "Wallhack",
    "terailiq": "Лоши Хора",
    "petailiq": "Лоши Времена",
    "exailiq": "Еврейн",
    "zettailiq": "Синагога",
}

factories: dict[str, Factory] = {
    "zettailiq": Factory("zettailiq", 1e24,  "exailiq",  1e15),
      "exailiq": Factory("exailiq",   1e18,  "petailiq", 1e12),
     "petailiq": Factory("petailiq",  1e13,  "terailiq", 1e10),
     "terailiq": Factory("terailiq",  1e9,   "gigailiq", 1e8),
     "gigailiq": Factory("gigailiq",  1e6,   "megailiq", 1e6),
     "megailiq": Factory("megailiq",  10000, "pushka",   1e5),
       "pushka": Factory("pushka",    100,   "iliq",     1e4),
         "iliq": Factory("iliq",      10,    "rage",     1e3),
}  # fmt: off

world: dict[str, Number] = {
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

инструкции: str = """\
💡 Всяко нещо произвежда предишното.
Всеки 10 купени качват цената и удвояват производството.
Monster Energy прави времето 20% по-бързо.
Целта е да достигнеш 1.79е308 Ярост - маx стойност, която може да се представи в стандартен компютърен тип double.
Може да задържаш вместо да спамиш бутоните!\
"""

label_instructions = tk.Label(
    root,
    text=инструкции,
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

# Column sizes adjusted to perfectly fit "Купени:" and "Бонус:" text lengths
game_frame.columnconfigure(0, minsize=220)  # Column 0: Factory Name
game_frame.columnconfigure(1, minsize=140)  # Column 1: Quantity Owned
game_frame.columnconfigure(2, minsize=130)  # Column 2: | Купени: X
game_frame.columnconfigure(3, minsize=180)  # Column 3: | Бонус: xX
game_frame.columnconfigure(4, weight=1)  # Column 4: Action Button

ui_rows = {}

for i, b_name in enumerate(поредност_бутони):
    красиво_име = ИМЕНА_ЗА_UI.get(b_name, b_name.capitalize())

    # Column 0: Name
    lbl_name = tk.Label(
        game_frame,
        text=красиво_име,
        font=("Courier", 11, "bold"),
        anchor="w",
        bg=DARK_BG,
        fg="#FFFFFF",
    )
    lbl_name.grid(row=i, column=0, sticky="w", pady=6)

    # Column 1: Total Amount Owned
    lbl_count = tk.Label(
        game_frame,
        text="0.00",
        font=("Courier", 11),
        anchor="e",
        bg=DARK_BG,
        fg="#2ECC71",
    )
    lbl_count.grid(row=i, column=1, sticky="e", padx=10, pady=6)

    # Column 2: Purchased count with text and separator
    lbl_purchased = tk.Label(
        game_frame,
        text="| Купени: 0",
        font=("Courier", 10),
        anchor="w",
        bg=DARK_BG,
        fg="#888888",
    )
    lbl_purchased.grid(row=i, column=2, sticky="w", padx=5, pady=6)

    # Column 3: Multiplier Bonus with text and separator
    lbl_bonus = tk.Label(
        game_frame,
        text="| Бонус: x1",
        font=("Courier", 10),
        anchor="w",
        bg=DARK_BG,
        fg="#FFD700",
    )
    lbl_bonus.grid(row=i, column=3, sticky="w", padx=5, pady=6)

    # Column 4: Buy Button
    row_btn = tk.Button(
        game_frame, text="", width=22, relief="flat", font=("Helvetica", 10)
    )
    row_btn.bind(
        "<ButtonPress-1>",
        lambda event, name=b_name: start_buying_building(name),
    )
    row_btn.bind("<ButtonRelease-1>", stop_buying)
    row_btn.grid(row=i, column=4, sticky="e", pady=6)

    ui_rows[b_name] = {
        "count": lbl_count,
        "purchased": lbl_purchased,
        "bonus": lbl_bonus,
        "button": row_btn,
    }


def cheat_code(_) -> None:
    world["iliq"] = 1e307
    update_ui()


root.bind("<Return>", cheat_code)
game_tick()
root.mainloop()
