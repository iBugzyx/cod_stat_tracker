import sys
import os 
import json
import tkinter as tk
from PIL import ImageTk, Image
from tkinter import ttk, messagebox, filedialog
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive

"""
try and build and dl exe to google drive for use by others. or git hub it
dark mode
work on ui
better user experience

"""
# Google Drive Authentication

gauth = GoogleAuth()
client_secrets_file = os.path.abspath("main/client_secrets.json")
credentials_file = os.path.abspath("main/credentials.json")

print(f"Client secrets file path: {client_secrets_file}")
print(f"Credentials file path: {credentials_file}")

if not os.path.exists(client_secrets_file):
    print(f"Client secrets file does not exist at path: {client_secrets_file}")
else:
    print(f"Client secrets file found at path: {client_secrets_file}")

gauth.settings["client_config_file"] = client_secrets_file

gauth.LoadCredentialsFile(credentials_file)

try:
    if gauth.credentials is None:
        gauth.LocalWebserverAuth()
    elif gauth.access_token_expired:
        gauth.Refresh()
    else:
        gauth.Authorize()
except Exception as e:
    print(f"Failed to authenticate: {e}")
    gauth.LocalWebserverAuth()

gauth.SaveCredentialsFile(credentials_file)

drive = GoogleDrive(gauth)

json_file_path = "cod_ireland_stats.json"

players = ["Bapper", "Jordy", "Stevo", "Varel", "Mixo", "Hok-Tuah"]
maps = ["Vault", "Skyline", "Rewind", "Protocall", "Red Card"]
game_modes = ["Hardpoint", "Control", "Search and Destroy"]
objectives = ["Time on Hill", "Plants", "Captures"]
match_data = []
current_series = {"Series Number": 1, "Matches": []}

# File Related Functions

def download_from_google_drive(file_name, local_path):
    try:
        file_list = drive.ListFile({'q': f"title='{file_name}'"}).GetList()
        print(f"File list: {file_list}")
        if file_list:
            file_drive = file_list[0]
            file_drive.GetContentFile(local_path)
            return True
        else:
            print(f"File {file_name} not found on Google Drive.")
            return False
    except Exception as e:
        print(f"Failed to download file from Google Drive: {e}")
        return False

def upload_to_google_drive(file_path):
    try:
        file = drive.CreateFile({'title': os.path.basename(file_path)})
        file.SetContentFile(file_path)
        file.Upload()
        return True
    except Exception as e:
        print(f"Failed to upload file to Google Drive: {e}")
        return False
    
def init_data_file():
    if not os.path.exists(json_file_path):
        try:
            with open(json_file_path, "w") as file:
                json.dump([], file)
        except Exception as e:
            print(f"Failed to initialize data file: {e}")

def load_init_data():
    global match_data, current_series
    if not os.path.exists(json_file_path):
        download_from_google_drive("cod_ireland_stats.json", json_file_path)
    if os.path.exists(json_file_path):
        try:
            with open(json_file_path, "r") as file:
                match_data = json.load(file)
                if match_data:
                    current_series = match_data[-1].copy()
                else:
                    current_series = {"Series Number": 1, "Matches": []}
        except json.JSONDecodeError:
            messagebox.showerror("Error", "Failed to load initial data.")
            match_data = []
            current_series = {"Series Number": 1, "Matches": []}
        except Exception as e:
            messagebox.showerror("Error", f"An unexpected error occurred: {e}")
            match_data = []
            current_series = {"Series Number": 1, "Matches": []}
    else:
        match_data = []
        current_series = {"Series Number": 1, "Matches": []}

def import_data():
    global match_data, current_series

    file_path = json_file_path

    if not file_path:
        messagebox.showinfo("Info", "No file selected.")
        return

    try:
        with open(file_path, "r") as file:
            imported_data = json.load(file)

        if not isinstance(imported_data, list):
            raise ValueError("Invalid data format: Expected a list of series data.")

        for series in imported_data:
            if not isinstance(series, dict):
                raise ValueError(f"Invalid series structure in JSON data: {series}")
            if "Series Number" not in series or "Matches" not in series:
                raise ValueError(f"Missing keys in series: {series}")

            for match in series["Matches"]:
                if not isinstance(match, dict):
                    raise ValueError(f"Invalid match structure in JSON data: {match}")
                if "Game Mode" not in match or "Map" not in match or "Player Stats" not in match:
                    raise ValueError(f"Missing keys in match: {match}")

                for player_stats in match["Player Stats"]:
                    if not isinstance(player_stats, dict):
                        raise ValueError(f"Invalid player stats structure in JSON data: {player_stats}")
                    if "Player" not in player_stats or "Kills" not in player_stats or "Deaths" not in player_stats or "OBJ" not in player_stats:
                        raise ValueError(f"Missing keys in player stats: {player_stats}")
                    
                    if match["Game Mode"] == "Hardpoint":
                        if isinstance(player_stats["OBJ"], str):
                            player_stats["OBJ"] = mmss_to_seconds(player_stats["OBJ"])
                        else:
                            raise ValueError(f"Invalid OBJ format for Hardpoint: {player_stats['OBJ']}")

        match_data = imported_data
        if match_data:
            current_series = match_data[-1].copy()
        else:
            current_series = {"Series Number": 1, "Matches": []}
        messagebox.showinfo("Success", f"Data imported successfully from {file_path}.")

    except json.JSONDecodeError:
        messagebox.showerror("Error", "The selected file is not a valid JSON file.")
    except ValueError as ve:
        messagebox.showerror("Error", f"Data validation failed: {ve}")
    except Exception as e:
        messagebox.showerror("Error", f"An unexpected error occurred: {e}")

def save_round():
    player_stats = []
    
    for _, player_var, kills_entry, deaths_entry, obj_entry in player_widgets:
        selected_player = player_var.get()
        kills = kills_entry.get()
        deaths = deaths_entry.get()
        objectives = obj_entry.get()

        if selected_player:
            if not (kills.isdigit() and deaths.isdigit() and objectives.replace(':', '').isdigit()):
                messagebox.showerror("Error", f"Please enter valid stats for {selected_player}.")
                return

            obj_value = objectives
            if mode_var.get() == "Hardpoint":
                obj_value = seconds_to_mmss(mmss_to_seconds(objectives))

            player_stats.append({
                "Player": selected_player,
                "Kills": int(kills),
                "Deaths": int(deaths),
                "OBJ": obj_value
            })
    
    if not player_stats:
        messagebox.showerror("Error", "Please select at least one player and enter their stats.")
        return
    
    game_mode = mode_var.get()
    map_name = map_var.get()
    objective_type = objective_label.cget("text")   

    if not game_mode or not map_name:
        messagebox.showerror("Error", "Please select a game mode and map.")
        return
    
    if not win_var.get() and not lose_var.get():
        messagebox.showerror("Error", "Please select either Win or Lose.")
        return

    current_match_data = {
        "Game Mode": game_mode,
        "Map": map_name,
        "Player Stats": player_stats,
        "Match Number": len(current_series["Matches"]) + 1,
        "Result": "Win" if win_var.get() else "Loss"
        }
    current_series["Matches"].append(current_match_data)

    messagebox.showinfo("Success", f"Match {current_match_data['Match Number']} for Series {current_series['Series Number']} has been saved.")
    clear_all_inputs()
    match_data.append(current_series.copy())
    clear_all_series_data()

def export_data():
    if not match_data:
        messagebox.showerror("Error", "No match details to export.")
        return

    file_path = json_file_path

    if not file_path:
        return

    try:
        with open(file_path, "w") as file:
            json.dump(match_data, file, indent=4)
        if not upload_to_google_drive(file_path):
            with open("backup_cod_ireland_stats.json", "w") as backup_file:
                json.dump(match_data, backup_file, indent=4)
            messagebox.showinfo("Success", f"Exported successfully to backup_cod_ireland_stats.json as a backup.")
        else:
            messagebox.showinfo("Success", f"Exported successfully to Google Drive.")
    except Exception as e:
        print(f"Error in export_data: {e}")
        messagebox.showerror("Error", f"Failed to save file: {e}")

init_data_file()
load_init_data()

# Utility Functions

def update_checkbox_color():
    win_checkbox.config(background="green" if win_var.get() else "SystemButtonFace")
    lose_checkbox.config(background="red" if lose_var.get() else "SystemButtonFace")

def update_objective_options(event):
    game_mode = mode_var.get()
    objective = {
        "Hardpoint": "Time on Hill",
        "Control": "Captures",
        "Search and Destroy": "Plants"
    }.get(game_mode, "N/A")
    objective_label.config(text=objective)

def seconds_to_mmss(seconds):
    minutes, seconds = divmod(int(seconds), 60)
    return f"{minutes:02d}:{seconds:02d}"

def mmss_to_seconds(mmss):
    if ':' in mmss:
        minutes, seconds = map(int, mmss.split(':'))
        return minutes * 60 + seconds
    else:
        return int(mmss)

def clear_player_inputs():
    for _, player_var, kills_entry, deaths_entry, obj_entry in player_widgets:
        player_var.set("")
        kills_entry.delete(0, tk.END)
        deaths_entry.delete(0, tk.END)
        obj_entry.delete(0, tk.END)

def clear_all_inputs():
    clear_player_inputs()
    mode_var.set("")
    map_var.set("")

def clear_all_series_data():
    global current_series
    current_series = {"Series Number": current_series["Series Number"] + 1, "Matches": []}

# GUI Functions

def create_search_tab(notebook):
    search_tab = ttk.Frame(notebook)
    notebook.add(search_tab, text="Search Stats")

    search_frame = ttk.LabelFrame(search_tab, text="Search Filters", padding=10)
    search_frame.pack(fill="x", padx=10, pady=5)

    ttk.Label(search_frame, text="Player:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
    player_var = ttk.Combobox(search_frame, values=players, state="readonly")
    player_var.grid(row=0, column=1, padx=5, pady=5)

    ttk.Label(search_frame, text="Map:").grid(row=0, column=2, padx=5, pady=5, sticky="w")
    map_var = ttk.Combobox(search_frame, values=maps, state="readonly")
    map_var.grid(row=0, column=3, padx=5, pady=5)

    ttk.Label(search_frame, text="Game Mode:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
    search_mode_var = tk.StringVar()
    search_mode_menu = ttk.Combobox(search_frame, textvariable=search_mode_var, values=game_modes, state="readonly")
    search_mode_menu.grid(row=1, column=1, padx=5, pady=5)

    ttk.Label(search_frame, text="Objective:").grid(row=1, column=2, padx=5, pady=5, sticky="w")
    search_objective_var = tk.StringVar()
    search_objective_menu = ttk.Combobox(search_frame, textvariable=search_objective_var, state="readonly")
    search_objective_menu.grid(row=1, column=3, padx=5, pady=5)

    ttk.Label(search_frame, text="Result:").grid(row=2, column=0, padx=5, pady=5, sticky="w")
    result_var = ttk.Combobox(search_frame, values=["", "Win", "Loss"], state="readonly")
    result_var.grid(row=2, column=1, padx=5, pady=5)

    def update_search_objective_options(event):
        game_mode = search_mode_var.get()
        search_objective_var.set("")

        search_objective_menu["values"] = {
            "Hardpoint": ["Time on Hill"],
            "Control": ["Captures"],
            "Search and Destroy": ["Plants"]
        }.get(game_mode, [])

    search_mode_menu.bind("<<ComboboxSelected>>", update_search_objective_options)

    tree_frame = ttk.Frame(search_tab)
    tree_frame.pack(fill="both", expand=True, padx=10, pady=5)

    tree = ttk.Treeview(tree_frame, columns=("K/D", "Match", "Player", "Kills", "Deaths", "OBJ", "Map", "Mode", "Result"), show="headings")

    for col in ("K/D", "Match", "Player", "Kills", "Deaths", "OBJ", "Map", "Mode", "Result"):
        tree.heading(col, text=col, command=lambda _col=col: treeview_sort_column(tree, _col, False))

    for col in tree["columns"]:
        tree.column(col, width=70)

    tree.column("K/D", width=30, stretch=tk.NO)

    tree.pack(fill="both", expand=True)

    scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
    scrollbar.pack(side="right", fill="y")
    tree.configure(yscrollcommand=scrollbar.set)

    def search_stats():
        player_filter = player_var.get()
        map_filter = map_var.get()
        mode_filter = search_mode_var.get()
        objective_filter = search_objective_var.get()
        result_filter = result_var.get()

        for item in tree.get_children():
            tree.delete(item)

        for series in match_data:
            for match in series["Matches"]:
                if (player_filter and player_filter not in [stat["Player"] for stat in match["Player Stats"]]) or \
                (map_filter and match["Map"] != map_filter) or \
                (mode_filter and match["Game Mode"] != mode_filter) or \
                (result_filter and match["Result"] != result_filter) or \
                (objective_filter and "OBJ" in match and not any(stat["OBJ"] == objective_filter or (match["Game Mode"] == "Hardpoint" and str(mmss_to_seconds(stat["OBJ"])) == objective_filter) for stat in match["Player Stats"])): 
                    continue

                for stat in match["Player Stats"]:
                    if (not player_filter or stat["Player"] == player_filter) and \
                    (not objective_filter or "OBJ" in match and (stat["OBJ"] == objective_filter or (match["Game Mode"] == "Hardpoint" and str(mmss_to_seconds(stat["OBJ"])) == objective_filter))):
                        kd_indicator = '+' if stat["Kills"] > stat["Deaths"] else '-' if stat["Kills"] < stat["Deaths"] else '='
                        tree.insert("", "end", values=(
                            kd_indicator,
                            match["Match Number"],
                            stat["Player"],
                            stat["Kills"],
                            stat["Deaths"],
                            stat["OBJ"] if match["Game Mode"] != "Hardpoint" else seconds_to_mmss(stat["OBJ"]), 
                            match["Map"],
                            match["Game Mode"],
                            match["Result"]
                        ))
                for item in tree.get_children():
                    result_value = tree.item(item)['values'][-1]
                if result_value == 'Win':
                    tree.item(item, tags=('win',))
                elif result_value == 'Loss':
                    tree.item(item, tags=('loss',))

                tree.tag_configure("win", background="#00FF00")
                tree.tag_configure("loss", background="#FF0000")

    ttk.Button(search_frame, text="Search", command=search_stats).grid(row=3, column=3, columnspan=2, pady=5)

    def clear_filters():
        player_var.set("")
        map_var.set("")
        search_mode_var.set("")
        search_objective_var.set("")
        result_var.set("")
        
        for item in tree.get_children():
            tree.delete(item)

    ttk.Button(search_frame, text="Clear Filters", command=clear_filters).grid(row=3, column=0, columnspan=4, pady=5)

    def treeview_sort_column(tv, col, reverse):
        l = [(tv.set(k, col), k) for k in tv.get_children('')]
        try:
            l.sort(key=lambda t: int(t[0]), reverse=reverse)
        except ValueError:
            l.sort(reverse=reverse)

        for index, (val, k) in enumerate(l):
            tv.move(k, '', index)

        tv.heading(col, command=lambda: treeview_sort_column(tv, col, not reverse))

        for header in tv["columns"]:
            if header == col:
                tv.heading(header, text=f"{header} {'▼' if reverse else '▲'}")
            else:
                tv.heading(header, text=header)

def create_totals_tab(notebook):
    totals_tab = ttk.Frame(notebook)
    notebook.add(totals_tab, text="Totals")
    
    tree_frame = ttk.Frame(totals_tab)
    tree_frame.pack(fill="both", expand=True, padx=10, pady=10)

    tree = ttk.Treeview(tree_frame, columns=("Player", "Total Kills", "Total Deaths", "Time on Hill", "Captures", "Plants", "K/D Ratio"), show="headings")
    
    for col in ("Player", "Total Kills", "Total Deaths", "Time on Hill", "Captures", "Plants", "K/D Ratio"):
        tree.heading(col, text=col, command=lambda _col=col: treeview_sort_column(tree, _col, False))
        tree.column(col, width=100, anchor="center")

    tree.pack(fill="both", expand=True)

    scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
    scrollbar.pack(side="right", fill="y")
    tree.configure(yscrollcommand=scrollbar.set)

    def update_totals():
        for item in tree.get_children():
            tree.delete(item)

        player_totals = {}
        for series in match_data:
            for match in series["Matches"]:
                for stat in match["Player Stats"]:
                    player = stat["Player"]
                    if player not in player_totals:
                        player_totals[player] = {
                            "kills": 0, 
                            "deaths": 0, 
                            "time_on_hill": 0, 
                            "captures": 0, 
                            "plants": 0
                        }
                    
                    player_totals[player]["kills"] += stat["Kills"]
                    player_totals[player]["deaths"] += stat["Deaths"]
                    
                    if match["Game Mode"] == "Hardpoint":
                        if isinstance(stat["OBJ"], str):
                            player_totals[player]["time_on_hill"] += mmss_to_seconds(stat["OBJ"])
                        else:
                            player_totals[player]["time_on_hill"] += stat["OBJ"]
                    elif match["Game Mode"] == "Control":
                        player_totals[player]["captures"] += int(stat["OBJ"])
                    elif match["Game Mode"] == "Search and Destroy":
                        player_totals[player]["plants"] += int(stat["OBJ"])

        for player, totals in player_totals.items():
            kd_ratio = totals["kills"] / totals["deaths"] if totals["deaths"] != 0 else totals["kills"]
            time_on_hill = seconds_to_mmss(totals["time_on_hill"])
            
            tree.insert("", "end", values=(
                player,
                totals["kills"],
                totals["deaths"],
                time_on_hill,
                totals["captures"],
                totals["plants"],
                f"{kd_ratio:.2f}"
            ))

    update_button = ttk.Button(totals_tab, text="Update Totals", command=update_totals)
    update_button.pack(pady=10)

    def treeview_sort_column(tv, col, reverse):
        l = [(tv.set(k, col), k) for k in tv.get_children('')]
        try:
            if col == "K/D Ratio":
                l.sort(key=lambda t: float(t[0]), reverse=reverse)
            elif col == "Time on Hill":
                l.sort(key=lambda t: mmss_to_seconds(t[0]), reverse=reverse)
            else:
                l.sort(key=lambda t: int(t[0]), reverse=reverse)
        except ValueError:
            l.sort(reverse=reverse)

        for index, (val, k) in enumerate(l):
            tv.move(k, '', index)

        tv.heading(col, command=lambda: treeview_sort_column(tv, col, not reverse))

        for header in tv["columns"]:
            if header == col:
                tv.heading(header, text=f"{header} {'▼' if reverse else '▲'}")
            else:
                tv.heading(header, text=header)

def create_charts_tab(notebook):
    charts_tab = ttk.Frame(notebook)
    notebook.add(charts_tab, text="Charts")

    ttk.Label(charts_tab, text="Select Chart Type:").pack(pady=10)
    
    chart_type_var = tk.StringVar()
    chart_type_menu = ttk.Combobox(charts_tab, textvariable=chart_type_var, values=["Kills vs Deaths", "Objectives"], state="readonly")
    chart_type_menu.pack(pady=10)
    
    chart_frame = ttk.Frame(charts_tab)
    chart_frame.pack(fill="both", expand=True, padx=10, pady=10)

    def plot_chart():
        for widget in chart_frame.winfo_children():
            widget.destroy()

        chart_type = chart_type_var.get()
        if chart_type == "Kills vs Deaths":
            plot_kills_vs_deaths(chart_frame)
        elif chart_type == "Objectives":
            plot_objectives(chart_frame)

    ttk.Button(charts_tab, text="Plot Chart", command=plot_chart).pack(pady=10)

def plot_kills_vs_deaths(frame):
    players = []
    kills = []
    deaths = []

    for series in match_data:
        for match in series["Matches"]:
            for stat in match["Player Stats"]:
                players.append(stat["Player"])
                kills.append(stat["Kills"])
                deaths.append(stat["Deaths"])

    fig, ax = plt.subplots()
    ax.bar(players, kills, label='Kills')
    ax.bar(players, deaths, label='Deaths', bottom=kills)
    ax.set_xlabel('Players')
    ax.set_ylabel('Count')
    ax.set_title('Kills vs Deaths')
    ax.legend()
    canvas = FigureCanvasTkAgg(fig, master=frame)
    canvas.draw()
    canvas.get_tk_widget().pack(fill="both", expand=True)

def plot_objectives(frame):
    players = []
    objectives = []

    for series in match_data:
        for match in series["Matches"]:
            for stat in match["Player Stats"]:
                players.append(stat["Player"])
                objectives.append(stat["OBJ"])

    fig, ax = plt.subplots()
    ax.bar(players, objectives)
    ax.set_xlabel('Players')
    ax.set_ylabel('Objectives')
    ax.set_title('Objectives by Player')

    canvas = FigureCanvasTkAgg(fig, master=frame)
    canvas.draw()
    canvas.get_tk_widget().pack(fill="both", expand=True)

def create_splash_background(root):
    image_path = "Resources/stormlogo.png"
    try:
        image = Image.open(image_path)
        photo = ImageTk.PhotoImage(image)
        canvas = tk.Canvas(root, width=image.width, height=image.height, bg="black")
        canvas.pack(fill="both", expand=True)
        canvas.create_image(0, 0, image=photo, anchor="nw")
        canvas.image = photo
    except Exception as e:
        print(f"Error loading image: {e}")

root = tk.Tk()
root.title("Call of Duty Data Tracker")
root.geometry("800x700")
window_width = 800
window_height = 700
screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()
position_top = int(screen_height / 2 - window_height / 2)
position_right = int(screen_width / 2 - window_width / 2)
root.geometry(f'{window_width}x{window_height}+{position_right}+{position_top}')
root.resizable(True, True)
win_var = tk.BooleanVar()
lose_var = tk.BooleanVar()

create_splash_background(root)

root.grid_rowconfigure(0, weight=1)
root.grid_columnconfigure(0, weight=1)

notebook = ttk.Notebook(root)
notebook.pack(expand=True, fill="both", padx=5, pady=5)

main_tab = ttk.Frame(notebook)
notebook.add(main_tab, text="Data Entry")
main_tab.grid_rowconfigure(0,weight=1)
main_tab.grid_columnconfigure(0,weight=1)

frame = ttk.Frame(main_tab)
frame.pack(expand=True, fill="both", padx=20, pady=20)

for i in range(16):
    frame.grid_rowconfigure(i, weight=1)
for i in range(16):
    frame.grid_columnconfigure(i, weight=1)

create_search_tab(notebook)
create_totals_tab(notebook)
create_charts_tab(notebook)


mode_var = tk.StringVar()
ttk.Label(frame, text="Game Mode:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
mode_menu = ttk.Combobox(frame, textvariable=mode_var, values=game_modes, state="readonly")
mode_menu.grid(row=0, column=1, padx=5, pady=5, sticky=tk.EW)
mode_menu.bind("<<ComboboxSelected>>", update_objective_options)
mode_menu.config(cursor="hand2")

map_var = tk.StringVar()
ttk.Label(frame, text="Map:").grid(row=0, column=2, padx=5, pady=5, sticky=tk.W)
map_menu = ttk.Combobox(frame, textvariable=map_var, values=maps, state="readonly")
map_menu.grid(row=0, column=3, padx=5, pady=5, sticky=tk.EW)
map_menu.config(cursor="hand2")

win_checkbox = tk.Checkbutton(frame, text="Win", variable=win_var, command=update_checkbox_color)
win_checkbox.grid(row=1, column=2, padx=5, pady=5, sticky=tk.W)

lose_checkbox = tk.Checkbutton(frame, text="Lose", variable=lose_var, command=update_checkbox_color)
lose_checkbox.grid(row=1, column=3, padx=5, pady=5, sticky=tk.W)

objective_var = tk.StringVar()
ttk.Label(frame, text="Objective Type:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
objective_label = ttk.Label(frame, text="")
objective_label.grid(row=1, column=1, columnspan=1, padx=5, pady=5, sticky=tk.W)

ttk.Separator(frame, orient='horizontal').grid(row=2, column=0, columnspan=4, sticky='ew', pady=10)

player_widgets = []

for i in range(2):
    player_var = tk.StringVar()
    ttk.Label(frame, text=f"Player {i+1}:").grid(row=4 + i*4, column=0, padx=5, pady=5, sticky=tk.W)
    player_menu = ttk.Combobox(frame, textvariable=player_var, values=players, state="readonly")
    player_menu.grid(row=4 + i*4, column=1, padx=5, pady=5)
    player_menu.config(cursor="hand2")
    
    ttk.Label(frame, text="Kills:").grid(row=5 + i*4, column=0, padx=5, pady=5, sticky=tk.W)
    kills_entry = ttk.Entry(frame)
    kills_entry.grid(row=5 + i*4, column=1, padx=5, pady=5)

    ttk.Label(frame, text="Deaths:").grid(row=6 + i*4, column=0, padx=5, pady=5, sticky=tk.W)
    deaths_entry = ttk.Entry(frame)
    deaths_entry.grid(row=6 + i*4, column=1, padx=5, pady=5)

    ttk.Label(frame, text="Objective:").grid(row=7 + i*4, column=0, padx=5, pady=5, sticky=tk.W)
    obj_entry = ttk.Entry(frame)
    obj_entry.grid(row=7 + i*4, column=1, padx=5, pady=5)

    player_widgets.append((f"Player {i+1}", player_var, kills_entry, deaths_entry, obj_entry))

for i in range(2, 4):
    player_var = tk.StringVar()
    ttk.Label(frame, text=f"Player {i+1}:").grid(row=4 + (i-2)*4, column=2, padx=5, pady=5, sticky=tk.W)
    player_menu = ttk.Combobox(frame, textvariable=player_var, values=players, state="readonly")
    player_menu.grid(row=4 + (i-2)*4, column=3, padx=5, pady=5)
    player_menu.config(cursor="hand2")
    
    ttk.Label(frame, text="Kills:").grid(row=5 + (i-2)*4, column=2, padx=5, pady=5, sticky=tk.W)
    kills_entry = ttk.Entry(frame)
    kills_entry.grid(row=5 + (i-2)*4, column=3, padx=5, pady=5)

    ttk.Label(frame, text="Deaths:").grid(row=6 + (i-2)*4, column=2, padx=5, pady=5, sticky=tk.W)
    deaths_entry = ttk.Entry(frame)
    deaths_entry.grid(row=6 + (i-2)*4, column=3, padx=5, pady=5)
    
    ttk.Label(frame, text="Objective:").grid(row=7 + (i -2)*4, column=2, padx=5, pady=5, sticky=tk.W)
    obj_entry = ttk.Entry(frame)
    obj_entry.grid(row=7 + (i-2)*4, column=3, padx=5, pady=5)

    player_widgets.append((f"Player {i+1}", player_var, kills_entry, deaths_entry, obj_entry))

ttk.Separator(frame, orient='horizontal').grid(row=12, column=0, columnspan=4, sticky='ew', pady=10)

save_round_hint = ttk.Label(frame, text="Save the round stats to the file.")
save_round_hint.grid(row=13, column=0, columnspan=2, padx=5, pady=5, sticky=tk.E)

save_round_button = ttk.Button(frame, text="Save Stats", command=save_round)
save_round_button.grid(row=13, column=2, columnspan=2, padx=5, pady=5)
save_round_button.config(cursor="hand2")

export_hint = ttk.Label(frame, text="Export the series data to add to the file.")
export_hint.grid(row=14, column=0, columnspan=2, padx=5, pady=5, sticky=tk.E)

export_button = ttk.Button(frame, text="Export Data", command=export_data)
export_button.grid(row=14, column=2, columnspan=2, padx=5, pady=5)
export_button.config(cursor="hand2")

# Main Function

def main():
    root.title("CoD Stats Tracker")
    
    create_splash_background(root)
    import_data()

    root.mainloop()

if __name__ == "__main__":
    main()