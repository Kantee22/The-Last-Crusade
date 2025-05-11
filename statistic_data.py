import tkinter as tk
from tkinter import ttk
import pandas as pd
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt

# Load dataset
df = pd.read_csv('runs.csv')

# Plot functions
def plot_histogram():
    fig, ax = plt.subplots()
    ax.hist(df['Play_Time_Sec'], bins=10)
    ax.set_title('Distribution of Play Time (sec)')
    ax.set_xlabel('Play_Time_Sec')
    return fig

def plot_boxplot_play_time():
    fig, ax = plt.subplots()
    ax.boxplot(df['Play_Time_Sec'], vert=False)
    ax.set_title('Boxplot of Play Time (sec)')
    ax.set_xlabel('Play_Time_Sec')
    return fig

def plot_bar_class():
    fig, ax = plt.subplots()
    counts = df['Class'].value_counts()
    counts.plot.bar(ax=ax)
    ax.set_title('Count by Class')
    ax.set_ylabel('Number of Players')
    return fig

def plot_bar_miniboss():
    fig, ax = plt.subplots()
    counts = df['Miniboss_Killed'].value_counts()
    counts.plot.bar(ax=ax)
    ax.set_title('Count by Miniboss Killed')
    ax.set_ylabel('Number of Players')
    return fig

def plot_bar_beat_boss():
    fig, ax = plt.subplots()
    counts = df['Beat_Final_Boss'].map({0: 'Lose', 1: 'Win'}).value_counts()
    counts.plot.bar(ax=ax)
    ax.set_title('Beat Final Boss (Win vs Lose)')
    ax.set_ylabel('Number of Players')
    return fig

def plot_scatter_level_time():
    fig, ax = plt.subplots()
    ax.scatter(df['Level'], df['Play_Time_Sec'])
    ax.set_title('Level vs Play Time (sec)')
    ax.set_xlabel('Level')
    ax.set_ylabel('Play_Time_Sec')
    return fig

def plot_box_time_by_class():
    fig, ax = plt.subplots()
    df.boxplot(column='Play_Time_Sec', by='Class', ax=ax)
    ax.set_title('Play Time by Class')
    ax.set_xlabel('Class')
    ax.set_ylabel('Play_Time_Sec')
    plt.suptitle('')
    return fig

# GUI setup
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Runs Data Visualizer")
        self.geometry("800x600")

        # Dropdown to select plot
        self.plot_funcs = {
            "Histogram": plot_histogram,
            "Boxplot Play Time": plot_boxplot_play_time,
            "Bar Class": plot_bar_class,
            "Bar Miniboss": plot_bar_miniboss,
            "Bar Beat Boss": plot_bar_beat_boss,
            "Scatter Level vs Time": plot_scatter_level_time,
            "Box Time by Class": plot_box_time_by_class
        }

        self.selected = tk.StringVar(value="Histogram")
        dropdown = ttk.Combobox(self, textvariable=self.selected, values=list(self.plot_funcs.keys()), state="readonly")
        dropdown.pack(pady=10)

        btn = ttk.Button(self, text="Show Plot", command=self.show_plot)
        btn.pack(pady=5)

        self.canvas_frame = ttk.Frame(self)
        self.canvas_frame.pack(fill=tk.BOTH, expand=True)

    def show_plot(self):
        for widget in self.canvas_frame.winfo_children():
            widget.destroy()

        plot_name = self.selected.get()
        fig = self.plot_funcs[plot_name]()
        canvas = FigureCanvasTkAgg(fig, master=self.canvas_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

if __name__ == "__main__":
    app = App()
    app.mainloop()
