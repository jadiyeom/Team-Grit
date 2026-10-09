from manim import *

class SmokeScene(Scene):
    def construct(self):
        title = Text("Team-Grit render check", font_size=36)
        circle = Circle(radius=1.0, color=BLUE)
        self.play(Write(title))
        self.play(title.animate.to_edge(UP))
        self.play(Create(circle))
        self.play(circle.animate.set_color(GREEN).scale(1.2))
        self.wait(0.2)
