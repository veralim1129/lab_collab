"""
Simple COVID-19 rule-based Expert System with a Tkinter UI using clipspy (CLIPS wrapper).

How it works
- Two CLIPS rules (knowledge base):
  1) If fever, cough, and loss_of_taste => Likely COVID-19
  2) If fever and difficulty_breathing => Possible severe COVID-19 (seek help)
- User selects symptoms in the GUI and clicks "Diagnose".
- The program asserts symptom facts into the CLIPS environment, runs the rules, and shows diagnosis facts.

Dependencies
- Python 3.x
- clipspy: `pip install clipspy`
- tkinter: usually included with Python. On some Linux distributions you may need: `sudo apt-get install python3-tk`

Save this file and run: `python covid_expert_system.py`
"""

import sys
import tkinter as tk
from tkinter import messagebox, scrolledtext

try:
    from clipspy import Environment
except Exception as e:
    message = (
        "The 'clipspy' library is required but not installed or failed to import.\n"
        "Install it with: pip install clipspy\n\n"
        f"Import error: {e}"
    )
    print(message)
    # If running from GUI, pop up a message and exit.
    try:
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("Missing dependency", message)
        root.destroy()
    except Exception:
        pass
    sys.exit(1)


class CovidExpertSystemApp:
    def __init__(self, master):
        self.master = master
        master.title("COVID-19 Simple Expert System")
        master.geometry("520x420")

        # CLIPS environment
        self.env = Environment()
        self._build_rules()

        # UI elements
        frame = tk.Frame(master)
        frame.pack(padx=12, pady=12, fill=tk.BOTH, expand=True)

        lbl = tk.Label(frame, text="Select symptoms:")
        lbl.pack(anchor=tk.W)

        self.symptom_vars = {
            'fever': tk.IntVar(),
            'cough': tk.IntVar(),
            'loss_of_taste': tk.IntVar(),
            'difficulty_breathing': tk.IntVar(),
        }

        # Checkbuttons
        for key, var in self.symptom_vars.items():
            pretty = key.replace('_', ' ').capitalize()
            cb = tk.Checkbutton(frame, text=pretty, variable=var)
            cb.pack(anchor=tk.W)

        btn_frame = tk.Frame(frame)
        btn_frame.pack(fill=tk.X, pady=(8, 8))

        diag_btn = tk.Button(btn_frame, text="Diagnose", command=self.diagnose)
        diag_btn.pack(side=tk.LEFT)

        clear_btn = tk.Button(btn_frame, text="Clear", command=self.clear)
        clear_btn.pack(side=tk.LEFT, padx=(6, 0))

        help_btn = tk.Button(btn_frame, text="Help", command=self.show_help)
        help_btn.pack(side=tk.RIGHT)

        # Results box
        res_label = tk.Label(frame, text="Result:")
        res_label.pack(anchor=tk.W)

        self.result_text = scrolledtext.ScrolledText(frame, height=8, wrap=tk.WORD)
        self.result_text.pack(fill=tk.BOTH, expand=True)
        self.result_text.configure(state=tk.DISABLED)

        # Fired rules box (for transparency)
        fired_label = tk.Label(frame, text="Fired rules (CLIPS agenda):")
        fired_label.pack(anchor=tk.W, pady=(8, 0))

        self.fired_text = tk.Text(frame, height=4)
        self.fired_text.pack(fill=tk.BOTH, expand=False)
        self.fired_text.configure(state=tk.DISABLED)

    def _build_rules(self):
        """Build CLIPS rules and templates."""
        # Clear any previous content
        try:
            # Recreate environment to ensure fresh start
            self.env.clear()
        except Exception:
            pass

        # A template to store diagnosis results
        self.env.build('''
            (deftemplate diagnosis
                (slot result))
        ''')

        # Rule 1: fever + cough + loss_of_taste => Likely COVID-19
        self.env.build('''
            (defrule covid-likely
                (fever yes)
                (cough yes)
                (loss_of_taste yes)
            =>
                (assert (diagnosis (result "Likely COVID-19")))
            )
        ''')

        # Rule 2: fever + difficulty_breathing => Possible severe COVID-19
        self.env.build('''
            (defrule covid-severe
                (fever yes)
                (difficulty_breathing yes)
            =>
                (assert (diagnosis (result "Possible severe COVID-19 - seek medical attention")))
            )
        ''')

        # Optional: a rule that asserts nothing else but we won't add more rules to keep it simple.

    def diagnose(self):
        # reset environment and assert current symptoms
        self.env.reset()

        # Assert symptom facts using simple facts like (fever yes)
        for symptom, var in self.symptom_vars.items():
            if var.get():
                fact_str = f'({symptom} yes)'
                self.env.assert_string(fact_str)

        # Run the engine
        fired_before = len(list(self.env.agenda())) if hasattr(self.env, 'agenda') else None
        try:
            self.env.run()
        except Exception as e:
            messagebox.showerror("CLIPS Error", f"An error occurred while running CLIPS: {e}")
            return

        # Collect diagnosis facts
        diagnoses = []
        for fact in self.env.facts():
            # fact.template.name available on clipspy Fact objects
            try:
                if fact.template.name == 'diagnosis':
                    diagnoses.append(fact['result'])
            except Exception:
                # ignore other facts
                continue

        # Show fired rules (very simple: list agenda or mention none)
        fired_rules = []
        try:
            # clipspy's Environment has method agenda() that can be iterated
            for act in self.env.agenda():
                fired_rules.append(str(act))
        except Exception:
            # If agenda isn't available or empty, leave empty
            fired_rules = []

        # Display results
        self.result_text.configure(state=tk.NORMAL)
        self.result_text.delete('1.0', tk.END)
        if diagnoses:
            for d in diagnoses:
                self.result_text.insert(tk.END, f"{d}\n")
        else:
            self.result_text.insert(tk.END, "No COVID-19-specific rule was triggered.\nIf symptoms persist, consult a healthcare professional.")
        self.result_text.configure(state=tk.DISABLED)

        self.fired_text.configure(state=tk.NORMAL)
        self.fired_text.delete('1.0', tk.END)
        if fired_rules:
            for f in fired_rules:
                self.fired_text.insert(tk.END, f + '\n')
        else:
            self.fired_text.insert(tk.END, "(No items on the CLIPS agenda or agenda not available)\n")
        self.fired_text.configure(state=tk.DISABLED)

    def clear(self):
        for var in self.symptom_vars.values():
            var.set(0)
        self.result_text.configure(state=tk.NORMAL)
        self.result_text.delete('1.0', tk.END)
        self.result_text.configure(state=tk.DISABLED)
        self.fired_text.configure(state=tk.NORMAL)
        self.fired_text.delete('1.0', tk.END)
        self.fired_text.configure(state=tk.DISABLED)
        self.env.clear()
        self._build_rules()

    def show_help(self):
        messagebox.showinfo(
            "Help",
            "This is a tiny educational expert system with only two simple rules:\n\n"
            "1) Fever + Cough + Loss of taste => Likely COVID-19\n"
            "2) Fever + Difficulty breathing => Possible severe COVID-19 (seek help)\n\n"
            "These are *example* rules only and NOT a medical diagnosis tool.\n"
            "If you or someone is unwell, consult a qualified healthcare professional.")


if __name__ == '__main__':
    root = tk.Tk()
    app = CovidExpertSystemApp(root)
    root.mainloop()
