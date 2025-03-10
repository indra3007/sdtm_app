from manim import *

class AdverseEventVisualization(Scene):
    def construct(self):
        # Title
        title = Text("Adverse Event Data Summary").scale(0.8).to_edge(UP)
        self.play(Write(title))
        self.wait(1)

        # Sample data
        events = ["Headache", "Nausea", "Abdominal Pain", "Chest Pain", "Leg Cramps"]
        occurrences = [15, 10, 12, 8, 5]

        # Axes for the bar chart
        axes = Axes(
            x_range=[0, len(events), 1],
            y_range=[0, max(occurrences) + 5, 5],
            x_length=8,
            y_length=5,
            axis_config={"include_numbers": True},
            tips=False,
        ).to_edge(DOWN)
        self.play(Create(axes))
        self.wait(1)

        # Labels for the x-axis
        x_labels = VGroup()
        for i, event in enumerate(events):
            label = Text(event, font_size=24).next_to(axes.c2p(i, 0), DOWN)
            x_labels.add(label)
        self.play(Write(x_labels))
        self.wait(1)

        # Create the bars
        bars = VGroup()
        for i, count in enumerate(occurrences):
            bar = Rectangle(
                width=0.5, height=count / max(occurrences) * 4, color=BLUE, fill_opacity=0.8
            ).move_to(axes.c2p(i, count / 2))
            bars.add(bar)

        self.play(Create(bars))
        self.wait(1)

        # Display occurrence numbers above each bar
        occurrence_labels = VGroup()
        for i, count in enumerate(occurrences):
            label = Text(str(count), font_size=24).next_to(bars[i], UP)
            occurrence_labels.add(label)
        self.play(Write(occurrence_labels))
        self.wait(1)

        # Add commentary
        commentary = Text(
            "Headache is the most common adverse event, followed by Nausea and Abdominal Pain.",
            t2c={"Headache": BLUE, "Nausea": BLUE, "Abdominal Pain": BLUE},
            font_size=24
        ).to_edge(DOWN)
        self.play(Write(commentary))
        self.wait(3)

        # Highlight the tallest bar (Headache)
        highlight = SurroundingRectangle(bars[0], color=YELLOW, buff=0.2)
        self.play(Create(highlight))
        self.wait(2)

        # Fade out
        self.play(FadeOut(VGroup(bars, x_labels, occurrence_labels, commentary, highlight, axes, title)))
