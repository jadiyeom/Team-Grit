from manim import *

class BubbleSortAnimation(Scene):
    def construct(self):
        print("Enter the number of terms")
        nums = int(input("Number of terms: "))
        print("Enter the numbers separated by space")
        nums_list = list(map(int, input().split()))
        square_text_pairs = [
            (Square(fill_color=BLUE, fill_opacity=0.5, side_length=1, color=BLUE), Text(str(num), color=WHITE, font_size=18))
            for num in nums_list
        ]

        square_text_groups = [VGroup(square, text) for square, text in square_text_pairs]

        for i, (square, text) in enumerate(square_text_pairs):
            square.move_to([2 * i - 4, 0, 0])
            text.move_to(square)

        title = Text("Bubble Sort", color=WHITE, font_size=30)
        title.move_to([0, 2, 0])

        self.play(Write(title))
        self.play(*[Create(group) for group in square_text_groups])

        for i, (square, text) in enumerate(square_text_pairs):
            new_position = [2 * i - 4, 0, 0]
            square_text_groups[i].move_to(new_position)

        self.bubble_sort(nums_list, square_text_groups)

        self.play(FadeOut(title), *[FadeOut(group) for group in square_text_groups])

    def bubble_sort(self, nums_list, square_text_groups):
        n = len(nums_list)
        for i in range(n):
            for j in range(0, n-i-1):
                self.play(square_text_groups[j][0].animate.set_color(RED),
                          square_text_groups[j+1][0].animate.set_color(RED),
                          run_time=0.5)
                self.wait(0.5)

                if nums_list[j] > nums_list[j+1]:
                    nums_list[j], nums_list[j+1] = nums_list[j+1], nums_list[j]  
                    square_text_groups[j], square_text_groups[j+1] = square_text_groups[j+1], square_text_groups[j]
                    self.play(
                        square_text_groups[j][0].animate.move_to(square_text_groups[j+1][0].get_center()),
                        square_text_groups[j+1][0].animate.move_to(square_text_groups[j][0].get_center()),
                        square_text_groups[j][1].animate.move_to(square_text_groups[j+1][1].get_center()),
                        square_text_groups[j+1][1].animate.move_to(square_text_groups[j][1].get_center()),
                        run_time=0.5
                    )

                self.play(square_text_groups[j][0].animate.set_color(BLUE),
                          square_text_groups[j+1][0].animate.set_color(BLUE),
                          run_time=0.5)

                for k, (square, text) in enumerate(square_text_groups):
                    new_position = [2 * k - 4, 0, 0]
                    square_text_groups[k].move_to(new_position)

        for square, text in square_text_groups:
            self.play(square.animate.set_color(GREEN), run_time=0.2)
            self.wait(0.2)
